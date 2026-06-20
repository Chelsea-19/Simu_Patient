# OSCE Evaluation Summary

This deterministic internal benchmark compares a transparent rule-based rubric scorer against hand-authored reference transcripts. It is not clinical validation.

## Metrics

- total_transcripts: 10
- total_score_mae: 19.100
- score_correlation: 0.970
- pass_fail_agreement: 0.700
- false_pass_count: 0
- false_fail_count: 3
- red_flag_detection_accuracy: 0.700
- missed_item_detection_accuracy: 0.432

## Pass/Fail Confusion Matrix

- true_pass: 2
- true_fail: 5
- false_pass: 0
- false_fail: 3

## Dimension MAE

- history_taking: 4.600
- communication: 3.300
- clinical_reasoning: 5.200
- empathy: 1.700
- closure: 2.800
- safety_red_flags: 2.600

## Interpretation

The scorer is deterministic and explainable: it rewards coverage of expected questions, red-flag handling, empathy, closure, and reasoning language. High correlation with reference totals means the ordering may be consistent, while MAE and false pass/fail counts show calibration error that still needs review.

## Limitations

- Reference transcripts and rubric scores are authored samples, not a validated clinical assessment set.
- Keyword and synonym matching can miss valid paraphrases and can over-credit superficial mentions.
- The benchmark should be used for regression tracking and scorer transparency, not for claims about real-world OSCE validity.
