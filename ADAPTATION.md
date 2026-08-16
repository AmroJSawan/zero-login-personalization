# The temporal layer: what accumulating behaviour tells you, and what to do about it

Companion to `index.html` (the first-shot signal surface) and `MODELS.md` (the model stack).
This covers the second phase: what becomes knowable as interactions accumulate, and what the
evidence says about adapting an interface in response.

---

## The finding that should reorder the work

The instinct is to improve prediction accuracy first, then adapt. The literature says the
opposite: **the adaptation technique determines whether being wrong is survivable, and it
matters more than the accuracy itself.**

Findlater and Gajos's *ephemeral adaptation* (CHI 2009) is the cleanest demonstration. Instead
of reordering a menu to put predicted items on top, every item stays exactly where it always
was; predicted items simply appear immediately while the rest fade in over a few hundred
milliseconds. Across two experiments with 48 users, ephemeral adaptive menus were **faster
than static menus when prediction accuracy was high, and not significantly slower when
accuracy was low.** They also beat adaptive highlighting.

That is an adaptation with an *asymmetric payoff*: it wins when right and costs nothing when
wrong. Spatial reordering has the opposite shape. It wins a little when right and costs a lot
when wrong, because the user's spatial memory is now lying to them.

**Practical consequence:** choose adaptations by their failure cost before optimising the model
that drives them. A 60%-accurate model driving a Tier A adaptation is a better product than a
90%-accurate model driving a Tier C one.

---

## Part 1: The temporal knowledge ladder

What becomes available as a session accumulates. Stages are event counts, not seconds, because
event density varies enormously between a decisive user and a browsing one.

| Stage | Events | Newly knowable | Confidence | Basis |
|---|---|---|---|---|
| **T0** | 0 | Locale, device class, network, coarse geo, referral, temporal context, accessibility preferences | High on facts, weak on intent | Request headers + first paint |
| **T1** | 1–2 | Entry velocity, whether they scrolled at all, viewport engagement | Low | Scroll and visibility events |
| **T2** | 3–5 | Reading mode (scanning / skimming / reading) from scroll velocity distribution, first section of genuine attention, pointer input type | Moderate | IntersectionObserver + scroll velocity |
| **T3** | 6–10 | Topic interest from dwell distribution, search intent from partial query, hesitation and uncertainty from pointer path | Moderate to high once a query appears | Dwell + query |
| **T4** | 10–20 | Task vs browse distinction, comparison behaviour (repeat visits to two sections), early struggle indicators | High | Sequence patterns |
| **T5** | **20–30** | **Frustration reliably predictable** | ~91% accuracy, ROC AUC 0.97 | Published clickstream LSTM result |
| **T6** | 30+ | Abandonment risk, task completion likelihood, whether intervention would help at all | High | Full-sequence models |

The T5 row is the direct answer to "what can I know after some interactions". A 2025 study on
5.4 million clickstream events across 304,881 sessions found XGBoost reached ~90% accuracy
(AUC 0.958) and an LSTM ~91% (AUC 0.971) at classifying a session as frustrated, and reported
that **the LSTM predicts frustration reliably from only the first 20 to 30 interactions.**

That is the load-bearing number for this phase. Frustration is not a lagging indicator you
discover in a post-hoc report. It is detectable in-session with time left to act.

---

## Part 2: Operational signal definitions

Vendor practice has converged on a fairly stable set. These are the definitions to implement,
with the thresholds that matter.

