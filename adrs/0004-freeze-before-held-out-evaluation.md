# Freeze the triage pipeline before held-out evaluation

**Status: Design retained; evaluation not executed in the final submission.**

The designed 1,000-message evaluation workflow splits 200 calibration messages from 800 held-out test messages. If executed, rules, prompts, model choice, and routing thresholds may be improved using only calibration labels; the pipeline must be frozen before evaluating the held-out set so reported quality reflects generalization rather than tuning.

The sampling and scoring workflow remains implemented and tested, but the final submission does not include human annotations, held-out metrics, or calibrated-confidence claims.
