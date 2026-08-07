#!/usr/bin/env python3
"""Build and execute the dependency-free Part 2 feasibility notebook."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path


def markdown(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip() + "\n"}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.strip() + "\n",
    }


CELLS = [
    markdown(
        r"""
# Part 2 PM-claim feasibility: reconstructed database and definitive verdict

**Decision:** none of the six mocked claims is safe to publish exactly as written. Claim (a) is minable only after a validated complaint definition and cannot be quarter-over-quarter from a single 90-day snapshot. Claim (b) must be split: reviewer overlap is exact, while "taste" is not a supplied metric. Claims (c) and (d) are observations that require hedging. Claims (e) and (f) are judgments beyond review-only evidence.

This notebook reconstructs the supplied JSON exports into a constrained SQLite database, verifies the joins and source counts, and tests every claim against the actual data. It uses no LLM for arithmetic or facts. Text rules below are transparent **feasibility proxies**, not production-validated classifiers.

Authoritative inputs: [assessment brief, Part 2 on page 4](../../../AI_Engineer_Task.docx.pdf), [schema dictionary](../DATA_DICTIONARY.xlsx), and the seven files in `../Files/`.
"""
    ),
    code(
        r"""
from pathlib import Path
import sys

ROOT = Path.cwd().resolve()
if not (ROOT / "Files").exists():
    if (ROOT.parent / "Files").exists():
        ROOT = ROOT.parent
    else:
        raise FileNotFoundError("Run from the Part 2 directory or its analysis/ directory")
sys.path.insert(0, str(ROOT))

from analysis.reconstruct_database import build_database
from analysis.feasibility_analysis import (
    CLAIM_CLASSIFICATIONS,
    COMPLAINT_THEMES,
    THEME_DEFINITIONS,
    analysis_window,
    connect,
    data_quality,
    database_profile,
    evidence_sample,
    fastest_growing_complaints,
    format_table,
    loyalty_evidence,
    overlap_ratings,
    period_rating_trends,
    reviewer_overlap,
    select_trends,
    theme_trends,
)

DB_PATH = ROOT / "analysis/generated/competitive_benchmarking.sqlite"
build_result = build_database(ROOT / "Files", ROOT / "DATA_DICTIONARY.xlsx", DB_PATH)
connection = connect(DB_PATH)
print(f"Database: {DB_PATH.relative_to(ROOT)}")
print(build_result["counts"])
"""
    ),
    markdown(
        r"""
## 1. Reconstruction and validation

The relational model keeps canonical entities separate from source lineage:

- `brands`, `branches`, `reviewers`, and `reviews` hold canonical records.
- Nested JSON is normalized into branch categories, star distributions, opening hours, popular times, attributes, tags, review categories, context, detailed ratings, and menu items.
- `source_branch_records` and `source_review_records` retain canonical raw JSON, file/ordinal lineage, and SHA-256 hashes.
- `ingestion_manifest` fingerprints every input; `data_dictionary_fields` imports field definitions and provenance from the workbook.
- Exact duplicate source rows remain auditable, but only one canonical review contributes to metrics.
"""
    ),
    code(
        r"""
profile = database_profile(connection)
quality = data_quality(connection)
print(format_table(profile, [
    ("brand_name", "brand"), ("unique_reviews", "unique reviews"), ("reviewers", "reviewers"),
    ("reviewed_branches", "branches"), ("first_date", "first date"), ("last_date", "last date"),
    ("mean_stars", "mean stars"), ("reviews_with_text", "text reviews"),
    ("owner_responses", "owner responses"),
]))
print("\nIntegrity and coverage")
print(format_table([quality], [(key, key.replace("_", " ")) for key in quality]))
"""
    ),
    markdown(
        r"""
**Data-quality consequence.** The source contains 15,150 rows but 15,149 unique review IDs because one row is an exact duplicate. Also, 5,431 canonical reviews have no text. Text-theme prevalence is therefore normalized by **text-bearing reviews**, while overall rating metrics use all canonical reviews. The workbook labels every record language as Arabic, but detected original-language metadata includes Arabic, English, other languages, and nulls; a production extractor must be multilingual and explicitly evaluate missing-language behavior.
"""
    ),
    markdown(
        r"""
## 2. Decision framework and fixed definitions

