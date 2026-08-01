# Part 2 - Competitive Benchmarking AI Summary

HTML presentation for the required Competitive Benchmarking AI Summary. The product analyzes public reviews for one focal F&B brand and two competitors over a trailing 90-day window, using no operational data beyond those reviews.

The final deliverable is an HTML presentation in `presentation/`, grounded in the supplied coffee-review exports and designed to ship consistently across F&B categories.

## Deliverable

The response must answer all seven assessment questions:

1. Classify and honestly rewrite the six proposed PM claims.
2. Separate shared product behavior from governed category adaptation.
3. Define deterministic computation versus LLM-assisted discovery and narration.
4. Bind every generated claim to exact source reviews.
5. Communicate limits from biased, uneven, and potentially manipulated review data.
6. Draw the line for prescriptive advice from reviews alone.
7. Make regenerate behavior coherent and trustworthy for users.

Prepare three focal-brand views: Lumen Coffee, Solara Coffee, and Vera Coffee. In each view the other two brands are competitors; do not collapse them into one market-wide verdict.

## Design position already agreed

- Build evidence discovery, not six hard-coded PM claims. Deterministic computation finds trends, gaps, branch outliers, recurring or emerging themes, reviewer overlap, and response coverage.
- The LLM may label or cluster novel language, prioritize validated insight candidates, and narrate. It must not invent metrics or calculate the numbers itself.
- Every narrative claim is backed by an evidence-bound, deterministic insight candidate with definitions, metrics, evidence rules, confidence treatment, and review IDs. Suppress unsupported insights.
- Show an **Observation** before any **Suggested Action Plan**. An observation describes evidence; an action is a testable recommendation, never a promised outcome or causal conclusion.
- In review-only mode, recommendations remain generic and testable. Operational ownership or feasibility requires a versioned client Business Context Profile.
- Use three configuration layers: a Core F&B Model, a governed Category Playbook, and client-specific Business Context. Novel themes never edit production playbooks automatically.

## Workspace layout

```text
part-2-competitive-benchmarking/
├── README.md
├── presentation/ # Canonical HTML presentation and local assets
├── docs/       # Supporting notes and diagrams
├── analysis/   # Reproducible exploration and data notes
└── outputs/    # Review-ready final artifacts
```

The raw review exports remain in the ignored assessment-data directory. If analysis produces derived data, document its source, date range, filters, and reproducibility steps before placing a safe-to-share artifact in `outputs/`.

## Evidence and product guardrails

The known data profile is 15,150 Arabic reviews from 2026-03-31 through 2026-06-29: Lumen has 3,665 reviews across 70 branches, Solara 6,901 across 67, and Vera 4,584 across 20. Treat inferred repeat behavior only as a defined language proxy, never as actual customer behavior; reviews cannot prove a competitor fixed a problem or that one intervention caused a rating change.

For consistent regeneration, freeze the dataset snapshot, configuration versions, model version, and approved insight set. Limit variation to the narration layer or cache the reviewed result; a changing verdict is a product-trust issue, not merely sampling noise.

## References

- [Part 2 handoff](../../handoffs/roboost-assessment-part-2-handoff.md)
- [Assessment brief](../../AI_Engineer_Task.pdf)
- [Review Benchmarking vocabulary](../../CONTEXT.md#review-benchmarking)
- Related ADRs: [`0010`](../../docs/adr/0010-separate-observations-from-action-plans.md), [`0011`](../../docs/adr/0011-separate-review-evidence-from-business-context.md), [`0012`](../../docs/adr/0012-use-core-model-playbooks-and-client-context.md)
