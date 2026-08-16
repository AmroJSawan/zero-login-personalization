# Copy and Presentation Spec: Adaptive Booking Demo

## 1. Voice rules

1. One idea per string; hard ceiling 25 words per sentence, aim near 14 (GDS 25-word limit; API data: 90%+ comprehension at 14 words, <10% at 43 — insidegovuk.blog.gov.uk/2014/08/04, wyliecomm.com/how-long-should-a-sentence-be).
2. Cut word count roughly in half and write objectively, never promotionally; concise + objective copy measured 58% to 124% better usability (Morkes & Nielsen, nngroup.com/articles/concise-scannable-and-objective-how-to-write-for-the-web).
3. Never mention the cursor, hesitation, dwell, or any inferred signal on the booking surface; inferred-signal disclosure is the most-rejected framing, roughly a 27% effectiveness drop versus silence (Kim, Barasz & John, JCR 2019, academic.oup.com/jcr/article/45/5/906/4985191; Leiva et al., CHIIR 2021, dl.acm.org/doi/10.1145/3406522.3446011).
4. Frame every adaptive insight as a fact about the fare or the market, never about the user's behavior (Google Flights price-insight grammar, blog.google/products/travel/google-flights-find-deals).
5. State what happens; never deny a threat you introduced ("no spam" style copy swung signups from -18.7% to +19.5% on wording alone; Aagaard/ContentVerve).
6. Each reassurance appears exactly once, inline, at its single moment of relevance, in under 8 words where possible (Baymard, baymard.com/blog/explain-phone-number-field; repeated canned assurance is a catalogued AI tell, en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
7. Casual but unfunny in all money-adjacent copy; playful tone measurably lowers trust where money is at stake, and trust explains 52% of desirability (NN/G, nngroup.com/articles/tone-voice-users); keep a straight face when unsure (styleguide.mailchimp.com/voice-and-tone).
8. Ban negative parallelism ("X, not Y"), rule-of-three triads, and spaced-dash asides; all are catalogued machine-authorship tells that carry a measured trust penalty (WP:AISIGNS; washingtonpost.com/technology/interactive/2025/how-detect-chatgpt-em-dash; arxiv.org/abs/2510.24011).
9. The payment step is personalization-silent: show a persistent itemized total instead of asserting honesty; triggered personalization at the purchase transition makes regret 3.2x more likely (Gartner 2025, gartner.com/en/newsroom/press-releases/2025-06-03; Baymard cost-visibility data, baymard.com/lists/cart-abandonment-rate).
10. Labels are verb-first, grade 7, never cute or clever; system text names the state, not the vibe (Apple HIG Writing, developer.apple.com/design/human-interface-guidelines/writing; Shopify content guidelines, shopify.dev/docs/apps/design/content).

## 2. Before / after table

| # | Surface | Before (verbatim) | After |
|---|---------|-------------------|-------|
| 1 | Page intro | "Nothing to type here on purpose. The page reads only your cursor - where it gravitates, what it returns to, where it hesitates - and adjusts in steps small enough to miss." | "This is a demo booking flow. It adapts as you browse. Open the log to see each change." |
| 2 | Comparison hint | "You seem to be weighing 09:10 Light against 14:20 Light - EUR14 apart · same conditions - the cheaper one wins." | "Same fare conditions. The 09:10 is EUR 14 less." |
| 3 | Extras offer | "The bag, without the bundle / You weighed 09:10 Flex - most of that EUR41 jump is the checked bag. Just the bag is EUR38." | Heading: "Checked bag". Body: "23 kg checked bag, EUR 38. Flex includes it, with free changes and seat choice, for EUR 41 more." |
| 4a | Extras alt (Flex) | "Nothing to sell you / Bag, free changes and seat choice are already inside your Flex fare." | Heading: "Included in Flex". Body: "Your fare includes a checked bag, free changes and seat selection." |
| 4b | Extras alt (light) | "Travelling light, confirmed / You never looked at bags, so we are not asking twice." | Delete the card. If the section must render, show a neutral utility line: "Add bags or seats any time before check-in." The adaptation (suppressed upsell) is recorded in the log drawer, not narrated on the surface. |
| 5 | Form note | "Goes nowhere - this page has no network." | "Demo only. Nothing you enter is sent or saved." |
| 6 | Email helper | "Only the ticket goes here. No newsletter, no account, nothing else." | "Used once, to send your ticket." |
| 7 | Payment intro | "The total below is the total. Nothing was added along the way without you." | Delete the sentence. Replace with a persistent itemized summary ending: "Total EUR 214, including all taxes and fees." |
| 8 | Idle reassurance | "Taking your time is fine. The total is final, and cancellation is free for 24 hours." | Static line near the total, always visible, never triggered: "Free cancellation for 24 hours." |
| 9a | Status pill (idle) | "reading the room - quietly" | "Idle" |
| 9b | Status pill (active) | "the page is adapting - see how" | "Adapting · View log" |
| 10a | Log entry | "watching, not judging" | "14:02:03 tracking started. Cursor position only, in-page." |
| 10b | Log entry | "reassured, not pressured" | "14:05:41 idle 12s on payment. No action taken (payment step is static)." |
| 10c | Log entry | "peak-end on purpose" | "14:07:19 confirmation rendered. Order summary pinned to top." |
| 11 | Footer | Three-sentence privacy lecture | "Demo. No data leaves this page." One line, nothing more. The privacy claim already lives at the email field (row 6); do not repeat it. |

Notes on the table: no em dashes appear in any after string. Every second-person behavior narration ("you seem", "you weighed", "you never looked") is gone; those constructions are the same grammar EU regulators forced Booking.com to remove (ec.europa.eu/commission/presscorner/detail/en/ip_19_6812) and the most-rejected disclosure type in Kim et al.

## 3. Presentation rules for adaptive elements

**Comparison hint**
- Placement: inline badge or single line attached to the fare card it describes, exactly where Google Flights places price insights. Never a toast, never floating.
- Length: one clause, 8 words or fewer, key fact first ("EUR 14 less").
- Tone: a fact about the fares. No second person, no verdict ("wins"), no recommendation verb. The user draws the conclusion.
- Frequency: at most one behavior-informed hint per screen; repetition flips trust to surveillance (Feng et al., ICWSM 2026, arxiv.org/abs/2501.12152).

**Targeted offer**
- Placement: a normal card in the extras grid, visually identical to non-targeted cards. Targeting shows in ordering and content, never in styling or callouts (Airbnb pattern: full personalization, zero narration; dl.acm.org/doi/10.1145/3219819.3219885).
- Length: heading 3 to 6 words naming the item (Netflix label grammar, newamerica.org/oti/reports/why-am-i-seeing-this/case-study-netflix); body one sentence with concrete specs (weight, price).
- Tone: item-anchored. The offer describes the bag, not the browsing that surfaced it. Silence about the mechanism is load-bearing, not evasive.
- The suppressed-upsell case renders as absence, not as an announcement of absence.

**Idle reassurance**
- Do not trigger anything on idle at the payment step. Reactive messages at the purchase transition are the measured worst case: 3.2x regret, 2.8x time pressure, 44% lower repurchase (Gartner 2025).
- The reassurance content (free 24-hour cancellation) becomes static page furniture next to the total, present from first paint. Never acknowledge that the user paused.
- Length: one clause. Tone: policy fact, no empathy performance ("taking your time is fine" is deleted).
- The idle detection itself may still fire; it logs to the drawer ("idle 12s, no action taken") instead of touching the surface.

## 4. Delete outright (do not rewrite)

- The footer privacy lecture. At 20 to 28% words read, it is unread page weight (nngroup.com/articles/how-little-do-users-read). One line survives (row 11).
- The payment intro sentence. Showing the itemized total is the fix; prose vouching for it is not (Baymard).
- The "Travelling light, confirmed" card. It discloses a negative passive observation ("you never looked"), the most-rejected disclosure class. The adaptation is the absence of the upsell.
- The idle-triggered message as a mechanism on the booking surface.
- All cursor narration in the intro ("where it gravitates, what it returns to, where it hesitates").
- "The cheaper one wins" and every other verdict clause; steering-by-narration is catalogued pressure copy (Mathur et al., dl.acm.org/doi/10.1145/3359183).
- Every instance of "on purpose", "quietly", "not judging", "not pressured": self-narrated modesty is the promotional register that cost 27 to 58% in measured usability and is an AI tell.
- Emoji, title case, and bold anywhere except one price figure per view (WP:AISIGNS).

## 5. Meta/demo layer rules (status pill and log drawer)

The demo layer is the one sanctioned place to name the mechanism, because the user opens it voluntarily (the Spotify/Netflix pattern: signal inventory lives one click away, never on the surface).

**Status pill**
- Vocabulary: state labels of 1 to 3 words. "Idle", "Adapting", "Paused". Plus one affordance: "View log".
- Verb-first, present tense, no adverbs, no personality. "Adapting to your cursor" is the maximum permissible specificity (Apple HIG: never cute or clever in labels).
- The pill never editorializes about intent, ethics, or restraint.

**Log drawer entries**
- Fixed format per entry: `timestamp · signal observed · threshold or count · action taken`.
- Example: "14:02:11 cursor returned to 09:10 fare, 3rd visit. Showed fare comparison line."
- Past tense, factual, complete. Name the exact signal ("cursor dwell 4.2s on Flex column"), the exact rule that fired, and the exact UI change. Precision replaces charm.
- Banned in log copy: adjectives, adverbs, jokes, negative parallelism, any word from the excess-vocabulary list (delve, seamless, meticulous, elevate; science.org/doi/10.1126/sciadv.adt3813), and any self-assessment ("gently", "quietly", "on purpose", "not judging").
- One entry per adaptation, including null actions ("no action taken"), which demonstrate restraint through the record rather than through prose.
- A single static header line may state scope: "This log lists every signal read and every change made. Data stays in-page." Nothing else in the drawer explains philosophy; the entries are the argument.