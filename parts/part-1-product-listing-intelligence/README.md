# Part 1 - Product Listing Intelligence

Final response for Part 1, Case Study 2: an Arabic-English marketplace that receives approximately 100,000 product listings each month. Each listing needs a category from a fixed tree, a standardized description, and a prohibited-item decision while human review is limited to 5% of monthly volume.

Part 1 is a product-reasoning deliverable rather than a runnable build. Its canonical submission is the written case-study report together with the architecture diagram.

## Final deliverables

| Artifact | Purpose |
| --- | --- |
| [`outputs/part1-report.md`](outputs/part1-report.md) | Final written response covering the proposed pipeline, all five assessment questions, moderation operations, auditability, metrics, cost controls, limitations, and design rationale |
| [`outputs/Part1.svg`](outputs/Part1.svg) | Self-contained architecture diagram for the listing-intelligence pipeline and taxonomy-adaptation workflow |
| [`outputs/Part 1 — AI Product Understanding & Problem Framing (1).pdf`](outputs/Part%201%20%E2%80%94%20AI%20Product%20Understanding%20%26%20Problem%20Framing%20%281%29.pdf) | Submission-ready PDF export of the written response |

The Markdown report and SVG are the reviewable source artifacts; the PDF is the assessor-facing export.

## What the solution covers

The report proposes a risk-aware multimodal cascade with three distinct outputs and decision paths:

1. Prohibited-item classification optimized for high recall across images, OCR, seller text, and cross-modal inconsistencies.
2. Fixed-tree category assignment using bilingual category representations, category-specific thresholds, and an explicit `UNKNOWN` outcome.
3. Schema-constrained Arabic-English description standardization with factual validation and a deterministic fallback.

The design uses deterministic validation, normalization, and policy rules first; specialized OCR and vision models for image evidence; embeddings and compact classifiers for candidate selection and signal consolidation; and LLMs only for controlled description generation and low-frequency taxonomy proposals.

## Operating assumptions and scale

- Approximately 100,000 listings are processed per month, or about 3,400 per day.
- The fixed category tree contains approximately 500 categories.
- A 5% review limit provides capacity for approximately 5,000 listings per month.
- The final report's initial review allocation is 70% prohibited gray-zone and detector-disagreement cases, 20% adversarial or suspected-counterfeit cases, 1% representative unknown-category cases, and 9% stratified audit of auto-approved listings. This supersedes the earlier 80/15/5 proposal recorded in ADR 0006.
- Exact risk thresholds require calibration on reviewed marketplace data; the report does not claim measured production performance or fixed provider costs.

## Guardrails and governance

- Seller text, images, and OCR are treated as untrusted input and retained in original form for audit.
- Required safety-check failures, contradictory evidence, and medium-risk cases are held for review rather than silently approved.
- A signal consolidator combines independent safety indicators; no single model or registry lookup is treated as conclusive proof of counterfeiting.
- Description generation has no moderation authority, must satisfy a strict schema, and is checked for unsupported facts.
- Unknown and low-confidence listings are deduplicated and clustered. An LLM may draft a candidate category, but a taxonomy owner must approve every production change.
- Appeals, reviewer overrides, model and rule versions, thresholds, evidence, latency, and estimated processing cost are retained for audit and calibration.

## Workspace layout

```text
part-1-product-listing-intelligence/
├── README.md
└── outputs/
    ├── Part 1 — AI Product Understanding & Problem Framing (1).pdf
    ├── Part1.svg
    └── part1-report.md
```

There is no Part 1 application, source module, or automated test suite because the selected assessment deliverable is a written design. Validation is limited to Markdown-link checks and confirming that the SVG is well-formed.

## References

- [Part 1 handoff](../../handoffs/roboost-assessment-part-1-handoff.md)
- [Assessment brief](../../AI_Engineer_Task.docx.pdf)
- [Listing Intelligence vocabulary](../../CONTEXT.md#listing-intelligence)
- Decision history: [`0005`](../../adrs/0005-hold-ambiguous-high-risk-listings.md), [`0006`](../../adrs/0006-prioritize-review-by-expected-harm.md), [`0007`](../../adrs/0007-govern-category-ontology-changes.md), [`0008`](../../adrs/0008-use-a-cost-tiered-listing-cascade.md), [`0009`](../../adrs/0009-roll-out-injection-detection-in-monitor-mode.md), and final allocation [`0018`](../../adrs/0018-use-final-review-capacity-allocation.md)
