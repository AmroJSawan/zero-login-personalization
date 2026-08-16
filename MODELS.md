# Models that consume zero-login signals

Companion to `index.html`, which shows the raw signal surface live. This document covers
what to do with it: how raw signals become features, which model consumes which feature
group, and where machine learning is the wrong answer.

Organising principle is **time horizon**, because that is what actually constrains model
choice. At t=0 you have twenty-odd scalars and no sequence. At t=10s you have a sequence
and no labels. These are different problems and they need different models.

---

## 0. The feature vector

Everything below reduces to one concatenated vector. Concrete spec:

| Block | Dims | Encoding | Source |
|---|---|---|---|
| Geo | 12 | city one-hot (top 10) + is_capital + is_outside_country | IP, server-side |
| Network class | 6 | ASN type one-hot (residential/mobile/corp/datacentre/edu/unknown) | IP → ASN |
| Connection | 5 | effectiveType one-hot(4) + saveData bool | Client Hints / NetInfo |
| Device class | 6 | log(cores), log(memory), dpr, is_touch, is_mobile, viewport bucket | UA-CH, navigator |
| Locale | 10 | lang one-hot(4) + calendar one-hot(3) + numbering one-hot(3) | Intl API |
| Temporal | 9 | hour sin/cos, dow sin/cos, is_weekend, is_business_hours, is_holiday, is_ramadan, days_to_deadline | server clock + geo join |
| Preferences | 8 | reduced-motion, contrast, color-scheme, forced-colors, reduced-data, pointer, hover, standalone | matchMedia |
| Referral | 12 | source one-hot(8) + has_utm + campaign hash bucket(3) | Referer, URL |
| Timezone consistency | 2 | tz_matches_ip, tz_offset_delta | Intl vs IP |
| **Tier-0 subtotal** | **70** | available at t=2ms, zero JavaScript | |
| Behavioural aggregate | 24 | scroll depth/velocity/reversals, dwell stats, hesitation, rage, dead clicks, copy, back-nav, query count | client sensor |
| Query semantics | 384 | embedding of concatenated search text | embedding model |
| Sequence | var | ordered event tokens | client sensor |

Two rules that matter more than the encoding choices:

**Bucket at the collector, not at the model.** `cores=8, memory=8, dpr=2, viewport=1512×982`
is four harmless numbers and roughly 9 bits of identity. Binning them (`cores≥8`, `memory≥8`,
`dpr≥2`, `viewport=desktop-large`) preserves essentially all predictive value and destroys the
identifiability. Do it in the edge worker so the unbucketed tuple never exists downstream.

**Never hash the tuple.** The moment you concatenate and hash device attributes into an ID,
you have built a fingerprint, and it is legally a tracker regardless of what you call it.

---

## 1. M0 — Rendering policy. Not a model.

**Consumes:** connection, saveData, device class, preferences, permission states.
**Produces:** prefetch policy, motion policy, image tier, JS budget.
**Implementation:** a deterministic rule table. Twenty lines.

This is in the document because it is the most common place teams reach for ML and should
not. `prefers-reduced-motion: reduce` means disable animation. There is no probability
involved, no training data required, and a model that gets it wrong 2% of the time is
strictly worse than an `if`. The live page computes this block with rules and it is correct
100% of the time by construction.

**Rule: if the mapping is a user instruction or a hard constraint, it is a rule, not a model.**

---

## 2. M1 — Cold-start prior. Logistic regression or GBDT.

**Horizon:** t = 2ms, before a byte of page is sent.
**Consumes:** the 70-dim tier-0 block.
**Produces:** prior distribution over intent classes.

**Model:** multinomial logistic regression, or a shallow gradient-boosted tree (LightGBM,
depth ≤ 4, ~100 trees). Both serialize to a few tens of KB, run in microseconds, and are
directly auditable, which matters when a public body has to explain why a citizen saw what
they saw.

**Why not something bigger:** the input is low-dimensional, mostly categorical, and the
signal is largely captured by a handful of interactions (referrer × hour, geo × language,
ASN type × device class). Tree ensembles are extremely hard to beat on exactly this shape
of data, and a neural model buys nothing while costing interpretability.

**Training:** needs only logged sessions with an outcome label. Works from ~5k sessions.
This is the model you can have running first.

**Realistic ceiling:** modest. Headers alone will not tell you what someone came to do.
Its job is to be better than uniform and to be honest about its uncertainty, not to be right.

---

## 3. M2 — Session sequence encoder.

**Horizon:** t = 1s onward, updating per event.
**Consumes:** ordered event tokens plus query embeddings.
**Produces:** a session vector used for both retrieval and intent classification.

An ordered ladder. Do not skip to the bottom.

| Model | Training data needed | Notes |
|---|---|---|
| **EWMA pooling** | none | Recency-weighted mean of event embeddings. Deterministic, explainable, ~40µs. The baseline everything must beat. |
| **Session-as-text** | none | Render the session as a sentence, embed it once with the catalog's own model. Unifies session and item space for free. Costs one embedding call (~7ms CPU). |
| **GBDT on engineered features** | ~10k sessions | Hand-built sequence features (counts, rates, first/last, time deltas). Routinely beats neural sequence models at this data scale. |
| **GRU4Rec** | ~100k sessions | The classic session-based recommender. Handles variable length natively. |
| **SASRec / BERT4Rec** | ~500k sessions | Self-attentive, the standard modern choice. Transformers4Rec is the battle-tested implementation. |
| **HSTU** | millions | Hierarchical sequential transduction; exhibits recsys scaling laws. Production-proven at very large scale. |
| **TIGER / RQ-VAE semantic IDs** | millions | Items become semantic ID sequences; recommendation becomes autoregressive generation. Reported up to 65.8% NDCG gain and 12.4% online engagement lift in production A/B. |

