# Anonymous Personalization: A Reference Architecture

Domain-agnostic. No vertical, no client, no case study. This is the general problem and the
general solution.

---

## 1. The problem, stated exactly

A system receives a stream of HTTP requests carrying no persistent identifier. It must select
what to render within a bounded latency, and improve that selection over time from observed
outcomes.

Formally, this is a **partially observable Markov decision process with episodic reset and no
cross-episode memory**:

```
observation   oₜ ∈ O     request metadata + client telemetry
latent state  sₜ ∈ S     user intent — never directly observed
action        aₜ ∈ A     what gets rendered
reward        r          task completion — sparse, delayed, often never observed
belief        bₜ = P(sₜ | o₁..ₜ)
policy        π(a | b)

constraints:  compute π within τ milliseconds
              b resets to prior at every episode boundary
```

The episodic reset is the defining constraint. Every property that distinguishes this problem
from ordinary personalization is a consequence of it.

---

## 2. Five invariants

These hold regardless of domain, scale, or stack.

**I1 — User-side collaborative filtering is unavailable.** Matrix factorization, user
embeddings, and user-user similarity all require persistent identity. All dead. Item-item
co-occurrence computed over sessions survives and is the correct CF formulation for anonymous
traffic. This is not a degraded substitute; it is the right method for the data you have.

**I2 — Every episode is a cold start.** The prior cannot come from this user's history because
there is none. It must come from population structure: item co-occurrence, request-time
context, and the item graph. Systems that treat cold start as an edge case are mis-specified
here, because cold start is 100% of traffic.

**I3 — Belief construction is the hot path.** The belief update runs on every event of every
session. It is executed more often than anything else in the system and its cost dominates.
Optimise it before optimising the model that consumes it.

**I4 — Your policy generates your training data.** Logged data is confounded by the policy that
produced it. Without logged propensities you cannot evaluate a candidate policy offline, ever,
and this is not recoverable retroactively. **Log `(context, action, propensity, outcome)` from
the first day the system serves anything.** It is the single decision in this architecture that
cannot be revisited later.

**I5 — Latency is a hard cap on model class, not a preference.** The budget determines the
feasible model set before accuracy enters the discussion. Choose the budget first, derive the
feasible set, then optimise within it.

---

## 3. The physics

Engineering here is mostly arithmetic. Do the arithmetic before choosing components.

### 3.1 The exact-search crossover

Exhaustive similarity search over `N` items of `d` dimensions costs `N·d` multiply-accumulates.

Measured throughput, single thread, `Int8Array` with float accumulator, plain JavaScript:
**≈ 580M MAC/s**. WASM SIMD gives roughly 4–8×. Native int8 dot-product instructions give
roughly 20–50×.

Feasible catalog size at budget `τ` and dimensionality `d`:

```
N ≤ (throughput × τ) / d
```

| Runtime | Throughput | τ = 5 ms, d = 384 | τ = 10 ms, d = 256 |
|---|---|---|---|
| Plain JS | 580M MAC/s | ~7,500 items | ~22,000 items |
| WASM SIMD (×6) | 3.5G MAC/s | ~45,000 items | ~136,000 items |
| Native int8 (×30) | 17G MAC/s | ~225,000 items | ~680,000 items |

**Rule: build an approximate index only when `N·d > throughput × τ`.** Below that line, exact
search is faster end to end and strictly better: no index build, no recall loss, no memory
overhead, no staleness, no tuning, no rebuild pipeline.

Most catalogs outside consumer-scale retail and media sit below this line. The vector index is
the most over-engineered component in this field by a wide margin.

### 3.2 Representation size

Index memory is `N × d × bytes_per_dim`. Two results that generalise:

- **int8 quantization is nearly free.** Measured cost ≈ 1 point of P@1 for a 4× size reduction.
- **Dimension truncation is not free.** Measured cost ≈ 31 points of P@1 truncating 384→128,
  on a model not trained for it.

The general principle: **nested representations must be trained for, not imposed.** Matryoshka
truncation works only on models trained with Matryoshka representation learning. Quantize
aggressively; truncate only with a model that earned it.

### 3.3 Session state

```
belief vector      d × 4 bytes
event ring buffer  k × ~32 bytes
counters/flags     ~128 bytes
```

At `d = 384`, `k = 20`: **≈ 2.2 KB per active session.**

| Concurrent sessions | State memory |
|---|---|
| 100k | 220 MB — single node |
| 1M | 2.2 GB — single large node |
| 10M | 22 GB — shard |
| 100M | 220 GB — shard |