The assessment's four feasibility classes are applied to the entire claim. Compound claims are split when their components have different evidence status. "Directly computable" means an exact deterministic aggregation of supplied fields. "Minable" means the claim depends on a declared and validated semantic definition. "Inference" permits only an explicitly hedged association. "Judgment beyond" means the required causal, operational, or strategic premise is absent.

For temporal feasibility only, the single ~90-day snapshot is split at its exact timestamp midpoint into equal-duration early and recent halves. This is **not** a prior-quarter/current-quarter comparison. Rates are per 1,000 text-bearing reviews; counts, denominators, Wilson 95% intervals, and review IDs remain available.
"""
    ),
    code(
        r"""
window = analysis_window(connection)
print(f"Snapshot start: {window['start'].isoformat()}")
print(f"Snapshot end:   {window['end'].isoformat()}")
print(f"Duration:       {window['duration_days']:.2f} days")
print(f"Midpoint:       {window['midpoint'].isoformat()}")

definitions = [
    {"theme": theme, "low_rating_required": item["requires_low_rating"], "definition": item["description"],
     "terms": ", ".join(item["terms"])}
    for theme, item in THEME_DEFINITIONS.items()
]
print("\nDeclared feasibility proxies")
print(format_table(definitions, [
    ("theme", "theme"), ("low_rating_required", "requires 1-3 stars"), ("definition", "definition")
]))
"""
    ),
    code(
        r"""
print("Definitive classification matrix")
print(format_table(list(CLAIM_CLASSIFICATIONS), [
    ("claim", "PM claim"), ("classification", "classification"),
    ("as_written", "as written"), ("strongest_supported_version", "strongest honest version"),
]))
"""
    ),
    markdown(
        r"""
## 3. Claim (a): wait-time complaints doubled this quarter

**Classification: minable with careful definitions. As written: infeasible.** A wait complaint is not a supplied field, and the source has no earlier quarter. The table below tests only a high-precision feasibility proxy: a 1-3 star review containing a declared wait/delay/queue/crowding term.
"""
    ),
    code(
        r"""
trends = theme_trends(connection)
wait_rows = select_trends(trends, ["wait_time_complaint"])
print(format_table(wait_rows, [
    ("brand", "brand"), ("early_text_reviews", "early text n"), ("early_matches", "early complaints"),
    ("early_per_1000", "early /1k"), ("early_ci_low_per_1000", "early CI low"),
    ("early_ci_high_per_1000", "early CI high"), ("recent_text_reviews", "recent text n"),
    ("recent_matches", "recent complaints"), ("recent_per_1000", "recent /1k"),
    ("recent_ci_low_per_1000", "recent CI low"), ("recent_ci_high_per_1000", "recent CI high"),
    ("relative_change_percent", "rate change %"), ("evidence_grade", "evidence"),
]))
for row in wait_rows:
    print(f"{row['brand']} evidence sample: {', '.join(evidence_sample(trends, row['brand'], 'wait_time_complaint'))}")
"""
    ),
    markdown(
        r"""
**Verdict for (a).** Lumen's proxy is the only near-doubling within the snapshot, rising from 23 to 51 matches and from roughly 20 to 38 per 1,000 text reviews. That is not the mocked 37-to-75 claim and not "this quarter" versus a prior quarter. A production claim requires an annotated wait-time evaluation set, frozen period boundaries, deduplication, minimum support, and review-ID evidence.
"""
    ),
    markdown(
        r"""
## 4. Claim (b): shared customers and taste ratings

**Classification: split.** Unique-reviewer overlap is directly computable because `reviewer_id` is stable across brands. The supplied star is overall, not taste. The closest structured field is the Arabic `الطعام` (food) detailed rating; it must not be relabeled as taste. To avoid overweighting prolific reviewers, each customer's reviews are averaged within a brand before customers are averaged.
"""
    ),
    code(
        r"""
overlap = reviewer_overlap(connection)
print("Exact unique-reviewer overlap")
print(format_table(overlap, [
    ("brand_a", "brand A"), ("brand_b", "brand B"), ("shared_reviewers", "shared reviewers"),
    ("shared_reviewers_also_at_third_brand", "also reviewed third"),
    ("pair_exclusive_reviewers", "pair-exclusive"),
]))