**The honest guidance:** a national portal catalog of ~1,200 services with short anonymous
sessions is in the top three rows of that table, not the bottom three. The bottom rows are
built for catalogs of millions of items and billions of interactions. Adopting them here
imports the cost without the regime that justifies them.

---

## 4. M3 — Interaction-state classifier.

**Horizon:** continuous, sliding 10s window.
**Consumes:** the 24-dim behavioural aggregate.
**Produces:** `{scanning, reading, searching, comparing, confused, frustrated, abandoning}`.

**Model:** small GBDT, or a 1D CNN over windowed features if you want smoothness.
**Labels:** self-supervised from proxy outcomes. Frustration is labelled by what follows
it: support contact, session abandonment, repeated failed search, rapid back-navigation.

**Why this is separate from intent:** intent says *what* to show, state says *how* and
*whether*. A confused user and a decided user wanting the same service need opposite
treatment: one needs the requirements explained, the other needs the button. Collapsing
these into one model is the single most common design error in this space.

The highest-precision inputs are cheap and under-instrumented: `copy` events (the user
found the answer and is taking it), pinch-zoom on a table (text too small, or scrutiny),
rage clicks, and query reformulation chains.

---

## 5. M4 — Calibration and abstention. The one nobody builds.

**Consumes:** raw scores from M1/M2.
**Produces:** a calibrated probability plus an explicit `abstain` decision.

This layer exists because of a measured result rather than a theoretical concern. In our
bench, a rules-based classifier was the most accurate model tested and completely unusable,
because on deliberately low-signal sessions its median confidence was **1.000**. Normalizing
a sum where only one weak rule fired produces total certainty. It became more confident as
evidence disappeared, and no threshold could fix it.

Any confidence-gated interface, meaning any interface with a "show the default when unsure"
tier, is entirely dependent on this layer.

**Options:**

- **Platt scaling / isotonic regression.** Fit a calibration map on held-out data. Cheap,
  standard, sufficient for most cases.
- **Temperature scaling.** One parameter, preserves ranking, good for neural outputs.
- **Conformal prediction.** The strongest option and the right one here. Gives a
  distribution-free, finite-sample guarantee: choose a coverage level (say 90%) and it
  returns a prediction *set* that contains the truth at least 90% of the time. When the set
  has one member, show the single card. Two or three, show the options strip. Four, show the
  default. The three UI tiers fall directly out of the set size, with a statistical guarantee
  attached, rather than out of a hand-tuned threshold.

**Do this before optimising the classifier.** A well-calibrated mediocre model produces a
good product. A miscalibrated excellent model produces a product that confidently shows
the wrong thing to people who gave it nothing to work with.

---

## 6. M5 — Ranker and decision policy.

**Consumes:** candidates plus session vector plus context.
**Produces:** the ranked slate, plus the propensity that makes evaluation possible later.

**Contextual bandit**, logistic Thompson sampling (PG-TS) or LinUCB, with four constraints
that are not optional in a public-sector setting:

1. **Certainty override.** Exact-match or inbound-with-service-code bypasses the bandit
   entirely. Never explore on a user who told you exactly what they want.
2. **Tiered exploration.** Slot 1 exploits only. Exploration is capped in slots 2 and 3 and
   banned entirely from appeals, complaints, and emergency services.
3. **Slate-aware ranking.** Three independently ranked slots will say the same thing three
   ways. Model the slate jointly or enforce diversity explicitly.
4. **Log the propensity at decision time.** Non-negotiable and non-retrofittable. Without it
   you can never evaluate a new policy offline and are locked into full-traffic A/B forever.

---

## 7. M6 — Uplift model. Worth knowing about.

**Question it answers:** not "what will this user click" but "does personalising this
session help, compared with showing the default".

**Model:** two-model or X-learner uplift estimation on logged data with a permanent holdout.

**Why it matters here:** a large fraction of sessions are better served by the plain default,
and a ranking model will never tell you that because it is not the question it was asked.
The uplift model identifies the sessions where intervention is actually worth it, which is
the difference between a system that personalises constantly and one that personalises well.

---

## Signal-to-model routing

| Signal group | M0 rules | M1 prior | M2 sequence | M3 state | M5 ranker |
|---|---|---|---|---|---|
| Geo, ASN, timezone | | ● | | | ● |
| Connection, device class | ● | ● | | | ● |
| Declared preferences | ● | | | | |
| Permission states | ● | | | | |
| Locale, calendar | ● | ● | | | ● |
| Temporal + ambient join | | ● | | | ● |
| Referrer, entry URL, UTM | | ● | ● | | |
| Scroll, dwell, pointer | | | ● | ● | |
| Query text | | | ● | | ● |
| Copy, zoom, rage, back-nav | | | ● | ● | |
| Event sequence order | | | ● | | |

---

## What the whole stack costs

| Stage | Latency | Where |
|---|---|---|
| M0 rendering rules | <0.1 ms | edge worker |
| M1 cold-start prior | <0.5 ms | edge worker |
| Query embedding | ~7 ms CPU | edge or client |
| M2 EWMA / session-as-text | <1 ms | edge or client |
| Retrieval, exact scan over 1,208 items | ~0.8 ms | edge or client |
| M4 calibration | <0.1 ms | edge worker |
| M5 bandit scoring | <2 ms | edge worker |
| **Total** | **~12 ms** | inside a 30 ms budget |

Embedding is the dominant cost by an order of magnitude. Any latency work starts there,
not in retrieval, and the first move is caching query embeddings rather than optimising the
search structure.
