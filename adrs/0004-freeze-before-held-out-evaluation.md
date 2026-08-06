# Freeze the triage pipeline before held-out evaluation

The 1,000-message Evaluation Set is split into 200 calibration messages and 800 held-out test messages. Rules, prompts, model choice, and routing thresholds may be improved using only calibration labels; the pipeline is frozen before evaluating the held-out set so reported quality reflects generalization rather than tuning.