Sessions are mutually independent, so sharding is a hash of the session key with **no
cross-shard coordination, ever**. Horizontal scaling here is genuinely free, which is rare.

### 3.4 Throughput

`RPS_per_node = cores / decision_cost`. At 2 ms per decision on 16 cores: ~8,000 RPS per node.
The decision loop is CPU-bound and embarrassingly parallel; there is no shared mutable state on
the request path.

---

## 4. The belief-state view unifies the model zoo

The most useful reframing in this architecture: **every session encoder is a belief update
operator** `bₜ = f(bₜ₋₁, oₜ)`. Choosing an encoder is choosing an update rule and a belief
representation.

| Encoder | Update rule | Belief representation | Cost per event |
|---|---|---|---|
| EWMA | `b ← λb + (1−λ)e(o)` | point in embedding space | O(d) |
| Count sketch | bin increment | histogram | O(1) |
| HMM | forward algorithm | categorical over K states | O(K²) |
| Linear-Gaussian | Kalman update | Gaussian (mean, covariance) | O(d²) |
| GRU / LSTM | gated recurrence | hidden vector | O(d²) |
| Transformer | attention over full history | recomputed from scratch | **O(t·d²)** |
| Particle filter | importance resampling | weighted sample set | O(P·d) |

The row that matters is the transformer. **Recursive updates are constant cost per event.
Attention is linear in history length.** A transformer recomputes the entire belief on every
new observation. At high event rates, or on a client device, or in long sessions, that cost
difference dominates benchmark accuracy differences.

This is why the honest ordering is: start with a recursive update, and only pay for attention
when you have measured that it wins by more than its cost. It also explains why HMMs remain
competitive here despite being unfashionable: `O(K²)` with `K = 6` is nothing, and the belief
is a calibrated categorical distribution rather than an uninterpretable vector.

---

## 5. Action space design

Actions should be selected by **failure cost**, not expected value, because the loss is
sharply asymmetric:

```
L(wrong action) ≫ L(abstain) > L(right action)
```

Partition the action space by regret bound:

| Class | Property | Examples | Max regret |
|---|---|---|---|
| **Additive, non-displacing** | adds emphasis or content without moving anything | gradual-onset emphasis, prefetch, ordering inside a not-yet-visible list, progressive disclosure | **bounded and small** |
| **Additive, displacing** | occupies a fixed reserved region | one adaptive slot | bounded, moderate |
| **Subtractive or rearranging** | removes or moves what the user already learned | reordering navigation, hiding items, layout change | **unbounded** |

**The rule: an action with unbounded regret must never be driven by an uncertain model.** No
accuracy figure makes it safe, because the failure mode is "the user cannot find something they
know exists", and that cost is paid on every subsequent visit, not just the one where the model
was wrong.

Design the action set so that the **null action is always available and always cheap**. If
abstaining is expensive, the architecture is wrong.

---

## 6. Abstention is a first-class action

The decision layer must be able to output "I do not know". This requires calibration, not
capacity: a more accurate model that cannot express uncertainty is less useful than a weaker
one that can.

**Conformal prediction** is the right mechanism. Choose a coverage level; it returns a
prediction *set* guaranteed to contain the truth at that rate, distribution-free and with
finite-sample validity. Set size maps directly onto action tiers:

```
|set| = 1        →  commit: single confident action
|set| = 2..3     →  offer: present the alternatives
|set| > 3        →  abstain: render the default
```

The tiers fall out of a statistical guarantee rather than a hand-tuned threshold. Threshold
tuning is where confidence-gated systems normally rot.

Note the failure mode this defends against, which is common and counterintuitive: **normalized
score functions become more confident as evidence disappears.** A scoring rule that divides by
the sum of weights returns maximal confidence when exactly one weak signal fired. Calibration
must be measured on deliberately low-evidence inputs, not only on average traffic.

---

## 7. The learning loop

```
serve → log(context, action, propensity, outcome) → offline evaluation
     → candidate policy → interleaving → A/B → promote → serve
```

**Offline:** inverse propensity scoring, self-normalized IPS, doubly robust. Cheap, noisy,
filters most candidates.

**Online, fast:** interleaving. Competitive-pair designs reach a decision far faster than
parallel A/B because the comparison is within-user rather than between-user.

**Online, definitive:** A/B with a permanent holdout that never receives personalization. The
holdout is the only instrument that detects slow drift.

**Orthogonal:** an uplift model (T-learner, X-learner, causal forest) answering "does acting
beat doing nothing", which no ranking model can answer because it is not the question a ranker
is asked.

