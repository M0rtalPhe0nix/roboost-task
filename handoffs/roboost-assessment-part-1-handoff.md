# Handoff: Part 1 - Product Listing Intelligence

## Submission status

Complete. Part 1 answers Case Study 2 as a written product-reasoning deliverable with a
self-contained architecture diagram. No application build is required.

## Canonical artifacts

- [Written report](../parts/part-1-product-listing-intelligence/outputs/part1-report.md)
- [Architecture diagram](../parts/part-1-product-listing-intelligence/outputs/Part1.svg)
- [PDF export](../parts/part-1-product-listing-intelligence/outputs/Part%201%20%E2%80%94%20AI%20Product%20Understanding%20%26%20Problem%20Framing%20%281%29.pdf)
- [Part README](../parts/part-1-product-listing-intelligence/README.md)

## Final decisions

- Use a cost-tiered cascade: deterministic validation and policy rules, compact text and vision
  models, then LLMs only for controlled ambiguity and description generation.
- Treat seller text, photos, and OCR as untrusted input. Only validated, evidence-linked fields may
  drive deterministic publication decisions.
- Auto-reject only confirmed policy violations. Hold ambiguous high-risk listings unpublished for
  review; review-capacity pressure is not evidence of a violation.
- Allocate review throughput initially as 70% prohibited gray-zone and detector disagreement, 20%
  adversarial or suspected-counterfeit cases, 1% representative unknown-category cases, and 9%
  stratified audit. Safety emergencies may preempt the allocation.
- Govern category changes through a bilingual ontology and taxonomy owner. Novel clusters may
  produce proposals but never publish production categories autonomously.
- Keep injection detection monitor-and-flag until bilingual false-positive evidence justifies a
  stronger action.

## References and verification

- [Shared vocabulary](../CONTEXT.md#listing-intelligence)
- [Assessment brief](../AI_Engineer_Task.docx.pdf)
- ADRs [0005](../adrs/0005-hold-ambiguous-high-risk-listings.md) through
  [0009](../adrs/0009-roll-out-injection-detection-in-monitor-mode.md), plus final allocation
  [0018](../adrs/0018-use-final-review-capacity-allocation.md)

The Markdown report is present and the SVG passes XML well-formedness validation. There is no
automated application test suite for this written-design part.
