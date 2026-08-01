# Part 3 - Pharmacy Operations Assistant

Working-prototype workspace for a non-technical COO of a pharmacy group. The assessment brief describes a restaurant group with 120 branches, but the supplied workbook and data dictionary identify a pharmacy operation with 132 branches and 64,619 delivery orders. The dataset is the authoritative domain source for this part.

## Required submission

This workspace will contain:

- Runnable prototype code and setup instructions.
- A short COO handoff: what the assistant does, how to use it, what it can be relied on for, and what it cannot answer.
- A short engineering handoff: what must be true before responsible production use.

The final README must provide verified local run instructions, required environment variables without secrets, test commands, deployment assumptions, and known limitations.

## Product boundary

The assistant answers supported operational questions over supplied orders, delivery timestamps, ratings, and comments. An LLM may translate a COO question into an allow-listed, read-only query plan; deterministic code performs all calculations and rankings. Responses show filters, definitions, observation counts, and evidence strength without exposing raw query logic by default.

Unsupported questions - including medication safety, inventory, staffing, and definitive causation - must be declined with the missing source named. For “why” questions, show measured timing contributors separately from customer-reported comment signals; neither establishes a proven root cause.

## Intended workspace layout

```text
part-3-pharmacy-operations-assistant/
├── README.md
├── apps/
│   ├── api/       # FastAPI analysis and bot integration
│   └── web/       # Internal React/admin debugging UI
├── docs/           # COO and engineering handoffs
├── data/           # Local derived data only; never commit source data or secrets
├── tests/          # Query, metric, and safety tests
└── deploy/         # Docker Compose and optional demo deployment material
```

The intended primary COO interface is a non-public Telegram bot protected by a Telegram-ID allowlist. The React application is an internal debugging/admin surface, not the primary user interface. Docker Compose is the canonical handoff. A Koyeb deployment may be added only as an optional public demonstration; it must not be treated as persistent or always available.

## Reliability requirements

- Calculate end-to-end delivery duration, dispatch lag, and pickup lag deterministically.
- Assign high, medium, or low evidence strength from observation count, time coverage, and data completeness; display the supporting counts.
- Suppress branch comparisons that do not meet a minimum comparability floor, especially for sparse or late-appearing branches.
- Keep all access read-only, credentials outside the repository, and no API key or Telegram bot token in code, documents, or outputs.

## References

- [Part 3 handoff](../../handoffs/roboost-assessment-part-3-handoff.md)
- [Assessment brief](../../AI_Engineer_Task.pdf)
- [Pharmacy Operations vocabulary](../../CONTEXT.md#pharmacy-operations)
- Related ADRs: [`0013`](../../docs/adr/0013-treat-part-3-as-a-pharmacy-domain.md), [`0014`](../../docs/adr/0014-show-evidence-strength-for-operational-calculations.md), [`0015`](../../docs/adr/0015-separate-measured-contributors-from-review-signals.md), [`0016`](../../docs/adr/0016-use-koyeb-only-for-the-public-demo.md)

