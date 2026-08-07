# Part 2 - Competitive Benchmarking AI Summary

Final written product exercise for the required Competitive Benchmarking AI Summary. The product analyzes public reviews for one focal F&B brand and two competitors over a trailing 90-day window, using no operational data beyond those reviews.

The submission is grounded in the supplied coffee-review exports and designed to ship consistently across F&B categories. No runnable product build is required by the brief.

## Final deliverables

| Artifact | Purpose |
| --- | --- |
| [`outputs/Part_2.md`](outputs/Part_2.md) | Canonical written response to all seven assessment questions |
| [`outputs/part_2.pdf`](outputs/part_2.pdf) | Assessor-facing PDF export |
| [`analysis/part2_pm_claim_feasibility.ipynb`](analysis/part2_pm_claim_feasibility.ipynb) | Executed data audit and feasibility analysis |
| [`analysis/feasibility_analysis.py`](analysis/feasibility_analysis.py) | Deterministic evidence calculations and proxy definitions |

The response must answer all seven assessment questions:

1. Classify and honestly rewrite the six proposed PM claims.
2. Separate shared product behavior from governed category adaptation.
3. Define deterministic computation versus LLM-assisted discovery and narration.
4. Bind every generated claim to exact source reviews.
5. Communicate limits from biased, uneven, and potentially manipulated review data.
6. Draw the line for prescriptive advice from reviews alone.
7. Make regenerate behavior coherent and trustworthy for users.

The report treats the supplied three-brand dataset as evidence for the product design rather than claiming three separately generated client summaries. In production, each generated summary has exactly one focal client brand and treats the other two brands as competitors.

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
├── analysis/   # Reproducible database reconstruction, notebook, and helpers
├── outputs/    # Markdown and PDF submission artifacts
└── tests/      # Deterministic reconstruction and notebook checks
```

The raw review exports and data dictionary remain ignored local inputs under `Files/` and `DATA_DICTIONARY.xlsx`. The executed notebook is tracked, while the reconstructed SQLite database is ignored because it is reproducible from those inputs.

## Reproduce the analysis

Run from this directory with Python 3.11 or newer after placing the supplied inputs in `Files/` and `DATA_DICTIONARY.xlsx`:

```bash
python3 analysis/reconstruct_database.py
python3 analysis/build_pm_feasibility_notebook.py
python3 -m unittest discover -s tests -v
```

The suite performs no model calls. The final verified run completed all eight tests.

## Evidence and product guardrails

The exports contain 15,150 raw review rows from 2026-03-31 through 2026-06-29. One exact duplicate is retained in source lineage but removed from metrics, leaving 15,149 canonical reviews: Lumen 3,665, Solara 6,900, and Vera 4,584. Most text-bearing reviews are Arabic, with a smaller English subset and 5,431 reviews without text. Treat inferred repeat behavior only as a defined language proxy, never as actual customer behavior; reviews cannot prove a competitor fixed a problem or that one intervention caused a rating change.

For consistent regeneration, freeze the dataset snapshot, configuration versions, model version, and approved insight set. Limit variation to the narration layer or cache the reviewed result; a changing verdict is a product-trust issue, not merely sampling noise.

## References

- [Part 2 handoff](../../handoffs/roboost-assessment-part-2-handoff.md)
- [Assessment brief](../../AI_Engineer_Task.docx.pdf)
- [Review Benchmarking vocabulary](../../CONTEXT.md#review-benchmarking)
- Related ADRs: [`0010`](../../adrs/0010-separate-observations-from-action-plans.md), [`0011`](../../adrs/0011-separate-review-evidence-from-business-context.md), [`0012`](../../adrs/0012-use-core-model-playbooks-and-client-context.md)
