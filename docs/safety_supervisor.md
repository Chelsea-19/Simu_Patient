# Safety Supervisor

## Purpose and boundary

The Safety Supervisor is a deterministic training safeguard for SimuPatient. It reviews the
learner's recorded Action Trace and structured submissions before formative assessment. It is not
a validated clinical decision-support system, does not replace an OSCE examiner, and must not be
used for real-patient diagnosis or treatment.

## Trusted inputs

The supervisor reads only:

- the persisted `EncounterState`;
- case-authored safety vocabulary in `case_templates/chest_pain_001.yaml`;
- deterministic tool-use records such as `vital_signs` and `ecg`;
- learner-authored differential diagnoses and management fields.

The LLM does not select rules, change tool results, set the safety decision, or write the final
score. Case facts remain in YAML; Python applies the rules.

## Output contract

`app.schemas.safety.SafetyReview` exposes:

```json
{
  "risk_level": "high",
  "decision": "block_completion",
  "triggered_rules": [],
  "missing_critical_actions": [],
  "learner_feedback": "",
  "recommended_reflection_questions": []
}
```

Rule identifiers and messages are learner-safe. They do not expose hidden history, the scoring
rubric, ground-truth diagnosis, or unreleased investigation results.

## Chest-pain rules

The configured review checks whether the learner:

- considered a time-critical cause in the differential;
- asked about pain radiation;
- assessed cardiovascular risk factors;
- asked directly about recreational drugs or stimulants;
- reviewed vital signs;
- reviewed the configured critical test, ECG;
- selected an unsafe home or outpatient disposition;
- supplied deterioration or emergency-return advice;
- supplied urgent escalation, referral, admission, or monitored care.

These checks are independent evidence flags. A single history omission does not automatically
block completion.

## Blocking policy

| Case risk | Disposition | ECG reviewed | Urgent escalation | Decision |
|---|---|---:|---:|---|
| High | Home/outpatient | No | Any | Block |
| High | Home/outpatient | Yes | No | Block |
| High | Urgent admission/monitored care | Any | Yes | Allow; record remaining gaps |
| High | Non-home safe plan | Yes | Yes | Allow; record remaining gaps |

The current Phase 3 rule intentionally blocks only the safety-critical combination of a high-risk
case, low-acuity disposition, and either missing ECG review or missing urgent escalation. This
keeps formative history gaps visible without treating every omission as a hard stop.

When blocked, the encounter stays in `MANAGEMENT`, sets `assessment_status` to
`blocked_by_safety`, and returns reflection prompts. The learner can order an allowed missing test,
revise the management plan, and call `finish_encounter()` again. A passing review advances through
`SAFETY_REVIEW` to `ASSESSMENT`.

## Trace and UI behavior

Every completion attempt writes a Trace event. A blocked event includes:

- `structured_action.status = blocked`;
- `structured_action.decision = block_completion`;
- the same rule identifiers in `safety_event` and the structured tool result;
- the learner-safe feedback and reflection questions;
- no hidden case state.

The Streamlit workbench displays the structured review and reflection prompts. It only starts
assessment after `finish_encounter()` returns `success`.

## Prompt-injection boundary

Learner chat text is untrusted input. Phase 3 adds three layers:

1. The patient prompt receives no unreleased hidden facts or instructor rubric.
2. Known role-redefinition and control attempts receive a fixed, in-role patient response and are
   still recorded as learner actions.
3. Assessment prompts place the transcript behind an explicit system boundary: transcript text is
   evidence, never an instruction.

Clinical tools, safety decisions, encounter stages, and persisted scores remain Python/database
operations. Chat instructions cannot invoke or mutate them.

Covered injection attempts include requests to reveal hidden or standard answers, mark tests
normal, award full marks, disable blocking, and switch to a system-administrator role.

## Known limitations

- Keyword matching supports the English competition demo vocabulary and is not a complete semantic
  clinical-risk model.
- The hard-block combination is intentionally narrow for Phase 3 and needs author review before a
  new case receives a safety configuration.
- Prompt-pattern matching is defense in depth, not a universal injection detector.
- Safety review is formative software behavior and has not been clinically validated.
