# Part 2 — Product Thinking: Competitive Benchmarking AI Summary

## Executive summary

The proposed feature should be an **evidence-bound market intelligence system**, not an autonomous strategist. It can be bold about which observed issue deserves attention, but it must remain conservative about facts, causality, customer motives, and the likely effect of an intervention.

My design separates the feature into four responsibilities:

1. A multilingual semantic layer extracts review-level aspects, sentiment, repeated-visit language, product references, and explicit mentions of operational changes.
2. Deterministic code owns deduplication, joins, dates, denominators, rates, statistical intervals, reviewer overlap, trend calculations, eligibility rules, and ranking.
3. An evidence registry binds every publishable claim to its metrics, definitions, date range, branch coverage, and supporting review IDs.
4. An LLM narrates only pre-approved claim objects. It cannot invent a number, infer a cause, or introduce a recommendation that was not supplied by the deterministic insight engine.

The attached analysis reconstructed the supplied exports into a constrained SQLite database and tested the six mocked PM claims. The result is deliberately conservative: **none of the six claims is safe to publish exactly as written**. Some components are directly computable, some require validated text mining, some permit only hedged association, and some exceed what public review data can support.

The resulting product can still feel like a strategist’s brief. Its strongest responsible form is:

> **A decisive, evidence-linked prioritization of what the review market is signaling, followed by bounded actions to investigate or test—not unsupported claims about why customers behave as they do or what will certainly fix the business.**

---

## 1. Scope, assumptions, and dataset audit

### 1.1 Assumptions

For this exercise:

- The product design itself is brand-agnostic.
- Branch metadata is used for attribution and coverage. Menu data, popular-times data, and other non-review attributes are not used to prove the review-market claims because the product brief restricts conclusions to public review data.
- A public review is an observation from a self-selected reviewer. It is not equivalent to a transaction, a representative customer survey, or an operational measurement.
- The supplied dataset contains one trailing 90-day window, so quarter-over-quarter claims cannot be reproduced. For feasibility testing only, I divide the window into two equal 45-day periods.
- Raw aspect counts should never be compared across brands without showing review volume or normalized rates.
- Star-only reviews cannot support claims about taste, service, wait time, packaging, or motives.

### 1.2 Initial Data Exploration

The supplied files maps to canonical brands, branches, reviewers, reviews, detailed ratings, review context, and source-lineage tables.

| Brand | Unique reviews | Unique reviewers | Reviewed branches | Text-bearing reviews | Mean stars |
|---|---:|---:|---:|---:|---:|
| Lumen Coffee | 3,665 | 3,614 | 70 | 2,511 | 4.32 |
| Solara Coffee | 6,900 | 6,524 | 67 | 3,898 | 4.29 |
| Vera Coffee | 4,584 | 4,538 | 20 | 3,309 | 4.29 |
| **Total** | **15,149** | — | **157** | **9,718** | — |

The raw review exports contained 15,150 rows, of which one was an exact duplicate. The duplicate remains in source lineage but contributes only once to metrics. There were no orphan review-to-branch joins,

The date range is **March 31, 2026 to June 29, 2026**, 90 days.

### 1.3 Data-quality consequences

There are 5,431 reviews without text. Therefore:

- Overall star calculations can use all canonical reviews.
- Aspect prevalence must use text-bearing reviews .

Language handling also requires care. Most textual reviews are Arabic, a smaller set is English, and many star-only reviews have no usable original-language value. A production extractor must handle Arabic dialects, Arabizi, English, Franco code-switching, spelling variation, and null text explicitly.

---

## 2. Question 1 — Feasibility of the six mocked claims

### Classification framework

I use the assessment’s four requested classes as follows:

- **Directly computable:** exact aggregation of supplied structured fields.
- **Minable with careful definitions:** requires semantic extraction from text using a declared, evaluated definition.
- **Inference that must be hedged:** the data supports an association or proxy, but not the behavioral or causal conclusion (Correlation is not Causation).
- **Judgment beyond what the data supports:** a necessary causal, operational, financial, or strategic premise is absent.

Compound claims are split when their components have different evidence status.

### Summary matrix

