# Phase 4 Report

## Status

PASS

SimuPatient now generates a persisted nine-dimension learning diagnosis after a structured
encounter, derives a personalized remediation plan from the lowest one to three dimensions, starts
a fresh-state Focused Retry, and compares both attempts. The entire baseline diagnosis, retry, and
comparison path runs with MockProvider; a simulated LLM failure also produces a valid template-based
profile.

## Goals

- Replace single-score feedback with nine traceable learning dimensions.
- Combine deterministic checklist coverage, structured Trace evidence, and bounded qualitative
  feedback.
- Generate a personalized remediation plan from the weakest dimensions.
- Support a focused second attempt without carrying hidden or unlocked state across patients.
- Compare two attempts without claiming causal teaching effectiveness.
- Provide three progressively explicit hints and account for hint dependence.
- Preserve offline operation, Phase 1 state isolation, Phase 3 safety blocking, and old benchmark
  compatibility.

## Completed Work

- Added session-level schemas for `DimensionDiagnosis`, `LearningProfile`,
  `PersonalizedRemediationPlan`, `LearningProgressReport`, and the persisted diagnosis bundle.
- Added all nine required dimensions: history taking, communication, clinical reasoning, red-flag
  recognition, investigation selection, management safety, empathy, closure/safety netting, and
  efficiency.
- Added score, deterministic baseline, bounded qualitative adjustment, evidence, strengths,
  omissions, risks, and recommended practice to every dimension.
- Implemented deterministic evidence extraction from Encounter State and Action Trace, including
  questions, legitimately unlocked hidden-history evidence, differential diagnoses, tools,
  Safety Supervisor flags, management fields, hints, errors, time, and completion state.
- Limited LLM influence to `-5..+5` for communication, empathy, and complex clinical reasoning.
- Kept red-flag, investigation, management-safety, closure, efficiency, and all Safety Supervisor
  decisions deterministic.
- Added a template fallback that yields all nine dimensions and a remediation plan when assessment
  model calls fail.
- Persisted the profile and plan in a `learning_diagnosis` record keyed by encounter `session_id`.
- Added all nine dimension scores and the learning-profile reference to the assessment-completion
  Action Trace score event.
- Ranked the lowest one to three dimensions and generated objective, case, difficulty, targeted
  actions, graduated hint policy, and success criteria.
- Added `focused_retry`, `focus_skills`, and `history_turn_limit` to Encounter State.
- Implemented Focused Retry with a newly created patient from the same YAML case, reset disclosure
  state/evidence/tests/history, six focused history turns, and source linkage via
  `retry_of_session_id`.
- Replaced generic chest-pain hints with reflective Level 1, directional Level 2, and teaching Level
  3 prompts.
- Applied deterministic efficiency costs of 2, 5, and 10 points to Levels 1, 2, and 3.
- Added a progress report containing total scores, nine dimension deltas, safety omissions,
  hints, simulated time, and remaining weak dimensions.
- Added the required caution that the report is only an individual Demo performance comparison.
- Updated Streamlit to display the nine-dimension table, evidence, personalized plan, Focused Retry
  action, focused-turn budget, and second-round comparison.
- Added resume support for persisted learning profiles.

## Files Added

- `app/models/learning.py`
- `app/repositories/learning_repository.py`
- `app/schemas/learning.py`
- `app/services/learning_diagnosis_service.py`
- `docs/learning_diagnosis.md`
- `tests/test_learning_diagnosis.py`
- `tests/test_focused_retry_progress.py`
- `reports/phase_4_report.md`

## Files Modified

- `app/models/__init__.py`
- `app/schemas/assessment.py`
- `app/schemas/encounter.py`
- `app/services/clinical_skill_router.py`
- `app/services/simu_engine.py`
- `app/streamlit_services.py`
- `streamlit_app.py`

The disclosure and OSCE result artifacts were regenerated; their reported metrics were unchanged.

## Commands Executed

```text
python -m compileall -q app streamlit_app.py tests
pytest -q tests/test_service_with_mock_provider.py tests/test_clinical_tools_state_machine.py
pytest -q tests/test_learning_diagnosis.py tests/test_focused_retry_progress.py
pytest -q tests/test_clinical_tools_state_machine.py::test_streamlit_workbench_exposes_state_tools_evidence_and_trace tests/test_clinical_tools_state_machine.py::test_mock_provider_completes_full_encounter_without_network tests/test_prompt_injection.py::test_full_marks_injection_cannot_change_formative_score
pytest -q
$env:LLM_PROVIDER='mock'; python experiments/run_disclosure_eval.py
$env:LLM_PROVIDER='mock'; python experiments/run_osce_eval.py
git diff --check
```

Two standalone two-round MockProvider probes were executed with temporary SQLite databases. The
first printed valid comparison data but exited 1 because Windows still held the database handle
during `TemporaryDirectory` cleanup. The exact temporary database file and directory were then
removed successfully. The corrected probe explicitly disposed the SQLModel engine, printed the
same comparison data, cleaned its temporary directory automatically, and exited 0.

