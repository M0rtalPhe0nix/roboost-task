# AI Engineer Assessment

Completed four-part AI Engineer Assessment submission. Parts 1 and 2 are written product exercises; Parts 3 and 4 contain runnable implementations, reviewer-facing documentation, tests, and reproducible output evidence.

## Selected assessment paths

| Part | Assessment deliverable | Repository workspace |
| --- | --- | --- |
| 1 | Case Study 2: Product Listing Intelligence (report and architecture diagram) | [`parts/part-1-product-listing-intelligence`](parts/part-1-product-listing-intelligence/README.md) |
| 2 | Competitive Benchmarking AI Summary (written report and reproducible analysis) | [`parts/part-2-competitive-benchmarking`](parts/part-2-competitive-benchmarking/README.md) |
| 3 | Pharmacy Operations Assistant prototype | [`parts/part-3-pharmacy-operations-assistant`](parts/part-3-pharmacy-operations-assistant/README.md) |
| 4 | Option C: High-Volume Message Triage | [`parts/part-4-message-triage`](parts/part-4-message-triage/README.md) |

Parts 1 and 4 each require one selected option. The selections above are the ones established in the task handoffs. Part 3 is described as a restaurant assistant in the brief, but the supplied workbook is pharmacy data; this repository follows the data and records that assumption explicitly.

## Repository map

```text
.
├── parts/
│   ├── part-1-product-listing-intelligence/   # Final written case study and architecture diagram
│   ├── part-2-competitive-benchmarking/       # Written product exercise and analysis
│   ├── part-3-pharmacy-operations-assistant/  # Runnable prototype and handoffs
│   └── part-4-message-triage/                 # Runnable pipeline and classifications
├── adrs/                                      # Cross-cutting decision records
├── handoffs/                                  # Current task-by-task continuation notes
├── CONTEXT.md                                 # Shared assessment vocabulary
└── AI_Engineer_Task.docx.pdf                  # Source brief (local reference)
```

Assessment inputs live under their corresponding part. Part 2 review exports and the Part 4 message corpus remain ignored local inputs. The supplied anonymized Part 3 workbook is intentionally included so the prototype is runnable from a fresh clone.

## Submission artifacts

| Part | Canonical reviewer artifact |
| --- | --- |
| 1 | [Product Listing Intelligence report](parts/part-1-product-listing-intelligence/outputs/part1-report.md) and [architecture diagram](parts/part-1-product-listing-intelligence/outputs/Part1.svg) |
| 2 | [Competitive Benchmarking report](parts/part-2-competitive-benchmarking/outputs/Part_2.md), [PDF export](parts/part-2-competitive-benchmarking/outputs/part_2.pdf), and [executed analysis notebook](parts/part-2-competitive-benchmarking/analysis/part2_pm_claim_feasibility.ipynb) |
| 3 | [Runnable assistant](parts/part-3-pharmacy-operations-assistant/README.md), [COO guide](parts/part-3-pharmacy-operations-assistant/docs/coo-handoff.md), and [engineering guide](parts/part-3-pharmacy-operations-assistant/docs/engineering-handoff.md) |
| 4 | [Runnable triage pipeline](parts/part-4-message-triage/README.md), [classifications](parts/part-4-message-triage/outputs/classifications.jsonl), and [approach document](parts/part-4-message-triage/docs/approach.md) |

## How to use this repository

1. Start in the README for the part you are working on; it lists its scope, deliverables, guardrails, and intended artifact locations.
2. Read the matching file in [`handoffs/`](handoffs/) and any linked ADRs before changing a part's design.
3. Put source code, tests, documents, and reproducible outputs in that part's workspace.
4. Preserve the recorded run, cost, and deployment evidence. Do not replace measured values with unverified claims.

## Documentation and decision sources

- The [assessment brief](AI_Engineer_Task.docx.pdf) defines the requested deliverables.
- [`CONTEXT.md`](CONTEXT.md) defines the terms that must retain the same meaning across the repository.
- [`adrs/`](adrs/) records the material design decisions already made.
- [`handoffs/`](handoffs/) captures the final implementation context, verification boundary, and any continuation notes for each part.

## Repository conventions

- Each part is independently reviewable and owns its code, documents, tests, and generated deliverables.
- Part 1 uses a Markdown report and self-contained SVG architecture diagram as its canonical source deliverables. Part 2 uses a Markdown report, PDF export, and executed analysis notebook.
- `outputs/` is for reproducible submission artifacts, never secrets or raw source data.
- `docs/` holds audience-facing and engineering-facing documents; `app/` or `src/` holds implementation when applicable.
- Decisions that affect more than one part belong in `adrs/`; avoid silently redefining shared terms in a local README.
- The source brief allows any provider or framework. Provider, model, prompt, and cost claims must be versioned and evidenced in the applicable part workspace.

## Current status

| Part | Status |
| --- | --- |
| 1 | Final written case study and architecture diagram completed |
| 2 | Final written exercise, PDF, and reproducible analysis completed |
| 3 | Prototype, deterministic suite, COO handoff, engineering handoff, and Northflank demo completed |
| 4 | Full-corpus classifications and cost evidence completed; no human quality evaluation is claimed or planned for this submission |