| PM claim | Classification | Verdict | Strongest honest version |
|---|---|---|---|
| **(a)** “Wait-time complaints doubled this quarter, from 37 to 75.” | Minable with careful definitions | A wait complaint is not a supplied field. | “Between two predeclared periods, reviews matching the validated wait-time-complaint definition changed from X of N text reviews to Y of M, with the normalized rate and evidence IDs shown.” |
| **(b)** “61 customers reviewed both you and Competitor A. They rate your taste 4.4 versus their 4.0.” | Split: overlap directly computable; taste minable | Reviewer overlap is exact. Taste is not a supplied metric. | “X public reviewers reviewed both brands. Their customer-balanced overall ratings were A and B. Among the Y reviewers whose taste preference could be determined, P% preferred Brand A and Q% preferred Brand B.” |
| **(c)** “Your regulars are going quiet. Repeat-customer language is down 38%.” | Inference requiring hedging | Repeat-visit language is observable; actual regular status and silence are not. | “The share of text reviews containing the defined repeat-visit-language proxy changed by X%.” |
| **(d)** “Competitor A already fixed its wait-time problem. Their reviews show it worked and that they gained 0.4★.” | Inference requiring hedging | Reviews can show parallel trends, not the intervention or its causal effect. | “Wait-related review mentions and mean review stars moved in opposite directions over the defined periods.” |
| **(e)** “Competitor A’s loyalty program is why customers forgive their mistakes.” | Judgment beyond support | Enrollment, redemption, exposure, mistakes, forgiveness, and motive are absent. | “Loyalty-program terms appeared in X reviews and co-occurred with low ratings in Y. This does not establish forgiveness or explain why customers rated the brand as they did.” |
| **(f)** “First move: fix your delivery packaging. It addresses your fastest-growing complaint and protects your product lead.” | Judgment beyond support | Theme growth can be measured, but priority and effect require business context. | “Packaging is an eligible rising complaint signal. Validate it by branch, channel, product, impact, and controllability before assigning intervention priority." |


## 3. Question 2 — One design across coffee, burgers, shawarma, and future categories

The feature should use a **shared core ontology with adaptive category-specific leaves**. The F&B domain provides a shared semantic core, while each category requires its own terminology and lower-level aspect definitions.”

### 3.1 Shared components

The following concepts are stable across most F&B categories:

- Product quality
- Taste and seasoning
- Temperature and freshness
- Order accuracy
- Availability
- Service speed
- Staff behavior
- Cleanliness
- Atmosphere
- Value
- Delivery
- Packaging
- Digital ordering
- Drive-through or pickup experience

The shared platform can also reuse:

- Review ingestion and deduplication.
- Arabic-English normalization.
- Aspect-span extraction.
- Sentiment and intensity extraction.
- Reviewer-overlap computation.
- Branch, city, channel, and time segmentation.
- Trend and uncertainty calculations.
- Evidence binding.
- Confidence rules.
- Narrative templates and recommendation guardrails.

### 3.2 Category-adaptive components

The leaf taxonomy should adapt to the language observed in each market:

- **Coffee:** extraction, bean origin, milk alternatives, matcha, drive-through speed.
- **Burgers:** patty doneness, bun quality, fries, portion size, sauce balance.
- **Shawarma:** bread, meat dryness, filling ratio, garlic sauce, wrapping and leakage.
- **Bakery:** freshness, filling, texture, availability, display condition.

The model may discover candidate topics using multilingual embeddings, clustering, or structured LLM extraction. However, discovered labels should enter an **emerging-topic queue** rather than being immediately promoted to official metrics.

A new topic becomes publishable only when it passes:

1. Semantic coherence review.
2. Sufficient support across reviews or branches.
3. Precision testing on a labeled sample.
4. Mapping to a stable parent concept.
5. Versioned approval so historical comparisons remain interpretable.

### 3.3 Defining a competitor “move”

Review data rarely observes an internal business decision directly. A competitor move should therefore be limited to one of these evidence classes:

- **Explicit observed change:** multiple reviewers independently state that a process, product, price, layout, or policy changed.
- **New market signal:** a new product or service term appears abruptly and persists across branches.
- **External fact from an approved additional source:** only if the product scope later expands beyond reviews.

The summary may say “reviewers began mentioning a changed drive-through process.” It should not say “the competitor redesigned operations” unless the change is independently verified.

### 3.4 What counts as a good rating

A fixed threshold such as 4.2 is not portable across categories, cities, or review cultures. “Good” should be relative to:

- Peer distribution in the same market and period.
- The brand’s own recent baseline.
- Review volume and uncertainty.
- Branch mix.
- The proportion of star-only versus text reviews.

This allows the system to adapt without a category-specific rebuild. The software remains stable; the observed market distribution and validated taxonomy determine interpretation.

---

## 4. Question 3 — Deterministic computation versus LLM responsibilities

### 4.1 Deterministic responsibilities

Code or SQL should own anything that has one correct answer:

