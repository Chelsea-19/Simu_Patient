# Clinical Tool Interface

## Design contract

Clinical tools are deterministic methods on `ClinicalSkillRouter`. They read authored YAML facts,
update the persisted Encounter State, append an Action Trace entry, and return `ToolResult`. They do
not ask the LLM to create clinical facts.

## Common result

```json
{
  "tool_name": "order_ecg",
  "status": "success",
  "evidence_unlocked": [],
  "result": {},
  "time_cost": 5,
  "safety_events": [],
  "learner_message": "",
  "current_stage": "INVESTIGATION"
}
```

`status` is `success`, `error`, or `duplicate`. Unknown or wrong-stage calls return structured errors
and empty evidence. Duplicate deterministic tests return the existing authored result, add no time,
and unlock no duplicate evidence.

## Available tools

### `request_vital_signs(session_id)`

- Reads `case.vital_signs`.
- Available from history taking through clinical reasoning, subject to `unlock_condition`.
- Adds `vital_signs` to `tests_ordered` and unlocks structured evidence.

### `perform_physical_exam(session_id, system)`

- Reads `case.physical_examination[system]`.
- Uses normalized lowercase system names.
- Unknown systems fail safely without inventing findings.

### `order_ecg(session_id)`

- Reads `case.investigations.ecg`.
- Available from examination through management.
- The patient/chat model cannot modify the result.

### `order_lab_test(session_id, test_name)`

- Reads a configured investigation with `kind: lab`.
- Unknown names and non-lab investigations fail safely.

### `submit_differential_diagnosis(session_id, diagnoses)`

- Requires at least one investigation stage to have been reached.
- Deduplicates and trims learner entries.
- Stores the learner's structured list; it does not confirm a final diagnosis.

### `submit_management_plan(session_id, plan)`

- Requires clinical reasoning or management stage.
- Stores non-empty structured fields such as disposition, initial management, and safety net.
- Safety is determined later by the Safety Supervisor.

### `request_hint(session_id, level)`

- Accepts Levels 1, 2, and 3.
- Level 1 is reflective, Level 2 directional, and Level 3 instructional.
- Stores level in Encounter State and Action Trace.
- Phase 4 efficiency deductions are 2, 5, and 10 points respectively.

### `finish_encounter(session_id)`

- Requires a differential and management plan.
- Runs deterministic Safety Supervisor review.
- A blocking result leaves the encounter in `MANAGEMENT` for correction.
- An allowed result advances through `SAFETY_REVIEW` to `ASSESSMENT`.

## Encounter stages

```text
CASE_INTRO
→ HISTORY_TAKING
→ EXAMINATION
→ INVESTIGATION
→ CLINICAL_REASONING
→ MANAGEMENT
→ SAFETY_REVIEW
→ ASSESSMENT
→ REMEDIATION
→ COMPLETED
```

History, examination, and investigation methods permit defined clinically reasonable revisits.
The state machine rejects arbitrary jumps.

## Action Trace contract

Every accepted, rejected, duplicate, hint, safety, and assessment action records:

```text
action_id
session_id
timestamp
stage
natural_language_input
structured_action
tool_name
tool_parameters
result_summary
evidence_unlocked
time_cost
hint_level
safety_event
score_event
```

The assessment-completion `score_event` contains the formative overall score, nine dimension
scores, and the corresponding learning-profile session ID. Instructor exports use this Trace; they
do not reconstruct actions from UI state.

## Focused Retry

A retry creates a new patient and session with:

- `retry_of_session_id`;
- `focused_retry=true`;
- generated `focus_skills`;
- a six-turn focused history budget in Streamlit;
- empty questions, evidence, tools, and hidden disclosure state.

All normal tools, Trace behavior, and Safety Supervisor rules remain active.

## Safety and extension rules

- Never hard-code case results in Streamlit.
- Add authored results to YAML and validate them.
- Do not make a tool return hidden rubric or expected-question fields.
- Keep learner messages reflective; do not reveal the ground-truth diagnosis.
- Treat tool output as simulation evidence, not real medical advice.
- Add tests for success, wrong stage, unknown inputs, duplicates, persistence, Trace, and safety.
