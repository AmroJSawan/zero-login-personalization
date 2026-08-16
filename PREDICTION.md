# What the signals lead to, and the models that predict from them

Constraints are parked in the other documents. This one is purely capability and model
selection: what you can infer from the signal surface, what you can predict, and which
model to reach for.

---

## Part 1: What the signals actually let you conclude

Signals do not arrive as conclusions. Each inference is a chain, and the useful move is to
be precise about where the chain gets weak.

### Strong inferences (precision high enough to act on)

| Evidence | Inference | Why it holds |
|---|---|---|
| Corporate ASN + business hours + desktop + high navigation efficiency | Acting in a **work capacity**, likely a professional intermediary | Three independent signals agree; efficiency is hard to fake |
| Mobile carrier ASN + evening + mobile + low efficiency | Acting in a **personal capacity**, first-time or infrequent | Same, inverted |
| Entry query uses the exact institutional service name | **Repeat or informed user** | Nobody says "Issuance of Vehicle Details Validity Certificate" on their first visit |
| Entry query is colloquial ("renew my car papers") | **First-timer**, vocabulary mismatch | Direct evidence of the gap |
| Session timezone disagrees with IP geolocation | **Traveller, VPN, or recent arrival** | Deterministic, not statistical |
| Arabic primary + Islamic calendar + local geo | **National or long-term resident** | Preference stack is set deliberately |
| Deadline date derivable from statutory calendar + service context | **Urgency** | Derived from a known calendar, not observed at all |
| Service position in a known prerequisite chain | **Life-event stage** | The graph tells you, behaviour just locates them on it |
| Repeated language switching mid-session | **Bilingual, or terminology failure in one language** | Very high value: it localises exactly which term broke |
| 20 to 30 interactions with struggle patterns | **Frustration**, ~91% accuracy, AUC 0.97 | Published clickstream result |

The **professional intermediary** row is the one most portals never model and the one with the
highest operational leverage. Typing centres, PRO services and corporate admin staff transact
in volume, know the vocabulary, need zero explanation, and want density and speed. They are
trivially separable from citizens by navigation efficiency and ASN, and serving them the
hand-holding first-timer experience wastes everyone's time. Detecting them is easy and the
payoff is immediate.

### Weak inferences (derivable, low precision, poor basis for action)

| Evidence | Tempting inference | Why it is unreliable |
|---|---|---|
| Reading speed normalised by content length | Literacy or education level | Confounded with interest, familiarity, and whether they are skimming to find one number |
| Frequent pinch-zoom on body text | Vision impairment | Also just a small phone, bright sunlight, or scrutinising a fee |
| Target miss rate, slow acquisition | Motor impairment | Also a moving vehicle, a cheap touchscreen, or a cold hand |
| Device price tier + neighbourhood geo | Income band | Device is shared, inherited, work-issued; geo is a centroid |
| Session length | Engagement | Long sessions are frequently failure, not interest |

These are listed because they will come up in workshops. The engineering point is not that
they are forbidden, it is that acting on a 55%-precision inference in a Tier B or C adaptation
produces a worse product than not acting. If you want accessibility accommodation, the reliable
route is already on the table: `prefers-reduced-motion`, `prefers-contrast`, `forced-colors`
and target-size preferences are **declared**, not inferred, and they are close to 100% precise.

---

## Part 2: Be precise about the prediction target

Model choice follows the target, and these get conflated constantly. There are eight distinct
questions here, not one.

| # | Target | Horizon | Question |
|---|---|---|---|
| P1 | Next click or page | seconds | Which element next |
| P2 | Next service | minutes | Which service this session is heading to |
| P3 | Session outcome | this session | Complete or abandon |
| P4 | Time to abandonment | continuous | *When* will they give up |
| P5 | **Next service in the real-world chain** | **days to months** | What will they need after this is done |
| P6 | Preference ranking | any | Given N candidates, what order |
| P7 | Intervention uplift | any | Does acting help, versus doing nothing |
| P8 | Return time | days | When will they come back |

P5 is where the value is on a government portal, and it is covered in Part 4.

---

## Part 3: Model selection by target

### P1 / P2 — next item, sequence prediction

An ordered ladder. The top of it is much stronger than people expect.

