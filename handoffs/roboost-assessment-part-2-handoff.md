# Handoff: Part 2 - Competitive Benchmarking AI Summary

## Next-session objective

Produce the required written product exercise for the AI Summary tab, grounded in the supplied coffee review exports. Address all seven key questions, especially the six PM claims and evidence-bound generation.

## Read first

- Shared vocabulary: `/Users/mohamedomara/Documents/roboost-task/CONTEXT.md` (Review Benchmarking section)
- Decisions: `/Users/mohamedomara/Documents/roboost-task/docs/adr/0010-separate-observations-from-action-plans.md` through `0012-use-core-model-playbooks-and-client-context.md`
- Brief: `/Users/mohamedomara/Documents/roboost-task/AI_Engineer_Task.pdf` (Part 2)
- Review data: `/Users/mohamedomara/Documents/roboost-task/AI Engineer Assessment/Benchmark Reviews/Files/`

## Settled scope

- Generate three focal-brand views: one each for Lumen Coffee, Solara Coffee, and Vera Coffee. In each view, the other two are competitors.
- Build a dynamic evidence-discovery product, not six hard-coded PM templates. Deterministic computation finds trends, gaps, branch outliers, recurring/emerging themes, reviewer overlap, and response-coverage patterns; LLMs label/cluster novel language, prioritize validated candidates, and narrate.
- Every narrative claim must be represented by a deterministic, evidence-bound insight candidate containing metrics, definitions, confidence/evidence rules, and source review IDs. Unsupported insights are suppressed.
- Use Observation then Suggested Action Plan in the UX. Observations are descriptive and evidence-bound; Action Plans are clearly separate, testable recommendations, not promises or causal claims.
- Business-operational feasibility requires a client-provided Business Context Profile. In review-only mode, show generic testable action hypotheses and name the missing context rather than inventing owners/timelines.
- Use three configuration layers: Core F&B Model, governed Category Playbook, and client-specific Business Context Profile. Do not rebuild the product per category and do not let novel themes auto-edit production playbooks.

## Data profile already established

- 15,150 reviews from 2026-03-31 through 2026-06-29.
- Lumen: 3,665 reviews, 70 branches; Solara: 6,901, 67; Vera: 4,584, 20.
- All supplied reviews are Arabic, despite the product requirement being Arabic-English.
- The exports contain public reviewer IDs, branch/city, ratings, text, dates, detailed ratings when present, and owner-response fields. Reviewer overlap exists between every brand pair.

## Initial PM-claim stance to validate in the document

- (a) minable with fixed period/aspect definitions; not LLM arithmetic.
- (b) reviewer overlap directly computable; taste comparison needs carefully defined evidence-backed aspect extraction.
- (c) only a proxy based on defined repeat-customer language, never actual regular-customer behavior.
- (d) causal “fixed it” claim must be hedged; reviews cannot prove intervention or cause.
- (e) loyalty-causes-forgiveness is beyond review-only evidence; co-occurrence is the strongest permitted rewrite.
- (f) action prioritization can be defensible only with definitions and evidence; it must not promise protection of an undefined product lead.

## Open work

- Perform reproducible exploratory analysis for real examples, including sample-size/confidence treatment.
- Define a generic insight-candidate schema and evidence eligibility rules.
- Explain regenerate consistency: frozen dataset/config/model version, cache/approved insight set, and variation only at narration layer.
- Decide document versus deck with the user if still needed.

## Suggested skills

- `spreadsheets:Spreadsheets` for the data dictionary workbook.
- `domain-modeling` for evolving product language.
- `pdf:pdf` for brief verification.
- `excalidraw` if an editable evidence-generation architecture diagram is useful.