rating_rows = overlap_ratings(connection)
print("\nCustomer-balanced supplied metrics for the same overlapping reviewers")
print(format_table(rating_rows, [
    ("brand_a", "brand A"), ("brand_b", "brand B"), ("shared_reviewers", "shared n"),
    ("a_overall_stars_mean", "A overall"), ("a_overall_stars_reviewers", "A overall n"),
    ("b_overall_stars_mean", "B overall"), ("b_overall_stars_reviewers", "B overall n"),
    ("a_food_subrating_mean", "A food"), ("a_food_subrating_reviewers", "A food n"),
    ("b_food_subrating_mean", "B food"), ("b_food_subrating_reviewers", "B food n"),
], digits=3))
"""
    ),
    markdown(
        r"""
**Verdict for (b).** The actual pair totals are 63, 30, and 65 shared reviewers. The mocked "61" happens to equal the Lumen-Solara **pair-exclusive** subset after incorrectly excluding two reviewers who also reviewed Vera; the correct inclusive overlap is 63. Neither the customer-balanced overall stars nor the food sub-ratings reproduce a 4.4-versus-4.0 taste gap. Publish overlap and metric coverage as separate facts; use "taste" only after a validated aspect-level extractor.
"""
    ),
    markdown(
        r"""
## 5. Claim (c): regulars are going quiet

**Classification: inference that must be hedged.** The data can count phrases that imply previous or repeated visits, but it cannot observe visits without reviews, define actual regulars, or prove that a customer segment is becoming quiet.
"""
    ),
    code(
        r"""
repeat_rows = select_trends(trends, ["repeat_visit_language"])
print(format_table(repeat_rows, [
    ("brand", "brand"), ("early_text_reviews", "early text n"), ("early_matches", "early proxy n"),
    ("early_per_1000", "early /1k"), ("recent_text_reviews", "recent text n"),
    ("recent_matches", "recent proxy n"), ("recent_per_1000", "recent /1k"),
    ("relative_change_percent", "rate change %"), ("evidence_grade", "evidence"),
]))
"""
    ),
    markdown(
        r"""
**Verdict for (c).** None of the brands shows the mocked 38% decline under this declared proxy. The strongest honest wording is: "The share of text reviews containing the defined repeat-visit-language proxy changed by X between the two halves." It must immediately state that this does not measure regular-customer visits or silence.
"""
    ),
    markdown(
        r"""
## 6. Claim (d): a competitor fixed wait time and gained 0.4 stars

**Classification: inference that must be hedged.** The data has no intervention date, measured wait time, operational treatment, or control group. It can show only parallel temporal movements in review-derived proxies.
"""
    ),
    code(
        r"""
rating_trends = period_rating_trends(connection)
combined = []
for wait in wait_rows:
    rating = next(row for row in rating_trends if row["brand"] == wait["brand"])
    combined.append({
        "brand": wait["brand"],
        "early_wait_per_1000": wait["early_per_1000"],
        "recent_wait_per_1000": wait["recent_per_1000"],
        "wait_rate_change": wait["relative_change_percent"],
        "early_mean_stars": rating["early_mean_stars"],
        "recent_mean_stars": rating["recent_mean_stars"],
        "star_change": rating["change_stars"],
    })
print(format_table(combined, [
    ("brand", "brand"), ("early_wait_per_1000", "early wait /1k"),
    ("recent_wait_per_1000", "recent wait /1k"), ("wait_rate_change", "wait change %"),
    ("early_mean_stars", "early stars"), ("recent_mean_stars", "recent stars"),
    ("star_change", "star change"),
], digits=3))
"""
    ),
    markdown(
        r"""
**Verdict for (d).** No brand gained 0.4 stars. Vera shows a lower wait-complaint proxy and only a small +0.037-star association; Solara's wait proxy is nearly flat and stars decline slightly; Lumen's wait proxy rises while stars decline. None of these patterns identifies a fix or proves causality.
"""
    ),
    markdown(
        r"""
## 7. Claim (e): loyalty makes customers forgive mistakes

**Classification: judgment beyond what the data supports.** Reviews do not contain program enrollment, exposure, redemption, known mistakes, or a counterfactual. Even explicit loyalty-term mentions can establish only sparse co-occurrence.
"""
    ),
    code(
        r"""