| Model | Data needed | Notes |
|---|---|---|
| **First-order Markov transition matrix** | ~1k sessions | A service-to-service transition matrix with smoothing. Trains in seconds, inspectable by a domain expert, and it is a genuinely hard baseline |
| **Session-KNN / item-item co-occurrence** | ~5k sessions | Find the k most similar past sessions, recommend what they did next. **Repeatedly shown to match or beat neural session recommenders** on many benchmarks. Do not skip it |
| **HMM over latent states** | ~10k sessions | See below. Interpretable, low-data, gives state *and* transition probabilities |
| **GRU4Rec** | ~100k | Classic session RNN, handles variable length natively |
| **SR-GNN** | ~100k | Models each session as a graph, gated GNN over it. Strong on short sessions with repeats |
| **GCE-GNN** | ~500k | Adds a *global* item-transition graph across all sessions on top of the local session graph. Consistently outperformed prior state of the art on benchmarks |
| **SASRec / BERT4Rec** | ~500k | Self-attentive, the standard modern choice |
| **HSTU** | millions | Exhibits recsys scaling laws |
| **TIGER / RQ-VAE semantic IDs** | millions | Autoregressive generation of item IDs, no index at all |

For a ~1,200-service catalog with short anonymous sessions, the top four rows are the realistic
operating range. GCE-GNN is the most interesting jump because the global graph directly encodes
"which services follow which" across the whole population, which is exactly the structure a
government catalog has.

### P3 / P4 — outcome and timing

**P3 (will they abandon)** is a classification problem, and it is largely solved: XGBoost on
tabular session features reaches ~90% accuracy (AUC 0.958), an LSTM on the raw event sequence
~91% (AUC 0.971), and the sequence model is reliable from the first 20 to 30 interactions.

**P4 (when will they abandon)** is the more useful and less commonly built one. Use a
**discrete-time hazard model**: reshape each session into person-period rows (one row per time
interval, with a binary "did the event occur in this interval" outcome), then apply any binary
classifier to predict the conditional hazard per interval. Discrete-time models frequently
outperform continuous-time Cox on this shape of data.

Why this matters more than P3: it outputs a **hazard curve**, not a label. You learn not just
"this session is at risk" but "risk of abandonment rises sharply in the next 15 seconds". That
is precisely the input the timing problem needs. A model that says *when* is worth more than a
model that says *whether*, because intervention timing is the harder half of the problem.

Dwell times within a session are well modelled by a **Weibull** distribution, which gives you a
parametric handle on the same question with very little data.

For P8 (return time), RNN survival models conditioned on absence time are the established
approach and beat both plain RNNs and Cox baselines.

### Latent state — the underrated model

A **hidden Markov model** over a small state space (`browsing`, `searching`, `comparing`,
`struggling`, `deciding`, `abandoning`) is a strong fit and routinely skipped in favour of deep
learning the team cannot feed. HMM ensembles are lightweight, interpretable and efficient, and
they perform well specifically in imbalanced or scarce-data regimes. They have an established
track record inferring latent states like purchase readiness, churn risk and browsing intent
where interpretability is a requirement.

What you get that a classifier does not give you: the **transition matrix**. Knowing that
`comparing → struggling` has probability 0.31 while `comparing → deciding` has 0.52 is a
product insight, not just a prediction, and a domain expert can read it and tell you whether it
is right.

### P6 — preference ranking

- **Two-tower** (session tower, item tower, dot product). Servable at the edge, scales fine.
- **LightGBM / LambdaMART** listwise ranker on engineered features. Boring, strong, hard to beat.
- **Contextual bandit** (PG-TS, LinUCB) when you need to learn online and control exploration.

Note that classical matrix factorization does not apply: there are no persistent user IDs.
Item-item collaborative filtering computed over session co-occurrence does apply, and is the
correct collaborative-filtering formulation for anonymous traffic.

### P7 — uplift

**T-learner, X-learner, or causal forests** on logged data with a permanent holdout. This
answers "does personalising this session help versus showing the default", which no ranking
model can answer because it is not the question a ranker is asked. A large share of sessions
are better served by the plain default, and only an uplift model will tell you which.

---

## Part 4: The domain-specific opportunity

**Government is not e-commerce, and copying e-commerce here leaves the best prediction on the table.**

In retail, next-click is the goal because purchase intent is diffuse and perishable. In
government, the sequences are real, causal, and often statutory. A residence visa is issued,
which *requires* an Emirates ID within a defined window, which *enables* a driving licence
transfer, which *precedes* vehicle registration, which *recurs* annually.

That structure means P5 (what will this person need in 30 to 90 days) is both more valuable and
more predictable than P1. You are not guessing at taste; you are locating someone on a graph
whose edges are defined by regulation.

**The model combination:**

1. **The prerequisite graph supplies structure.** `PRECEDES` and `REQUIRES` edges mined from
   real session and transaction data (service A then service B within N days, lift over base
   rate), then validated by subject-matter experts. Do not hand-author these; the real chains
   are not the ones on the org chart.

