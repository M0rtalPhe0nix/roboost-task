# Repository Guidelines

## Project Structure & Module Organization

This is a completed four-part AI Engineer Assessment submission. Start with the root [README.md](README.md), then work in the relevant `parts/part-*/` directory. Each part owns its implementation, documentation, tests, and submission artifacts:

- `outputs/` and `analysis/` hold the written deliverables and reproducible evidence for Parts 1 and 2.
- `app/`, `src/`, and `tests/` hold runnable work for Parts 3 and 4.
- `adrs/` contains cross-cutting architecture decision records; `handoffs/` contains current completion and continuation notes.
- `shared/` is for code or schemas used by at least two parts. Do not create shared abstractions prematurely.
- `outputs/` contains reproducible, review-safe artifacts. Part 2 and Part 4 source inputs remain ignored. The supplied anonymized Part 3 workbook is intentionally tracked so the prototype is runnable from a fresh clone.

Read the part README, its matching handoff, `CONTEXT.md`, and linked ADRs before changing assumptions or terminology.

## Build, Test, and Development Commands

There is no repository-wide build system, package manifest, or test runner yet. Add verified, part-local commands to the part README when implementation begins. Prefer commands run from the part directory, such as `npm test`, `pytest`, or `docker compose up --build`, and state their purpose.

For documentation changes, validate relative Markdown links and inspect final Markdown, SVG, and PDF artifacts before submitting. Do not record planned commands as if they had been run.

## Specification & Issue Workflow

Use GitHub Issues as the canonical tracker for implementation-ready specifications. Apply `ready-for-agent` only after the problem, solution, user stories, implementation decisions, testing seam, exclusions, and relevant assessment traceability are settled; implementation pull requests should link the originating issue.

## Coding Style & Naming Conventions

Match the conventions of the toolchain added to the relevant part and commit its formatter/linter configuration with the code. Use descriptive, lowercase kebab-case directory and document names (for example, `part-4-message-triage` and `approach-notes.md`). Keep code, test, and configuration files local to their owning part unless they are genuinely reusable.

Keep generated deliverables reproducible. Version model/provider, prompt, configuration, and dataset assumptions in the owning workspace; do not make unverified performance, cost, or deployment claims.

## Testing Guidelines

Place tests in the owning part's `tests/` directory. Name tests after behavior, such as `test_urgent_label_overrides_primary_intent`. Parts 3 and 4 should cover deterministic metrics/routing, schema validation, safety boundaries, and leakage or budget guards. Run the documented part-local suite before opening a pull request and report any unrun checks.

## Commit & Pull Request Guidelines

Existing history uses short, imperative summaries (for example, `Add initial README files and directory structure`). Keep commits focused and describe the affected part. Pull requests should explain the deliverable or decision, link relevant assessment requirements or ADRs, list verification performed, and include screenshots for presentation/UI changes. Do not commit API keys, tokens, local exports, or additional raw assessment data. The tracked anonymized Part 3 workbook is the explicit assessment-only exception.
