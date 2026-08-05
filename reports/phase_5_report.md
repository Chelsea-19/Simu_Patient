# Phase 5 Report

## Status

PASS

SimuPatient now provides a lightweight, role-gated teacher Dashboard and an instructor-facing YAML
case validator without adding an account system or changing the learner workflow. Teachers can
filter local records by `learner_id`, inspect session-level scores, dimensions, Trace, safety events,
hints, and retry comparison, then download Markdown or JSON reports. All 20 existing case templates
remain compatible and can be validated with a learner-safe preview.

## Goals

- Provide a lightweight teacher view over complete structured learning records.
- Show case, total/dimension scores, Action Trace, safety events, hints, and two-round comparison.
- Export human-readable Markdown and structured JSON reports.
- Validate raw YAML, Pydantic Schema, hidden disclosure rules, safety rules, and learner preview.
- Document case authoring, Schema, tool contracts, and teacher workflow for reuse.
- Preserve learner hidden-state isolation and all existing cases.

## Completed Work

- Added `TeacherDashboard`, `TeacherTrainingRecord`, `CaseTemplateValidationResult`, and structured
  validation issue schemas.
- Added ordered training-session repository queries for all local learners and individual
  `learner_id` values.
- Implemented `TeacherDashboardService` with server-side `APP_ROLE=instructor` enforcement.
- Aggregated session metadata, case, stage, formative total, nine dimension scores, full Action
  Trace, Safety Supervisor events, hints, simulated time, retry linkage, and progress report.
- Added Markdown and JSON teacher report export respecting the selected learner filter.
- Implemented `CaseTemplateValidationService` with instructor-role enforcement.
- Added template listing, raw YAML parsing, required-field detection, strict Pydantic validation,
  hidden reveal-condition checks, initial-view leak detection, safety critical-test checks, required
  safety-rule component checks, and learner-safe preview generation.
- Added Markdown and JSON validation exports.
- Kept warnings separate from errors: missing case-specific safety rules warn but do not invalidate a
  structurally compatible non-acute case.
- Expanded the existing instructor tab rather than introducing accounts or a separate application.
- Preserved the original full case blueprint, rubric, learner Trace, unlock history, and scoring
  evidence review.
- Added Dashboard filters, session table, dimension table, Trace expander, safety/hint metrics,
  first/second comparison, and report downloads to Streamlit.
- Added YAML template selection, validation action, finding table, learner preview, and validation
  downloads to Streamlit.
- Kept learner role as default and blocked all Dashboard/validator services in learner mode.
- Added the four requested open-template documents.

## Files Added

- `app/schemas/teacher.py`
- `app/services/teacher_dashboard_service.py`
- `app/services/case_template_validation_service.py`
- `docs/case_authoring_guide.md`
- `docs/case_schema.md`
- `docs/tool_interface.md`
- `docs/teacher_workflow.md`
- `tests/test_teacher_dashboard.py`
- `tests/test_case_template_validator.py`
- `reports/phase_5_report.md`

## Files Modified

- `app/repositories/training_repository.py`
- `app/streamlit_services.py`
- `streamlit_app.py`

The disclosure and OSCE result artifacts were regenerated; their reported metrics remained
unchanged.

## Commands Executed

```text
python -m compileall -q app streamlit_app.py tests
pytest -q tests/test_learner_state_isolation.py::test_instructor_streamlit_role_exposes_controlled_review_tab tests/test_learner_state_isolation.py::test_learner_streamlit_state_and_reset_do_not_carry_hidden_state tests/test_learning_diagnosis.py::test_streamlit_resume_displays_learning_profile_and_retry_action
pytest -q tests/test_teacher_dashboard.py tests/test_case_template_validator.py
pytest -q tests/test_teacher_dashboard.py::test_instructor_streamlit_exposes_dashboard_exports_and_validator
pytest -q
$env:LLM_PROVIDER='mock'; python experiments/run_disclosure_eval.py
$env:LLM_PROVIDER='mock'; python experiments/run_osce_eval.py
git diff --check
```

An AppTest inspection probe also queried Streamlit's `download_button` element collection and
confirmed the two teacher report downloads. It used a temporary SQLite database, explicitly disposed
the engine, and exited 0.

## Test Results

### Phase 5 focused tests

- Final result: 7 passed in 28.2 seconds.
- Covered two-round teacher records, nine dimension scores, full Trace, safety events, hints,
  progress comparison, Markdown/JSON exports, learner-role rejection, instructor UI, validation UI,
  hidden preview isolation, invalid-template findings, and all-existing-template compatibility.

### Full pytest suite

- Initial Phase 5 full result: 61 passed in 100.6 seconds.
- Final result after the expanded validation UI assertion: 61 passed in 86.7 seconds.
- Exit code: 0.

### Regression fixes during verification

