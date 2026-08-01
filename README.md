# AI Engineer Assessment

An organized monorepo for the four-part AI Engineer Assessment. It is deliberately a **scaffold**: this repository currently establishes the submission structure, decision record, and handoff-ready documentation. It does not represent completed implementations or submitted outputs.

## Selected assessment paths

| Part | Assessment deliverable | Repository workspace |
| --- | --- | --- |
| 1 | Case Study 2: Product Listing Intelligence (HTML presentation) | [`parts/part-1-product-listing-intelligence`](parts/part-1-product-listing-intelligence/README.md) |
| 2 | Competitive Benchmarking AI Summary (HTML presentation) | [`parts/part-2-competitive-benchmarking`](parts/part-2-competitive-benchmarking/README.md) |
| 3 | Pharmacy Operations Assistant prototype | [`parts/part-3-pharmacy-operations-assistant`](parts/part-3-pharmacy-operations-assistant/README.md) |
| 4 | Option C: High-Volume Message Triage | [`parts/part-4-message-triage`](parts/part-4-message-triage/README.md) |

Parts 1 and 4 each require one selected option. The selections above are the ones established in the task handoffs. Part 3 is described as a restaurant assistant in the brief, but the supplied workbook is pharmacy data; this repository follows the data and records that assumption explicitly.

## Repository map

```text
.
├── parts/
│   ├── part-1-product-listing-intelligence/   # HTML case-study presentation
│   ├── part-2-competitive-benchmarking/       # HTML product-exercise presentation
│   ├── part-3-pharmacy-operations-assistant/  # Runnable prototype and handoffs
│   └── part-4-message-triage/                 # Runnable pipeline and classifications
├── shared/                                    # Reusable code or schemas only when justified
├── docs/
│   ├── adr/                                   # Cross-cutting decision records
│   └── assessment/                            # Final cross-part submission material
├── handoffs/                                  # Current task-by-task continuation notes
├── CONTEXT.md                                 # Shared assessment vocabulary
└── AI_Engineer_Task.pdf                       # Source brief (local reference)
```

The assessment datasets live under `AI Engineer Assessment/`. That directory is intentionally ignored: source data, API keys, tokens, local exports, and generated working files must never be committed.

## How to use this repository

1. Start in the README for the part you are working on; it lists its scope, deliverables, guardrails, and intended artifact locations.
2. Read the matching file in [`handoffs/`](handoffs/) and any linked ADRs before changing a part's design.
3. Put source code, tests, documents, and reproducible outputs in that part's workspace. Keep cross-cutting utilities in `shared/` only after at least two parts genuinely need them.
4. Update the part README with real run, evaluation, cost, and deployment evidence as the work is completed. Do not replace planned values with unverified claims.

## Documentation and decision sources

- The [assessment brief](AI_Engineer_Task.pdf) defines the requested deliverables.
- [`CONTEXT.md`](CONTEXT.md) defines the terms that must retain the same meaning across the repository.
- [`docs/adr/`](docs/adr/) records the material design decisions already made.
- [`handoffs/`](handoffs/) captures the current implementation context and next steps for each part.

## Repository conventions

- Each part is independently reviewable and owns its code, documents, tests, and generated deliverables.
- Parts 1 and 2 use self-contained HTML presentations as their canonical deliverables. Their `presentation/` folders are for the presentation source and any local assets; `docs/` holds supporting notes only.
- `outputs/` is for reproducible submission artifacts, never secrets or raw source data.
- `docs/` holds audience-facing and engineering-facing documents; `src/`/`apps/` holds implementation when applicable.
- Decisions that affect more than one part belong in `docs/adr/`; avoid silently redefining shared terms in a local README.
- The source brief allows any provider or framework. Provider, model, prompt, and cost claims must be versioned and evidenced in the applicable part workspace.

## Current status

| Part | Status |
| --- | --- |
| 1 | Documentation workspace scaffolded |
| 2 | Documentation and analysis workspace scaffolded |
| 3 | Prototype and handoff workspace scaffolded |
| 4 | Pipeline and classification-output workspace scaffolded |