| Responsibility | Why deterministic |
|---|---|
| Deduplication and source lineage | Must be reproducible and auditable. |
| Date windows and comparison periods | Boundary errors materially change claims. |
| Counts, rates, shares, averages, and deltas | LLM arithmetic is unnecessary and unsafe. |
| Reviewer overlap | Exact set intersection over stable IDs. |
| Customer-balanced metrics | Weighting rules must be explicit. |
| Branch and city coverage | Structured aggregation. |
| Confidence intervals | Formal calculation. |
| Eligibility thresholds | Product contract, not prose judgment. |
| Candidate ranking | Must remain stable across regeneration. |
| Evidence IDs | Direct query output. |

### 4.2 LLM or semantic-model responsibilities

A multilingual language model is valuable where the meaning is not already structured:

- Extracting the exact evidence span.
- Distinguishing complaint, praise, neutral mention, and sarcasm.
- Resolving product and service synonyms.
- Recognizing explicit repeated-visit language.
- Identifying statements that reviewers describe as changes.
- Discovering candidate emerging themes.
- Producing clear executive prose from approved facts.

The extractor should return structured data, for example:

```json
{
  "review_id": "rev_990e8de1",
  "aspects": [
    {
      "aspect": "drive_through_speed",
      "sentiment": "negative",
      "evidence_span": "اصبح الزحام مزعج ووقت الانتظار طويل"
    }
  ],
  "explicit_change": {
    "type": "drive_through_process_change",
    "mentioned": true,
    "evidence_span": "الغاء شباك الطلب ... وتحول لشباك دفع واستلام"
  }
}
```

### 4.3 What goes wrong if the LLM produces the numbers

Allowing the LLM to calculate metrics introduces:

- Denominator inconsistency.
- Silent omission of star-only reviews.
- Incorrect date boundaries.
- Double counting duplicate or multi-aspect reviews.
- Reviewer weighting errors.
- Arithmetic hallucinations.
- Non-reproducible outputs.
- Numbers that cannot be traced to exact review IDs.

Its role is **narration**, not analysis-by-improvisation.

---

## 5. Question 4 — Binding every sentence to evidence

### 5.1 Claim object

Every publishable factual sentence should originate from a versioned claim object:

```json
{
  "claim_id": "CLM-WAIT-LUMEN-2026H2",
  "claim_type": "aspect_trend",
  "subject_brand": "Lumen Coffee",
  "metric_definition": "1-3 star text review matching validated wait-time taxonomy v1.3",
  "periods": {
    "early": {
      "start": "2026-03-31T16:32:14Z",
      "end": "2026-05-15T16:20:13Z",
      "matches": 23,
      "text_reviews": 1170,
      "rate_per_1000": 19.66
    },
    "recent": {
      "start": "2026-05-15T16:20:13Z",
      "end": "2026-06-29T16:08:12Z",
      "matches": 51,
      "text_reviews": 1341,
      "rate_per_1000": 38.03
    }
  },
  "relative_change_percent": 93.46,
  "evidence_review_ids": ["rev_aa58e69d", "rev_4f02c45f"],
  "confidence": "medium",
  "method_version": "aspect-taxonomy-v1.3",
  "allowed_language": "Wait-related complaint signals nearly doubled within the snapshot."
}
```

### 5.2 Generation constraints

The generator receives only approved claim objects and must follow these rules:

- Every factual sentence cites at least one `claim_id` internally.
- Every number must match a supplied metric exactly.
- The model may not introduce a cause, motive, intervention, or projected outcome unless supplied as a separately validated fact.
- Comparative language is allowed only when both brands use compatible definitions and periods.
- The summary must state denominators when volume materially affects interpretation.
- A recommendation must link to the observations that triggered it and show its validation step.

A post-generation validator should reject the response when:

- A number does not appear in an input claim.
- A brand, date, aspect, or direction is unsupported.
- Causal verbs such as “caused,” “fixed,” or “drove” appear without causal evidence.
- A sentence has no evidence binding.
- The wording exceeds the claim’s allowed certainty.


### 5.3 Unsupported insights

An interesting insight that cannot be bound to evidence must not enter the executive summary. It may be placed in a separate **Hypotheses to investigate** area, clearly labeled as unverified and excluded from the verdict and ranking.

---

## 6. Question 5 — Bias, uneven volume, and confidence communication

Public reviews are a biased, uneven observational sample:

- Reviewers self-select.
- Very satisfied and dissatisfied customers may post more often.
- Review volume varies significantly by brand and branch.
- Star-only reviews contribute no textual evidence.
- Review solicitation and platform behavior may differ by brand.
- Fake, coordinated, or duplicated reviews may exist.
- Public reviewer identity does not equal a verified customer identity.
- Branch mix can confound brand comparisons.

