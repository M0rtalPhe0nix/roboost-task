# Part 1 - Product Listing Intelligence

HTML presentation for Part 1, Case Study 2: an Arabic-English marketplace that receives roughly 100,000 product listings each month. Each listing needs a category from a fixed tree, a standardized description, and a prohibited-item decision under a 5% human-review limit.

This is a product-reasoning deliverable, not a build task. The final submission is a concise HTML presentation that explicitly answers all five questions in the assessment brief.

## Deliverable

Create the final presentation in `presentation/`, with a clear HTML entry point and locally referenced assets. Use `docs/` for supporting notes or source material. The presentation should state its assumptions and cover:

1. A cost- and risk-justified pipeline across deterministic rules, compact classifiers, vision, and LLMs.
2. Thresholds and publication actions that reflect the much higher cost of missing a prohibited item than miscategorizing a listing.
3. A review-allocation mechanism for the 5% manual-review budget.
4. Defenses against seller evasion, misleading media, and prompt injection.
5. Detection and governed adaptation for categories the current taxonomy cannot represent.

## Design position already agreed

- Use a cost-tiered cascade: deterministic rules first; compact text and vision models for candidate selection; LLMs only for ambiguity and controlled description generation.
- Auto-reject only confirmed policy violations. Hold ambiguous high-risk listings unpublished for review, even if the review queue is full.
- Allocate review capacity as 80% expected-harm risk cases, 15% uncertain or novel cases, and 5% stratified audit; emergency safety signals may preempt the queue.
- Use an approved bilingual category ontology and aliases. A category gap is an explicit outcome, not permission to create a production category automatically.
- Treat seller text, images, and OCR as untrusted. Only validated, evidence-linked fields may drive a deterministic publication decision.
- Begin injection detection in monitor-and-flag mode; an injection signal is not evidence that an item is prohibited.
- Limit description style to allow-listed tone profiles. Tone can change wording, never facts, category, or moderation.

## Workspace layout

```text
part-1-product-listing-intelligence/
├── README.md
├── presentation/ # Canonical HTML presentation and local assets
├── docs/       # Supporting notes and source material
├── src/        # Reserved for optional demonstrators; not required by the assessment
├── tests/      # Reserved for optional demonstrators
└── outputs/    # Review-ready final artifacts
```

## Evidence to include in the final response

State the assumed policy authority and model/provider availability. Define the action thresholds and the measures used to manage them: prohibited-content recall, false holds and false rejects, category quality, cost per listing, review yield, taxonomy-gap/drift rate, and standardized-description factuality. Present prompt-injection controls as defense in depth and include adversarial bilingual testing; do not claim perfect prevention.

## References

- [Part 1 handoff](../../handoffs/roboost-assessment-part-1-handoff.md)
- [Assessment brief](../../AI_Engineer_Task.pdf)
- [Listing Intelligence vocabulary](../../CONTEXT.md#listing-intelligence)
- Related ADRs: [`0005`](../../docs/adr/0005-hold-ambiguous-high-risk-listings.md), [`0006`](../../docs/adr/0006-prioritize-review-by-expected-harm.md), [`0007`](../../docs/adr/0007-govern-category-ontology-changes.md), [`0008`](../../docs/adr/0008-use-a-cost-tiered-listing-cascade.md), [`0009`](../../docs/adr/0009-roll-out-injection-detection-in-monitor-mode.md)