- The first instructor AppTest found six JSON-rendered elements instead of the existing controlled
  count of five. Cause: the new safety-event summary list was rendered by `st.write` as JSON.
  Resolution: render the summary as text while retaining complete structured events in Trace and
  exports. The original instructor isolation test then passed.
- The first new UI export assertion looked for download controls in AppTest's normal `button`
  collection. Streamlit exposes them as `download_button` elements. The test was corrected to query
  the actual control type; no production fix was required.

### Disclosure evaluation

- Exit code: 0.
- policy unit precision / recall: 1.000 / 1.000 across 80 scenarios.
- policy unit premature disclosure rate: 0.000.
- challenge precision / recall: 1.000 / 1.000 across 180 scenarios.
- challenge premature disclosure rate: 0.000.
- exact-item match: 1.000.
- over-disclosure rate: 0.000.
- prompt-injection resistance: 1.000.
- Result: no regression from Phases 0-4.

### OSCE evaluation

- Exit code: 0.
- transcripts: 10.
- total score MAE: 19.100.
- pass/fail agreement: 0.700.
- false pass / false fail: 0 / 3.
- red-flag detection accuracy: 0.700.
- Result: unchanged from Phases 0-4 and still an internal formative benchmark only.

### Static/runtime checks

- Python compilation: exit code 0.
- `git diff --check`: exit code 0; only Windows LF-to-CRLF notices were emitted.
- Streamlit instructor and learner AppTests: no final exceptions.

## Demo Evidence

Teacher Dashboard integration test:

- created an initial chest-pain session for local learner `teacher-demo-learner`;
- recorded a Level 1 hint;
- completed without ECG under an urgent monitored plan, leaving
  `critical_ecg_not_reviewed` as a traceable safety gap;
- generated and persisted all nine dimension scores;
- started a fresh-patient Focused Retry;
- completed the retry with ECG and a focused risk history;
- Dashboard returned two ordered records;
- first record contained the complete assessment Trace, hint `[1]`, and ECG safety event;
- second record linked to the first and contained a progress report resolving the ECG omission;
- Markdown export contained the session, dimension section, Action Trace, and first/second section;
- JSON export contained both records and the non-causal progress interpretation.

Template validator evidence:

- listed exactly 20 existing YAML templates;
- all 20 returned `valid=true` under the current strict Schema;
- `chest_pain_001` had no Schema error, no hidden-rule error, and no safety-rule error;
- chest-pain learner preview contained no cocaine fact, red-flag answer, or scoring rubric;
- `hypertension_followup_001` remained valid and reported the expected
  `safety_rules_not_configured` warning as the non-acute extensibility example;
- an intentionally invalid temporary author template reported missing `demographics`, missing
  `scoring_rubric`, visible hidden-fact leakage, and missing safety configuration;
- validation Markdown and JSON exports were parsed and checked.

Streamlit AppTest evidence:

- instructor tab retained the original five controlled JSON review elements;
- Teacher Dashboard and YAML Case Template Validator headers rendered;
- teacher Markdown and JSON download controls rendered;
- clicking **Validate YAML Template** produced a valid result in session state;
- validation Markdown and JSON download controls then rendered;
- learner workflow and learner session isolation tests continued to pass.

## Known Issues

- `APP_ROLE=instructor` is an environment-level Demo gate, not user authentication or authorization.
- Teacher reports may contain learner inputs and legitimately unlocked sensitive simulation facts;
  institutional privacy and retention controls are not implemented.
- YAML validation proves structure and configured consistency, not clinical correctness.
- Hidden-rule analysis checks explicit authored patterns and initial-view leakage; it is not a general
  semantic theorem prover.
- Safety-rule warnings are intentionally non-blocking for non-acute compatible cases.
- The Dashboard reads all local SQLite records into memory, appropriate for the competition Demo but
  not a large cohort.
- Markdown Action Trace tables summarize structured fields; JSON remains the lossless export.
- No additional case was created. Existing `hypertension_followup_001` is used as the one non-acute
  extensibility example.

## Risks

- Deploying instructor mode publicly without authentication would expose hidden cases and learner
  traces.
- Template authors can still enter medically incorrect but structurally valid facts; clinician or
  instructor review remains mandatory.
- Exported files can leave the application's local access boundary and need secure handling.
- Adding new YAML fields requires synchronized Schema, validator, documentation, and regression
  tests.
- Competition materials must continue labeling scores as formative and comparisons as individual
  Demo performance, not validated examination or educational-effect evidence.

## Next Phase Inputs

- Role-gated local Teacher Dashboard with learner/session filtering.
- Full Trace, safety, hint, dimension, and progress visibility.
- Markdown and JSON teacher exports.
- Instructor YAML Schema/hidden/safety validator with learner preview.
- Markdown and JSON validation exports.
- Open authoring, Schema, tool, and workflow documentation.
- Verified compatibility across all 20 existing templates.
- Stable 61-test suite and unchanged disclosure/OSCE benchmarks.

Phase 5 is complete. Stop and wait for `继续 Phase 6`.