| Signal | Operational definition | Precision | Notes |
|---|---|---|---|
| **Rage click** | 3+ clicks on the same target within ~1s in a small radius | High | The canonical frustration signal. Fires when an element looks responsive and is not |
| **Dead click** | Click on an element that looks interactive but has no handler | High | Almost always a real design defect, not a user problem |
| **Error click** | Click that precedes a console or network error | High | Cheap to instrument, directly actionable |
| **Thrashed cursor** | Rapid erratic pointer movement without target acquisition | Moderate | Confusion or waiting, ambiguous between them |
| **U-turn** | Navigate to a page and return within a few seconds | High | "Pogo-sticking". Strong dissatisfaction signal for the destination |
| **Search struggle** | Query reformulation chain without a result click | Very high | The user is telling you your vocabulary is wrong |
| **Form churn** | Repeated edits or refocus on the same field | Very high | Field-level, so it localises the problem precisely |
| **Long wandering session** | High event count, low progress toward any goal | Moderate | Needs a goal model to be meaningful |
| **Copy event** | User copies text | **Very high** | They found the answer and are extracting it. Under-instrumented everywhere |
| **Pinch-zoom on content** | Zoom gesture on a table or body text | High | Either the text is too small or they are scrutinising a number |
| **Exit intent** | Pointer exits viewport through the top edge | Moderate on desktop, meaningless on mobile | Widely abused; use sparingly |

Two implementation cautions from vendor practice:

**Set a combined threshold before declaring frustration.** FullStory explicitly requires a
high enough volume of combined events before classifying a session as frustrated, precisely to
suppress false positives. A single rage click is noise; a rage click plus a U-turn plus a
reformulated query is a signal.

**Score by percentile, not absolute count.** Contentsquare's frustration scoring uses
percentile metrics across devices. Absolute event counts are not comparable between a mobile
user on a slow connection and a desktop user, and a fixed threshold will systematically flag
the former.

---

## Part 3: What the research says about adapting

This is where the intuition is most often wrong. Five findings, in order of how much they
should constrain the design.

### 3.1 Accuracy has a threshold, below which adaptation is net harmful

Predictive accuracy has a significant effect on user performance in adaptive interfaces, and
the evaluation literature is genuinely mixed: some studies find adaptive menus faster or
preferred, others find the opposite. The variance is largely explained by accuracy and by
which adaptation technique was used. This is why the technique choice comes first.

### 3.2 Spatial stability is the dominant user preference

Users show high preference for adaptations that preserve spatial position and orientation and
tolerate value changes, and low preference for adaptations that change colour, motion, or
shape. Anything that moves a control the user has already learned is expensive, and the cost
is paid on every future visit, not just the one where the prediction was wrong.

### 3.3 Ephemeral adaptation is the technique that survives being wrong

Covered above. Gradual onset, no spatial change. This should be the default adaptation
primitive for anything above the fold.

### 3.4 Proactive help can backfire even when it is correct

A 2025 study found that anticipatory help **increased users' self-threat and reduced adoption**,
identifying self-threat as the mechanism by which proactive assistance backfires. Related work
found that people who received assistance only on request engaged more critically with the
advice and were less likely to be misled than those who received it unsolicited. Unsolicited
initiative can undermine the psychological needs for competence and autonomy even when the
help is accurate and useful.

**This matters disproportionately for a government portal.** Citizens frequently arrive in a
position of obligation or vulnerability: a fine, a visa deadline, a benefits application. A
system that announces it knows what they need can read as surveillance rather than service.
The same adaptation framed as "here is the shortcut you were heading for" versus "we know why
you are here" produces very different reactions with identical underlying machinery.

### 3.5 Mixed-initiative principles still hold

Horvitz's 1999 principles remain the correct checklist, and 2025-2026 work revisiting them for
AI systems reaches the same conclusions. The ones that bind hardest here:

- Consider the **uncertainty** of the inference, not just its argmax.
- Consider the **cost-benefit** of acting, including the cost of being wrong.
- **Minimise the cost of poor guesses.**
- Allow **efficient invocation and termination** by the user.
- **Scope the precision of the service to the uncertainty.** Low confidence should produce a
  weaker, vaguer intervention, not a confident wrong one.

The contemporary framing of the open problem is the **"Goldilocks time window"**: knowing *when*
to intervene remains harder than knowing *what* to offer, and mistimed help is disruptive even
when its content is right.

---

## Part 4: Adaptation pattern library, ranked by failure cost