### 6.1 Product claim limits

The product may describe **the observed public review signal**. It should not claim:

- Market share.
- Population-level customer satisfaction.
- Purchase frequency.
- True churn or loyalty.
- Operational root cause.
- Intervention effectiveness.
- Customer motive.
- That a suspicious review is fake without an external verification process.

### 6.2 Normalization

At minimum, aspect trends should show:

- Raw matching review count.
- Duplicate source records must be deduplicated before aggregation.
- Number of text-bearing reviews.
- Rate per 1,000 text reviews.
- Absolute and relative change.
- Number of branches represented.
- The share contributed by the largest branch.

A brand with ten times more reviews should not appear ten times worse merely because it generated more text.

### 6.3 Confidence model

Confidence should be multidimensional rather than a single opaque probability:

| Dimension | Example checks |
|---|---|
| Evidence volume | Minimum matches in each period. |
| Extraction quality | Precision/recall on a labeled multilingual set. |
| Breadth | Number of branches, cities, weeks, and reviewers represented. |
| Stability | Signal persists across adjacent windows or resampling. |
| Effect size | Change is material after normalization. |
| Concentration risk | Not driven by one branch, reviewer, or burst. |
| Data completeness | Adequate text coverage and language handling. |

The executive UI can compress this into a label such as:

> **Medium confidence · 51 relevant reviews · 14 branches · sustained for 4 weeks**

Detailed caveats should remain one click away. The main summary should be honest without becoming unreadable.

### 6.4 Suspicious-review handling

The system may detect suspicious patterns—duplicate wording, bursts, extreme reviewer behavior, or unusual branch concentration—but should treat them as a robustness factor:

- Show the metric with and without suspicious clusters.
- Lower confidence if the conclusion changes materially.
- Avoid declaring individual reviews fraudulent without verification.
- Preserve all exclusions and thresholds in the audit trail.

---

## 7. Question 6 — Responsible direct orders from review data

The PM wants “direct orders, not suggestions.” The responsible compromise is to make the language decisive about **the next evidence-seeking or reversible action**, not falsely certain about an expensive business decision.

### 7.1 Actions the system may issue directly

These actions are bounded, reversible, and connected to observed evidence:

- “Audit the five branches generating most of the packaging complaints.”
- “Review the morning drive-through process at the affected branch this week.”
- “Sample 50 cited reviews and validate the product-quality taxonomy before escalation.”
- “Run a two-week packaging test on the highest-volume affected product.”
- “Check whether staffing or process changes align with the review-signal start date.”

### 7.2 Actions that require business context

The system should not independently command:

- Replace a supplier.
- Change staffing levels permanently.
- Launch a loyalty program.
- Remove a product.
- Change price.
- Redesign a branch.
- Claim a financial return.

Those decisions need transaction volume, margin, operational feasibility, ownership, cost, customer research, and controlled measurement.

The feature remains bold by saying **what to investigate first**, while staying defensible about what the reviews cannot prove.

---

## 8. Question 7 — Regeneration consistency

A different verdict after clicking “regenerate” is a product failure because the user believes the system is re-expressing the same evidence, not conducting a new analysis with a different hidden policy.

### 8.1 Required controls

Each summary should freeze:

- Source-file hashes and ingestion timestamp.
- Canonical dataset snapshot ID.
- Date window.
- Deduplication version.
- Taxonomy and extractor version.
- Eligibility and confidence thresholds.
- Candidate claim set.
- Ranking policy.
- Prompt and model version.

The deterministic layer should produce an ordered list of approved claims and plays before narration. Low-temperature generation may vary wording, but not the facts, verdict, ranking, or recommended first action.

For high-stakes executive summaries, the reviewed output may simply be cached. Any changed verdict should include a visible diff explaining which data, threshold, taxonomy, or business input caused the change.

---

## 9. Proposed product architecture

```text
Public review exports
        │
        ▼
Schema validation, deduplication, lineage, language detection
        │
        ▼
Multilingual review-level extraction
(aspects, sentiment, evidence spans, explicit change language)
        │
        ▼
Deterministic metrics and cohort engine
(counts, rates, overlap, trends, intervals, branch coverage)
        │
        ▼
Candidate insight eligibility and stable ranking
        │
        ▼
Evidence registry / claim objects
        │
        ▼
Constrained LLM narration
        │
        ▼
Post-generation factual and certainty validator
        │
        ▼
AI Summary tab with claim-level click-through
```

### 9.1 Product output structure

