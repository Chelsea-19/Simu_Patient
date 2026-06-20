# Disclosure Evaluation Summary

This report separates simple policy-unit checks from a richer behavioral challenge split.

## Policy Unit Test

- total_scenarios: 80
- policy_unit_precision: 1.000
- policy_unit_recall: 1.000
- policy_unit_premature_disclosure_rate: 0.000

Perfect policy-unit scores only mean the controlled policy examples passed. They do not imply real-world disclosure performance.

## Behavioral Challenge Test

- total_scenarios: 180
- challenge_precision: 1.000
- challenge_recall: 1.000
- challenge_premature_disclosure_rate: 0.000
- challenge_exact_item_match_rate: 1.000
- over_disclosure_rate: 0.000
- prompt_injection_resistance_rate: 1.000

## Interpretation

The policy-unit split checks basic allow/deny behavior. The behavioral challenge split probes indirect, ambiguous, leading, compound, and prompt-injection-style questions using deterministic keyword and reveal-condition logic.

## Limitations

- This is a deterministic internal benchmark, not clinical validation.
- The evaluator uses transparent rule-based matching over hidden item text, reveal conditions, and clinically relevant keyword groups.
- Scores should be used for regression tracking and benchmark design feedback, not claims of patient-simulation safety or real-world OSCE validity.
- Challenge prompts are more realistic than the policy-unit checks, but they are still authored test cases rather than independent clinical conversations.