### Why contextual bandits and not reinforcement learning

Episodes are short (typically 5–30 events), reward is terminal and sparse, and state transitions
are mostly user-driven rather than action-driven. Credit assignment depth is shallow. A
contextual bandit at each decision point captures most of the available value at a fraction of
the variance and a fraction of the engineering cost.

Escalate to sequential RL only after demonstrating that actions change the *trajectory* rather
than just the immediate response. That is an empirical question with a cheap test, and the
answer is usually no.

---

## 8. Scaling globally

The architecture decomposes cleanly into two categories, and **nothing is in both**:

| Category | Contents | Consistency requirement |
|---|---|---|
| **Globally replicated, read-only** | item index, model parameters, policy weights, calibration maps | eventual; versioned; atomic swap |
| **Shard-local, ephemeral** | session belief state | none — single writer per session by construction |

There is no distributed transaction anywhere in this system. That is the property that makes it
scale to arbitrary request volume.

**Multi-region deployment:**

- **Artifacts** (index, models, calibration): content-addressed, pushed to every point of
  presence, version-pinned, atomically swapped. Rollback is a pointer change.
- **Session state**: pinned to the nearest PoP, never replicated. Episodes are short; if the PoP
  fails mid-session the system degrades to the default action, which is an acceptable and
  already-designed outcome.
- **Outcome logs**: asynchronous fan-in to a central store. Never on the request path.
- **Model refresh**: hours to days. Nothing requires sub-minute global consistency.

The one exception worth building deliberately: a **hot-facts overlay** for values that must
never be served stale (prices, deadlines, eligibility thresholds). Small key-value layer,
propagates in seconds, overrides anything embedded in the model or index. Never let a learned
representation be the source of truth for a fact that changes.

---

## 9. Failure taxonomy

| Failure | Mechanism | Mitigation |
|---|---|---|
| Confidence saturation | normalized scores maximal under sparse evidence | calibrate on low-evidence inputs; conformal sets |
| Feedback loop collapse | policy only ever sees what it chose | logged propensities + forced exploration floor |
| Popularity collapse | ranker converges on head items | minimum-exposure constraint per item |
| Slate redundancy | independently ranked slots duplicate intent | joint slate modelling or explicit diversity constraint |
| Automation poisoning | bots inflate arm statistics | separate bot traffic before the training stream |
| Stale facts | learned representation used as source of truth | hot-facts overlay with effective dating |
| Silent drift | no unpersonalized reference exists | permanent holdout |
| Latency regression under load | model cost scales with history length | recursive belief update; cap history |
| Shared-device leakage | belief outlives the person | short TTL; explicit reset affordance; shorter TTL on shared contexts |

---

## 10. Build ladder

Each rung is gated on beating the previous one, measured on the same corpus with the same rig.

1. **Instrumentation and the substitution harness.** Four contracts (encoder, retriever, ranker,
   renderer), a labelled corpus, one scoring rig. Propensity logging from the start.
2. **Population baselines.** Item-item co-occurrence, Markov transitions, popularity priors.
   These define the bar.
3. **Recursive belief update.** EWMA, then HMM. Cheap, interpretable, constant cost.
4. **Calibration and abstention.** Before any accuracy work. This is what makes the system
   safe to ship.
5. **Additive, non-displacing actions only.** Bounded regret. Ship these while accuracy is still
   poor, because they are robust to being wrong.
6. **Timing.** Discrete-time hazard modelling. Deciding *when* to act is harder and more
   valuable than deciding *what*, and is usually skipped entirely.
7. **Learned sequence encoders.** Only if they beat step 3 on replay by more than their serving
   cost. Frequently they do not at moderate catalog size.
8. **Online learning.** Contextual bandit with exploration floors and constraint set.
9. **Uplift.** Decide *whether* to act at all, per session.

Steps 4 and 5 are the ones that get skipped and the ones that determine whether the system is
shippable. Steps 7 and 8 are the ones that get built first and are the least load-bearing.

---

## Summary

The whole architecture reduces to four claims:

1. **It is a POMDP with episodic reset.** Belief construction is the core computation; every
   encoder is a belief update rule, and recursive rules are constant-cost while attention is not.
2. **The arithmetic decides the components.** Exact search beats approximate search below
   `N·d = throughput × τ`, which covers most real catalogs. Quantize freely; do not truncate.
3. **Asymmetric loss decides the action space.** Choose actions with bounded regret, make
   abstention free, and never drive an unbounded-regret action from an uncertain model.
4. **Propensity logging decides whether you have a future.** Everything else can be rebuilt
   later. That cannot.