loyalty_rows = loyalty_evidence(connection)
print(format_table(loyalty_rows, [
    ("brand", "brand"), ("mentions", "loyalty-term reviews"),
    ("low_rating_mentions", "1-3 star co-occurrence"), ("high_rating_mentions", "4-5 star co-occurrence"),
]))
for row in loyalty_rows:
    print(f"{row['brand']} evidence IDs: {', '.join(row['evidence_ids'][:8]) or 'none'}")
"""
    ),
    markdown(
        r"""
**Verdict for (e).** The evidence is sparse and the terms themselves require precision validation. Co-occurrence with a star band cannot mean "forgiveness," and nothing in this dataset can answer *why*. Suppress the causal claim.
"""
    ),
    markdown(
        r"""
## 8. Claim (f): first move is delivery packaging

**Classification: judgment beyond what the data supports.** A predeclared system can rank eligible complaint proxies, but an action priority also needs business impact, root cause, controllability, cost, owner, constraints, and an operational success metric. "Protects the product lead" additionally requires a defined product-lead metric and a causal premise.
"""
    ),
    code(
        r"""
fastest = fastest_growing_complaints(trends)
print("Fastest increase among eligible declared complaint proxies")
print(format_table(fastest, [
    ("brand", "brand"), ("theme", "fastest proxy"), ("early_matches", "early n"),
    ("recent_matches", "recent n"), ("early_per_1000", "early /1k"),
    ("recent_per_1000", "recent /1k"), ("absolute_change_per_1000", "change /1k"),
]))

print("\nPackaging specifically")
packaging_rows = select_trends(trends, ["packaging_complaint"])
print(format_table(packaging_rows, [
    ("brand", "brand"), ("early_matches", "early n"), ("early_per_1000", "early /1k"),
    ("recent_matches", "recent n"), ("recent_per_1000", "recent /1k"),
    ("relative_change_percent", "rate change %"), ("evidence_grade", "evidence"),
]))
"""
    ),
    markdown(
        r"""
**Verdict for (f).** Packaging is not the fastest-rising eligible proxy for Lumen or Solara under these definitions; it is for Vera. Even for Vera, the defensible output is an **Observation** plus a **Suggested validation plan**, not a direct order: inspect the cited reviews, verify the taxonomy on labeled data, segment by branch/channel/menu item, and obtain client context before prioritizing an intervention. No review-only analysis can promise to protect a product lead.
"""
    ),
    markdown(
        r"""
## 9. Final product decision

| Claim | Definitive feasibility | Product behavior |
|---|---|---|
| (a) | Minable, but not quarter-over-quarter from this snapshot | Rewrite as a defined within-window observation or wait for a prior comparable period |
| (b) | Overlap direct; taste not supplied | Split the facts; disclose metric meaning and coverage |
| (c) | Hedged language proxy only | Never label people as regulars or infer offline silence |
| (d) | Association only | Never claim a fix, intervention, or causal star gain from reviews |
| (e) | Beyond support | Suppress; sparse co-occurrence is not motive or causality |
| (f) | Theme ranking is minable; strategic order is beyond support | Show Observation, then a testable Suggested Action Plan gated by Business Context |

The feasible product is therefore an **evidence-discovery system**, not an autonomous strategist. Deterministic code owns deduplication, joins, period definitions, denominators, aggregations, uncertainty, eligibility, and review IDs. A validated multilingual model may assign aspects or discover candidate language, but it may not calculate metrics or invent evidence. Unsupported candidates are suppressed. Regeneration must freeze the dataset hashes, schema/playbook version, model version, thresholds, and approved candidates; only narration may vary, or the reviewed output should be cached.
"""
    ),
]


def execute_cells(notebook: dict) -> None:
    namespace = {"__name__": "__main__"}
    execution_count = 0
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        execution_count += 1
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(compile(cell["source"], f"notebook-cell-{index}", "exec"), namespace)
        outputs = []
        if stdout.getvalue():
            outputs.append({"name": "stdout", "output_type": "stream", "text": stdout.getvalue()})
        if stderr.getvalue():
            outputs.append({"name": "stderr", "output_type": "stream", "text": stderr.getvalue()})
        cell["execution_count"] = execution_count
        cell["outputs"] = outputs


def build_notebook(output_path: Path) -> None:
    notebook = {
        "cells": CELLS,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    execute_cells(notebook)
    output_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    build_notebook(root / "analysis/part2_pm_claim_feasibility.ipynb")
    print("Wrote and executed analysis/part2_pm_claim_feasibility.ipynb")
