# Learning Diagnosis and Focused Retry

## Educational purpose

Phase 4 turns a completed structured encounter into a session-level formative learning profile,
then uses its weakest dimensions to create a bounded second practice task. The output supports
learner reflection and instructor review. It is not a validated OSCE grade and does not establish
clinical competence or a causal teaching effect.

## Evidence pipeline

```text
YAML case configuration
        +
Deterministic checklist coverage
        +
Structured Encounter State and Action Trace
        +
Bounded LLM qualitative adjustment (-5 to +5)
        ↓
Nine-dimension Learning Profile
        ↓
Personalized Remediation Plan
        ↓
Focused Retry with a fresh patient state
        ↓
Individual two-round comparison
```

Case facts and clinical tool results remain YAML-controlled. Python determines topic coverage,
tool-use evidence, safety status, time/hint penalties, dimension baselines, ranking, remediation
actions, and progress deltas. The LLM can adjust only communication, empathy, and complex-reasoning
language quality by at most five points per applicable dimension. It cannot change Safety
Supervisor decisions.

## Nine dimensions

Every `DimensionDiagnosis` contains:

- `score`;
- `deterministic_score`;
- `qualitative_adjustment`;
- `scoring_evidence`;
- `strengths`;
- `omissions`;
- `risks`;
- `recommended_practice`.

The dimensions are:

1. `history_taking`: focused chest-pain topic coverage plus recorded history turns.
2. `communication`: observable learner-to-patient interaction with bounded language feedback.
3. `clinical_reasoning`: prioritized differential linked to collected structured evidence.
4. `red_flag_recognition`: time-critical differential and focused red-flag history coverage.
5. `investigation_selection`: vital signs, ECG, and troponin selection from Action Trace.
6. `management_safety`: disposition, urgent escalation, and final deterministic safety state.
7. `empathy`: explicit acknowledgement evidence with bounded language feedback.
8. `closure_and_safety_netting`: deterioration advice and escalation language.
9. `efficiency`: simulated task time, rejected/blocked actions, and hint dependence.

The overall score is the rounded mean of all nine final dimension scores. It is a formative software
score only.

## Repeatability and LLM fallback

Deterministic baselines can be regenerated from the persisted Encounter State and append-only Trace.
LLM qualitative adjustments use a fixed conversion and are clamped to `-5..+5`. If checklist or
qualitative model calls fail, the existing assessment engine supplies template defaults and the
learning profile remains available; applicable qualitative adjustments become zero.

Each session's complete profile and remediation plan is persisted in `learning_diagnosis`, keyed by
`session_id`. The assessment-completion Trace event stores the overall score, all nine dimension
scores, and the learning-profile session identifier.

## Personalized remediation

The planner selects one to three lowest dimensions, always selecting at least one. It produces:

```json
{
  "priority_skills": [],
  "learning_objective": "",
  "recommended_case": "",
  "recommended_difficulty": "",
  "specific_actions_to_practice": [],
  "hint_policy": "",
  "success_criteria": []
}
```

An overall score below 60 recommends foundational difficulty; otherwise the current case difficulty
is retained. Practice actions and criteria are deterministic templates linked to the selected weak
dimensions.

## Focused Retry

`start_focused_retry_logic()` requires a completed source session with a persisted diagnosis. It:

- creates a new patient record from the same YAML case, resetting disclosure and unlocked evidence;
- creates a new encounter linked by `retry_of_session_id`;
- copies the remediation objective, difficulty, and priority skills into the new state;
- marks the encounter as `focused_retry`;
- limits the Streamlit history workbench to six focused turns;
- preserves all normal deterministic tools and safety blocking.

The fresh patient record is important: hidden-information state and prior consultation logs cannot
carry from the first attempt into the retry.

## Three-level coaching

- Level 1 is reflective and asks the learner to identify an unresolved risk category.
- Level 2 is directional and points to pain characteristics, cardiovascular risks, and stimulant
  use.
- Level 3 is instructional and names the usual focused chest-pain history domains.

Every hint is stored in Encounter State and Action Trace. Efficiency deductions are deterministic:
Level 1 costs 2 points, Level 2 costs 5, and Level 3 costs 10. This is a dependence/efficiency signal,
not a punishment or clinical grade.

## Progress report

The comparison service verifies that the second session is a retry of the first. It reports:

- first and second total scores;
- all nine dimension deltas;
- first/second, resolved, and new safety-critical omissions;
- hint counts and delta;
- simulated completion times and delta;
- up to three remaining dimensions below 75.

Every report includes the interpretation:

> 当前 Demo 中的个体训练表现对比；分数变化不能解释为真实教学效果证明。

An increase may reflect familiarity, hint use, case repetition, or other Demo-specific factors. It
must not be described as proof of learning effectiveness.

## Known limitations

- History-language matching is currently optimized for the English chest-pain Demo; bilingual
  aliases require case-author review and tests.
- The score weights are prototype formative rules, not psychometrically calibrated OSCE weights.
- A Focused Retry uses the same case facts, so recall and familiarity can contribute to improvement.
- The six-turn limit is enforced in the Streamlit workbench; direct service callers are expected to
  respect the state field.
- Communication and empathy evidence is intentionally conservative without a reliable LLM signal.