2. **A temporal point process supplies timing.** Hawkes processes are the right formalism: they
   are *self-exciting*, meaning an event raises the intensity of correlated future events, with
   a decay. That is exactly what "visa issued" does to "Emirates ID application". A
   user-dependent intensity kernel gives you a conditional probability of the next interaction
   over time rather than just a ranked list.

3. **Time-interval-aware modelling handles recurrence.** Recent work (TIDE and similar) uses
   Hawkes-enhanced time encoding to capture item-specific periodicity and non-monotonic decay,
   which is the right treatment for annual renewals, inspection cycles and permit expiries.

4. **Per-edge survival models supply the hazard.** For each (A → B) edge, a hazard function over
   days-since-A. This tells you *when* to surface B, not just that B is coming.

The output is a system that says: *this person completed a visa transaction 41 days ago; the
hazard for Emirates ID application peaks around day 45; surface it now.* No login, no identity,
no stored profile. Just a position on a graph and a clock, and it can run entirely from a
device-local record of what the anonymous session has already done.

That is a materially different and more defensible product than next-click prediction, and it
is exactly what the graph structure of a statutory service catalog is suited to support.

---

## Part 5: How they compose

Not one model. A small ensemble where each answers a different question:

| Question | Model | Output |
|---|---|---|
| **What state are they in?** | HMM | latent state + transition probabilities |
| **What will they want?** | Session-KNN → GCE-GNN ladder | ranked candidates |
| **When should we act?** | Discrete-time hazard | risk curve over next intervals |
| **Should we act at all?** | Uplift model | expected gain vs default |
| **What exactly do we show?** | Contextual bandit | slate + propensity |
| **How sure are we?** | Conformal prediction | prediction set → UI tier |
| **What comes next month?** | Graph + Hawkes + per-edge survival | service + timing |

The routing is the design: the state model decides which of the others to consult. A user in
`struggling` should not be handed a ranked list of services; they should hit the timing and
uplift models, and probably a human.

---

## Part 6: The data ladder

Model choice is a function of volume before it is a function of ambition.

| Sessions available | Justified |
|---|---|
| < 10k | Markov transitions, content embeddings, rules, HMM |
| 10k – 100k | Session-KNN, GBDT classifiers, HMM, discrete-time hazard |
| 100k – 1M | GRU4Rec, SR-GNN, LSTM sequence models |
| 1M – 10M | SASRec / BERT4Rec, GCE-GNN, two-tower, Hawkes |
| 10M+ | HSTU, TIGER, generative retrieval |

National-scale portals report transaction volumes in the tens of millions per year, so the
top of this ladder is reachable on volume. That is not a reason to start there. The published benchmarks where simple
nearest-neighbour baselines match or beat neural session recommenders exist precisely because
teams skipped the bottom rungs and never measured what they cost themselves.

**Build order:** Markov and session-KNN first, as the baseline every later model must beat.
HMM next, because it produces product insight as a side effect. Discrete-time hazard third,
because timing is the harder problem and almost nobody has solved it. Neural sequence models
fourth, and only if they beat session-KNN on replay. The graph plus Hawkes layer in parallel
throughout, because it does not compete with the others and it is where the differentiated
value is.

---

## Sources

- [Session-based Recommendation with Graph Neural Networks (SR-GNN, AAAI 2019)](https://sxkdz.github.io/files/publications/AAAI/SR-GNN/SR-GNN.pdf)
- [Global Context Enhanced Graph Neural Networks for Session-based Recommendation (GCE-GNN, SIGIR 2020)](https://arxiv.org/abs/2106.05081)
- [Graph and Sequential Neural Networks in Session-based Recommendation: A Survey](https://arxiv.org/pdf/2408.14851)
- [Machine Learning to Predict Digital Frustration from Clickstream Data](https://arxiv.org/abs/2512.20438)
- [Survival prediction models: an introduction to discrete-time modeling](https://bmcmedresmethodol.biomedcentral.com/articles/10.1186/s12874-022-01679-6)
- [A Recurrent Neural Network Survival Model: Predicting Web User Return Time](https://arxiv.org/pdf/1807.04098)
- [Predicting Session Length in Media Streaming](https://arxiv.org/pdf/1708.00130)
- [Applying hidden Markov models for user and entity behavioural analytics](https://www.sciencedirect.com/science/article/pii/S2772941926000311)
- [Attentive Hawkes Process Application for Sequential Recommendation](https://link.springer.com/chapter/10.1007/978-3-031-30672-3_32)
- [Time-Interval-Aware Disentangled Expert Modeling for Next-Basket Recommendation (TIDE)](https://arxiv.org/html/2605.00499v1)
- [Local Low-Rank Hawkes Processes for Temporal User-Item Interactions](https://jshang2.github.io/pubs/local-low-rank.pdf)