The practical output. Order your roadmap by this table, not by expected lift.

### Tier A — benign failure. Deploy on moderate confidence.

| Pattern | Mechanism | Cost when wrong |
|---|---|---|
| **Ephemeral emphasis** | Predicted items render immediately, others fade in over ~250ms. No reordering | Essentially none; measured as not significantly slower than static |
| **Speculative prefetch** | Prerender top prediction, prefetch next two | Wasted bytes only. Gate on connection and Save-Data |
| **Ordering inside an opened list** | Reorder search suggestions or filter values that were not visible until invoked | Low; no spatial memory existed yet |
| **Progressive disclosure depth** | Expand the section they dwelled on, keep others collapsed | Low; one click to recover |
| **Copy adaptation** | Adjust reading level or terminology, not content | Invisible when wrong |
| **Asset weight** | Image tier, motion, JS budget by device and network | Invisible when wrong |

### Tier B — recoverable failure. Requires calibrated confidence.

| Pattern | Mechanism | Cost when wrong |
|---|---|---|
| **Fixed adaptive slot** | One reserved region whose contents change, position never moves | Wasted attention on one card |
| **Inline help offer** | Offer assistance after a struggle signal, dismissible | Mild annoyance; risks the self-threat effect |
| **Contextual prerequisite hint** | "This service also needs X", derived from the service graph | Low if phrased as information, not instruction |
| **Search vocabulary bridging** | After a failed query, suggest the institutional term for the colloquial one | Low; directly addresses a known failure |

### Tier C — costly failure. High confidence and a permanent holdout only.

| Pattern | Cost when wrong |
|---|---|
| **Reordering primary navigation** | Breaks learned spatial memory permanently |
| **Hiding or collapsing items by prediction** | User cannot find what they know exists. The classic adaptive-menu failure |
| **Layout restructuring** | Destroys page grammar; catastrophic for repeat users |
| **Auto-advancing a flow** | Removes agency; directly triggers the self-threat mechanism |
| **Modal interruption on predicted struggle** | Mistimed help is disruptive even when correct |

### Tier D — do not build.

Removing navigation paths, auto-submitting anything, altering legally operative content
(fees, eligibility, deadlines) based on inference, or making the default deck unreachable.
On a public service, personalization may add a shortcut. It may never remove a route.

---

## Part 5: Mapping detected state to response

Frustration is not one thing, and the correct response differs sharply. This is why the
interaction-state classifier (M3 in `MODELS.md`) is kept separate from the intent model.

| Detected state | Evidence pattern | Correct response | Wrong response |
|---|---|---|---|
| **Scanning** | High scroll velocity, no dwell | Nothing. Let them scan | Interrupting with a suggestion |
| **Reading** | Low scroll velocity, long section dwell | Ephemeral emphasis on related items, below fold | Moving anything they are reading |
| **Searching** | Query events, reformulation | Vocabulary bridging, suggestion reordering | Changing the page under them |
| **Comparing** | Repeat visits to two sections, copy events | Surface a comparison affordance in a fixed slot | Picking one for them |
| **Confused** | Thrashed cursor, dead clicks, hesitation | Clarify labels, expand the relevant explanation in place | Offering to do it for them |
| **Frustrated** | Rage clicks, U-turns, form churn | Offer a human channel and a status check, dismissible | Cheerful automated help, or a chatbot |
| **Abandoning** | Exit intent, long idle after struggle | Save-progress affordance if legitimate | Exit-intent modal begging them to stay |

The frustrated row is the one that matters most in public service. A citizen rage-clicking a
status page is not a conversion opportunity. The evidence on unsolicited help says the correct
move is a clearly-labelled route to a human, offered once, and dismissible.

---

## Part 6: Extending the POC

Concrete experiments, in dependency order. Each plugs into the existing bench harness
behind the same four contracts (SessionEncoder, CandidateSource, Ranker, DecisionRenderer).

