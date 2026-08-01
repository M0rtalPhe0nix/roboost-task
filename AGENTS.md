# Repository Guidelines

## Project Structure & Module Organization

This is a four-part AI Engineer Assessment scaffold. Start with the root [README.md](README.md), then work in the relevant `parts/part-*/` directory. Each part owns its implementation, documentation, tests, and submission artifacts:

- `presentation/` holds the canonical self-contained HTML deliverable for Parts 1 and 2.
- `apps/`, `src/`, and `tests/` are reserved for runnable work in Parts 3 and 4.
- `docs/adr/` contains cross-cutting architecture decision records; `handoffs/` contains current continuation notes.
- `shared/` is for code or schemas used by at least two parts. Do not create shared abstractions prematurely.
- `outputs/` contains reproducible, review-safe artifacts. Source assessment data remains in the ignored `AI Engineer Assessment/` directory.

Read the part README, its matching handoff, `CONTEXT.md`, and linked ADRs before changing assumptions or terminology.

## Build, Test, and Development Commands

There is no repository-wide build system, package manifest, or test runner yet. Add verified, part-local commands to the part README when implementation begins. Prefer commands run from the part directory, such as `npm test`, `pytest`, or `docker compose up --build`, and state their purpose.

For documentation changes, validate relative Markdown links and open HTML presentations locally before submitting. Do not record planned commands as if they had been run.

## Coding Style & Naming Conventions

Match the conventions of the toolchain added to the relevant part and commit its formatter/linter configuration with the code. Use descriptive, lowercase kebab-case directory and document names (for example, `part-4-message-triage` and `approach-notes.md`). Keep code, test, and configuration files local to their owning part unless they are genuinely reusable.

Keep generated deliverables reproducible. Version model/provider, prompt, configuration, and dataset assumptions in the owning workspace; do not make unverified performance, cost, or deployment claims.

## Testing Guidelines

Place tests in the owning part's `tests/` directory. Name tests after behavior, such as `test_urgent_label_overrides_primary_intent`. Parts 3 and 4 should cover deterministic metrics/routing, schema validation, safety boundaries, and leakage or budget guards. Run the documented part-local suite before opening a pull request and report any unrun checks.

## Commit & Pull Request Guidelines

Existing history uses short, imperative summaries (for example, `Add initial README files and directory structure`). Keep commits focused and describe the affected part. Pull requests should explain the deliverable or decision, link relevant assessment requirements or ADRs, list verification performed, and include screenshots for presentation/UI changes. Never commit raw assessment data, API keys, tokens, or local exports.