## Test Results

### Phase 4 focused tests

- Final focused result: 5 passed in 31.6 seconds.
- Covered nine-dimension structure and evidence, persisted diagnosis, remediation ranking, all three
  hints and Trace entries, deterministic efficiency deduction, LLM failure fallback, new-patient
  retry state, source linkage, two-round comparison, and Streamlit resume/display/action behavior.

### Full pytest suite

- Final result: 54 passed in 72.6 seconds.
- Exit code: 0.
- Streamlit AppTest exceptions: none.

### Disclosure evaluation

- Exit code: 0.
- policy unit scenarios: 80.
- policy unit precision / recall: 1.000 / 1.000.
- policy unit premature disclosure rate: 0.000.
- challenge scenarios: 180.
- challenge precision / recall: 1.000 / 1.000.
- challenge premature disclosure rate: 0.000.
- challenge exact-item match: 1.000.
- over-disclosure rate: 0.000.
- prompt-injection resistance rate: 1.000.
- Result: no regression from Phases 0-3.

### OSCE evaluation

- Exit code: 0.
- transcripts: 10.
- total score MAE: 19.100.
- pass/fail agreement: 0.700.
- false pass / false fail: 0 / 3.
- red-flag detection accuracy: 0.700.
- Result: unchanged from Phases 0-3. This is an internal formative benchmark, not formal OSCE or
  clinical validation.

### Static/runtime checks

- Python compilation: exit code 0.
- `git diff --check`: exit code 0; Git emitted only Windows LF-to-CRLF notices.
- MockProvider core path remained fully offline.

## Demo Evidence

The corrected standalone Demo used two fresh patient records and the real YAML loader, disclosure
controller, state machine, tools, Safety Supervisor, diagnosis persistence, remediation planner, and
comparison service.

First attempt:

- focused history only asked onset;
- vital signs and troponin requested;
- ECG omitted;
- safe urgent admission and safety-net plan submitted;
- formative learning-profile total: 74;
- simulated completion time: 19 minutes;
- hints used: 0;
- safety-critical gap: `critical_ecg_not_reviewed`.

Focused Retry:

- new patient ID and new session with no carried evidence, tests, questions, or disclosure state;
- retry linked to the first session and configured with the generated priority skills;
- focused question covered symptom characteristics, radiation, associated symptoms,
  cardiovascular risks, stimulant use, and empathy;
- vital signs, ECG, and troponin requested;
- formative learning-profile total: 93;
- simulated completion time: 24 minutes;
- hints used: 0;
- safety-critical gaps: none.

Observed Demo deltas:

- total: +19;
- history taking: +83;
- communication: 0;
- clinical reasoning: +8;
- red-flag recognition: +30;
- investigation selection: +35;
- management safety: 0;
- empathy: +15;
- closure/safety netting: 0;
- efficiency: 0;
- resolved safety omission: `critical_ecg_not_reviewed`;
- time: +5 minutes.

This is only “当前 Demo 中的个体训练表现对比”. The score increase must not be interpreted as proof
of learning effectiveness; it may include repetition, familiarity, and case-specific effects.

## Known Issues

- Chest-pain history matching is currently optimized for English Demo language. Equivalent Chinese
  questions can be under-counted until bilingual aliases are authored and tested.
- Deterministic dimension weights and thresholds are prototype formative rules, not psychometrically
  calibrated examination standards.
- The same case is used for Focused Retry, so memory and familiarity can contribute to apparent
  improvement.
- The six-turn focused-history limit is enforced by the Streamlit workbench; direct internal service
  callers can still submit additional questions.
- Qualitative model feedback is bounded but provider-dependent. A failure returns template output;
  it may be less nuanced for communication and empathy.
- Progress reports compare two recorded attempts only and do not adjust for hint level, case
  familiarity, or statistical uncertainty beyond reporting those values.
- Only the chest-pain Demo has detailed Phase 3 safety configuration and Phase 4 educational scoring
  assumptions.

## Risks

- Expanding language keyword coverage without negation/context tests could inflate checklist scores.
- Changes to Action Trace field semantics require a scoring-version update to preserve auditability.
- A new retry case must create a fresh patient record; reusing the first patient would contaminate
  hidden-information state.
- The learning profile contains learner inputs and unlocked evidence; exports and instructor views
  must continue respecting Phase 1 role isolation.
- Competition materials must use “formative learning diagnosis” and “individual Demo comparison”,
  never validated examination score or proven educational effect.

## Next Phase Inputs

- Persisted session-level nine-dimension Learning Profile.
- Trace-grounded scoring evidence with bounded qualitative adjustments and fallback.
- Deterministic personalized remediation planner.
- Fresh-state Focused Retry linked to the source session.
- Three-level hint system with efficiency accounting.
- Two-round progress report and explicit non-causal interpretation.
- Streamlit learning profile, retry, and comparison views.
- Stable 54-test suite and unchanged disclosure/OSCE benchmarks.

Phase 4 is complete. Stop and wait for `继续 Phase 5`.
