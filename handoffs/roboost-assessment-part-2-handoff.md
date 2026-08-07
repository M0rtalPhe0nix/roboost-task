# Handoff: Part 2 - Competitive Benchmarking AI Summary

## Submission status

Complete. Part 2 is a written product exercise supported by reproducible deterministic analysis;
the brief does not require a runnable product build.

## Canonical artifacts

- [Written report](../parts/part-2-competitive-benchmarking/outputs/Part_2.md)
- [PDF export](../parts/part-2-competitive-benchmarking/outputs/part_2.pdf)
- [Executed analysis notebook](../parts/part-2-competitive-benchmarking/analysis/part2_pm_claim_feasibility.ipynb)
- [Part README](../parts/part-2-competitive-benchmarking/README.md)

## Final decisions

- Build an evidence-discovery product, not six hard-coded PM claim templates.
- Deterministic code owns deduplication, periods, denominators, metrics, uncertainty, eligibility,
  ranking, and source review IDs. Semantic models structure text and narrate approved claims.
- Separate evidence-bound Observations from testable Suggested Action Plans. Public reviews alone do
  not prove causes, motives, interventions, or promised business outcomes.
- Use a shared Core F&B Model, governed Category Playbooks, and an optional client Business Context
  Profile. New themes enter review rather than editing production definitions automatically.
- Each production summary has one focal client brand. The assessment report uses all three supplied
  brands to ground the design; it does not claim three separately generated client summaries.

## Data and verification

- 15,150 raw review rows from 2026-03-31 through 2026-06-29.
- One exact duplicate is excluded from metrics, leaving 15,149 canonical reviews: Lumen 3,665,
  Solara 6,900, and Vera 4,584.
- Most text-bearing reviews are Arabic, with a smaller English subset; 5,431 canonical reviews have
  no text.
- `python3 -m unittest discover -s tests -v` passes all eight tests.

References: [shared vocabulary](../CONTEXT.md#review-benchmarking),
[assessment brief](../AI_Engineer_Task.docx.pdf), and ADRs
[0010](../adrs/0010-separate-observations-from-action-plans.md) through
[0012](../adrs/0012-use-core-model-playbooks-and-client-context.md).