**E1 — Instrument the full frustration signal set.** Extend the sensor to emit the Part 2
definitions with the stated thresholds. Cheap, and it is the input to everything below.

**E2 — Reproduce the frustration classifier.** Tabular features into XGBoost plus a sequence
LSTM, scored on the same corpus. Target: confirm the published finding that 20 to 30
interactions suffice, on our own event taxonomy. Report the accuracy-versus-events curve,
because that curve is the design input for when to allow intervention.

**E3 — Build the state classifier (M3).** Seven-class output per Part 5. Labels bootstrapped
from proxy outcomes: abandonment, support contact, repeated failed search.

**E4 — Implement ephemeral adaptation as the default primitive.** Gradual onset, no spatial
change, `prefers-reduced-motion` respected by falling back to static. This is the highest-value
build item on the list because it makes every downstream accuracy improvement optional rather
than load-bearing.

**E5 — Failure-cost simulation.** Run each Tier A/B/C pattern through the harness at simulated
accuracies from 40% to 95% and measure task completion. Produces the accuracy threshold below
which each pattern is net harmful. This is the experiment that tells you which patterns you are
actually allowed to ship given your real model.

**E6 — Timing model.** The "Goldilocks window" problem. Rather than intervening on confidence
alone, learn *when* an intervention is welcome, using dismissals as negative labels. Dismissal
data is the only clean negative signal available, which is why the dismiss control is a
data-collection instrument as much as a courtesy.

**E7 — Framing A/B.** Same adaptation, two framings: shortcut ("continue where you left off")
versus anticipation ("we know what you need"). Measures the self-threat effect directly on a
government audience. Cheap, and the result likely generalises across the whole programme.

---

## Sources

- [Ephemeral adaptation: gradual onset to improve menu selection performance (CHI 2009)](https://www.cs.ubc.ca/~joanna/papers/CHI2009_Findlater.pdf) and [ACM record](https://dl.acm.org/doi/10.1145/1518701.1518956)
- [A comparison of static, adaptive, and adaptable menus](https://www.researchgate.net/publication/221519087_A_comparison_of_static_adaptive_and_adaptable_menus)
- [Benefits and costs of adaptive user interfaces](http://www.cs.tufts.edu/~jacob/250aui/AdaptiveBenefits_Lavie_IJoHCI10.pdf)
- [User experience with adaptive user interfaces: comparing performance and preferences (2025)](https://www.sciencedirect.com/science/article/pii/S0164121225002675)
- [Principles of Mixed-Initiative User Interfaces, Horvitz (CHI 1999)](https://dl.acm.org/doi/10.1145/302979.303030) and [author's page](http://erichorvitz.com/uiact.htm)
- [How Users Perceive Mixed-Initiative AI (IUI 2026)](https://dl.acm.org/doi/full/10.1145/3742413.3789224)
- [Proactive AI Adoption can be Threatening: When Help Backfires](https://arxiv.org/abs/2509.09309)
- [To Solicit or Not to Solicit? Impact of AI Assistance Delivery Mechanisms on Decision-Making](https://doi.org/10.1080/10447318.2025.2536617)
- [Machine Learning to Predict Digital Frustration from Clickstream Data](https://arxiv.org/abs/2512.20438)
- [FullStory: rage, error, dead clicks and thrashed cursor](https://help.fullstory.com/hc/en-us/articles/360020624154-Rage-Clicks-Error-Clicks-Dead-Clicks-and-Thrashed-Cursor-Frustration-Signals) and [frustrated sessions](https://help.fullstory.com/hc/en-us/articles/360020828013-Frustrated-Sessions)
- [Contentsquare frustration score](https://contentsquare.com/platform/capabilities/frustration-score/) and [scoring methodology](https://support.contentsquare.com/hc/en-us/articles/37271860706193-How-to-use-Frustration-score)
- [Quantum Metric: rage clicks](https://www.quantummetric.com/glossary/rage-clicks) and [frustration / friction score](https://www.quantummetric.com/glossary/frustration-score-friction-score)
