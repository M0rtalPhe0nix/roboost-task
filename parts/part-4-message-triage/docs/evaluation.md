# Evaluation protocol and run record

Status: classifier run complete; review queues prepared; human gold labels pending.

## Frozen run candidate

The completed classifications were produced by `gemini-3.5-flash-lite` plus the documented rule
gate under configuration hash
`aacd6cb395fc4762708497418f6bd7adfd177b67d75ea5a36a340f398167ffa2`.
The run contains all 5,551 eligible customer turns. Provider-reported usage for 154 completed
requests was 574,833 input tokens and 157,498 billed output tokens, costing USD 0.566264. Including
the one deliberately retained outstanding reservation, conservative committed cost is USD
0.574427, below the USD 1 assessment limit.

No further paid request is required to evaluate these predictions. Treat this configuration as
frozen while reviewing. If calibration reveals a critical defect and the classifier changes, the
existing held-out predictions are invalid for that revised classifier; a replacement run must also
respect cumulative assessment spend.

## Sampling design

`uv run triage prepare-evaluation` created a deterministic, 1,000-message sample with seed
`20260806`. Conversations are assigned wholly to calibration or held-out before sampling, avoiding
cross-split context leakage. Sampling is stratified by predicted routing label to ensure useful rare
class coverage:

| Predicted routing label | Calibration | Held-out | Total |
| --- | ---: | ---: | ---: |
| Urgent escalation | 3 | 8 | 11 |
| Spam | 20 | 80 | 100 |
| Refund request | 24 | 96 | 120 |
| Compliment | 36 | 144 | 180 |
| Complaint | 40 | 160 | 200 |
| Order inquiry | 77 | 312 | 389 |
| **Total** | **200** | **800** | **1,000** |

All 11 predicted urgent escalations are included. The selected rows cover 742 Arabic, 202 English,
51 mixed-language, and 5 other-language messages across Facebook, Instagram, TikTok, and X.
Because the sample is not proportional to the predicted-label population, the scorer reports both
raw sample metrics and inverse-sampling-weighted population estimates.

## Blinding and files

- `outputs/evaluation/calibration-review.csv`: annotate first; 200 rows.
- `outputs/evaluation/heldout-review.csv`: annotate only after the calibration decision is frozen;
  800 rows.
- `outputs/evaluation/evaluation-manifest.csv`: predictions, stratum counts, weights, and
  configuration hash. Do not open this while labeling.
- `outputs/evaluation/evaluation-metadata.json`: reproducibility metadata and quotas.

The review files intentionally contain no predicted labels. They contain only stable identity,
platform/language metadata, past conversation history, the current message, and blank review
columns. They use an Excel-compatible UTF-8 encoding and escape leading spreadsheet formula
characters. They contain assessment text and therefore remain ignored by Git.

## Human annotation procedure

1. Review `docs/annotation-guide.md` before starting. Use only the displayed past history and
   current message.
2. In the calibration CSV, fill `gold_intent` with exactly one of `refund request`, `complaint`,
   `order inquiry`, `compliment`, or `spam`.
3. Fill `gold_is_urgent` with `true` or `false`. Urgency is independent of intent; never enter
   `urgent escalation` as an intent.
4. Set `reviewer_status` to `reviewed`. Use `adjudicated` after a second reviewer resolves an
   uncertain or disputed row. Put short rationale or evidence in `reviewer_notes` when useful.
5. Do not change, remove, reorder, or duplicate evaluation/message IDs.
6. Score calibration. Record any guide clarification and decide whether to accept the existing
   classifier. Freeze that decision and the annotation guide before annotating held-out.
7. Annotate held-out without opening the prediction manifest, then score it once. Use held-out
   results for final reporting, not additional tuning.

## Commands and outputs

Calibration scoring:

```bash
uv run triage score-evaluation \
  --review-csv outputs/evaluation/calibration-review.csv \
  --split calibration \
  --output outputs/evaluation/calibration-report.json
```

Held-out scoring after freeze:

```bash
uv run triage score-evaluation \
  --review-csv outputs/evaluation/heldout-review.csv \
  --split heldout \
  --output outputs/evaluation/heldout-report.json
```

Each command refuses to score unless every expected row has a valid gold intent, urgency flag, and
review status. A successful command writes a JSON report and a neighboring `*-errors.csv` with the
misrouted cases. Metrics include routing and primary-intent accuracy, macro-F1, per-label
precision/recall/F1, confusion matrices, urgency precision/recall/F1, and population-weighted
versions appropriate for the stratified design.

At present, attempting calibration scoring correctly fails with 200 incomplete rows. This is an
evaluation-readiness result, not a quality result: human annotation is the remaining prerequisite.
