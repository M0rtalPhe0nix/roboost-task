# Handoff: Part 3 - Pharmacy Operations Assistant

## Submission status

Complete. The repository contains a runnable Google ADK assistant, Telegram transport, local ADK
Web launcher, deterministic pandas analytics, Docker handoff, tests, and stakeholder documentation.

## Canonical artifacts

- [Part README and setup](../parts/part-3-pharmacy-operations-assistant/README.md)
- [COO usage guide](../parts/part-3-pharmacy-operations-assistant/docs/coo-handoff.md)
- [Engineering production-readiness guide](../parts/part-3-pharmacy-operations-assistant/docs/engineering-handoff.md)
- [Northflank worker handoff](../parts/part-3-pharmacy-operations-assistant/deploy/northflank-worker.md)

## Final implementation

- Google ADK and Gemini interpret plain-language questions and explain aggregate results.
- One allow-listed `analyze_operations` tool delegates every calculation to deterministic pandas
  code; the model cannot execute SQL or retrieve source rows.
- The primary reviewer/COO interface is a private-chat Telegram bot. ADK Web is a loopback-only
  development and review surface.
- The supplied anonymized 64,619-order, 132-branch workbook is intentionally tracked at
  `data/operations_data_anonymized.xlsx` so a fresh clone is runnable. It must not be replaced with
  confidential patient, prescription, customer, or employee data.
- The assessment worker runs on Northflank using a private image and one long-polling replica.
- Evidence Strength, comparison floors, unsupported-question refusals, aggregate-only outputs, and
  bounded conversation/session memory are enforced by code.

## Verification boundary

Run `uv run ruff check .` and `uv run pytest --cov=app --cov-report=term-missing`. The tests are
deterministic and make no Gemini calls. A conversational eval set is retained as design evidence,
but no live model-scored evaluation is claimed for the final submission.

References: [shared vocabulary](../CONTEXT.md#pharmacy-operations),
[assessment brief](../AI_Engineer_Task.docx.pdf), ADRs
[0013](../adrs/0013-treat-part-3-as-a-pharmacy-domain.md) through
[0015](../adrs/0015-separate-measured-contributors-from-review-signals.md), and Northflank decision
[0017](../adrs/0017-use-northflank-for-the-public-demo.md).
