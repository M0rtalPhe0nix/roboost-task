# Evaluation record

Status: not performed for the final submission.

## Submission decision

The completed classifier run is submitted with deterministic contract tests, full-corpus output,
provider usage, and cost evidence. No human annotation, calibration exercise, held-out evaluation,
accuracy, macro-F1, per-label metric, or calibrated-confidence claim is included.

The final classifications were produced by `gemini-3.5-flash-lite` plus the documented rule gate
under configuration hash
`aacd6cb395fc4762708497418f6bd7adfd177b67d75ea5a36a340f398167ffa2`.
The run contains all 5,551 eligible customer turns. Provider-reported usage for 154 completed
requests was 574,833 input tokens and 157,498 billed output tokens, costing USD 0.566264. Including
the retained outstanding reservation, conservative committed cost is USD 0.574427, below the USD
1 assessment limit.

## What remains in the repository

The codebase retains tested `prepare-evaluation` and `score-evaluation` commands that can create a
conversation-disjoint 200-message calibration split and 800-message held-out split. The unused
workflow supports stratified sampling, blinded review queues, inverse-sampling-weighted metrics,
schema validation, and leakage checks.

No review queues were generated for the final submission, and `outputs/evaluation/` intentionally
contains no artifacts. The annotation guide remains as design documentation only.

## Claim boundary

The submission may claim:

- one validated classification row for every eligible customer turn;
- source-order preservation and one-to-one message identity;
- use of past conversation history only;
- deterministic rule, schema, retry, budget, and leakage test coverage;
- provider-reported token usage and measured cost; and
- an enforced budget below the USD 1 task limit.

It may not claim measured classification quality, calibrated probability, representative accuracy,
or label-level recall. The `confidence_band` field is an uncalibrated operational placeholder tied
to decision source, not a model probability or evaluated reliability score.