The AI Summary tab should contain:

1. **Market verdict** — one stable sentence summarizing the strongest supported position.
2. **Your position** — strengths, weaknesses, and current trend.
3. **Competitor profiles** — evidence-based comparative observations.
4. **Early signals** — new or accelerating topics that pass eligibility rules.
5. **Recommended plays** — ordered validation actions, not ungrounded promises.
6. **Confidence and coverage** — compact badges with detailed methodology on click.
7. **Evidence drawer** — exact reviews and metrics behind every claim.

---

## 10. Worked evidence example: Solara Glenmoor drive-through

The supplied reviews contain a useful example of the distinction between observation, inference, and unsupported causality.

Several reviews from the Glenmoor branch explicitly describe a change to the drive-through ordering process and a worse waiting experience:

- `rev_990e8de1` describes moving order taking and payment closer to the pickup window, followed by longer queues and a slower experience.
- `rev_2470030b` says the branch was previously strong but deteriorated after drive-through changes.
- `rev_5d437e10` contrasts an alleged new 15-minute wait with a previous wait of at most five minutes.
- `rev_43c8ff1d` calls the changed drive-through process slow and describes queue-ordering problems.
- `rev_1de0836b` self-identifies as a frequent customer and says the changed process now causes them to avoid the branch.

From those reviews, the product may state:

> **Supported observation:** Multiple Glenmoor reviewers independently describe a changed drive-through process and longer waits during the same period.

It may state, with explicit uncertainty:

> **Hedged inference:** The timing and repeated descriptions suggest the process change may be contributing to the branch’s negative wait-time signal.

It may not state:

> **Unsupported:** The drive-through redesign caused the branch’s performance decline.

The appropriate direct action is:

> **Audit the Glenmoor drive-through process and compare operational wait measurements before and after the reported change. Test whether restoring separate order/payment and pickup steps reduces measured wait time.**

This is decisive, useful, and traceable without converting public-review association into causal certainty.

---

## Conclusion

The review dataset can support a valuable flagship AI Summary, but only when the system makes a strict distinction between **calculation, semantic mining, inference, and strategic judgment**.

The correct product is not “an LLM reads all reviews and writes a strategy.” It is a governed pipeline in which:

- Semantic models structure unstructured multilingual text.
- Deterministic code produces every metric.
- Eligibility and ranking rules stabilize the verdict.
- Every sentence is bound to evidence.
- Unsupported causal and behavioral claims are suppressed.
- Recommended plays begin with testable, reversible actions.

This design can ship unchanged across F&B categories because its core evidence contract remains stable while the category-specific taxonomy adapts through a controlled discovery and validation process.

The product can therefore remain bold and useful without being wrong:

> **Be decisive about the next investigation. Be precise about what the reviews show. Be explicit about what they cannot prove.**

---

## Appendix A — Feasibility proxy definitions used in the notebook

| Proxy | Feasibility definition |
|---|---|
| Wait-time complaint | 1–3 star text review containing a declared Arabic or English wait, delay, queue, or crowding term. |
| Packaging complaint | 1–3 star text review containing a packaging, cup, lid, leak, spill, container, or bag term. |
| Delivery complaint | 1–3 star text review containing a delivery, driver, or pickup term. |
| Product-quality complaint | 1–3 star text review containing a taste, drink, coffee, dessert, freshness, or temperature term. |
| Service complaint | 1–3 star text review containing a service, staff, employee, cashier, or attitude term. |
| Value complaint | 1–3 star text review containing a price, value, expensive, offer, or discount term. |
| Cleanliness complaint | 1–3 star text review containing a cleanliness, dirty, restroom, or hygiene term. |
| Repeat-visit language | Text containing a declared prior-visit or repeated-visit phrase; not a customer-status label. |
| Loyalty-program mention | Text containing a loyalty, points, rewards, or membership term. |

These rules are useful for transparent feasibility testing because a reviewer can inspect them. They should not be mistaken for production semantic performance.

## Appendix B — Submission artifacts

- [`part2_pm_claim_feasibility.ipynb`](../analysis/part2_pm_claim_feasibility.ipynb): executed analysis, data-quality checks, feasibility calculations, and claim-level verdicts.
- [`feasibility_analysis.py`](../analysis/feasibility_analysis.py): deterministic theme matching, overlap analysis, confidence intervals, period comparisons, and formatting helpers.
- `AI_Engineer_Task.docx.pdf`: assessment brief.
- `DATA_DICTIONARY.xlsx`: supplied schema dictionary.
- Brand review and branch JSON exports: source data used by the notebook.
