# Phase 6 Report

## Status

PASS

## Goals

- Execute 15 authored GOAI workflow scenarios with MockProvider and persisted Action Trace.
- Calculate the requested competition metrics from real scenario counters and logs.
- Retain the original disclosure and OSCE benchmark results, including non-perfect results.
- Polish the learner prototype so the core workflow is readable without raw internal JSON.
- Verify local no-API deployment and document Streamlit Community Cloud deployment.
- Capture real learner and instructor prototype evidence.

## Completed Work

- Added `evaluation/run_goai_evaluation.py`, which creates an isolated temporary SQLite database,
  runs all 15 scenarios through the real services/repositories, writes per-scenario traces, and
  calculates metrics from explicit numerators and denominators.
- Added JSON, CSV, and Markdown evaluation outputs and scenario-level result files.
- Retained the original disclosure benchmark and the original OSCE MAE, false-fail, red-flag, and
  missed-item results in the competition report.
- Renamed the learner workflow tabs to Choose Training, Clinical Encounter, and Formative Feedback.
- Replaced raw learner tool/feedback JSON views with readable evidence tables, formative feedback
  lists, a learner-safe report download, and a persistent safety-block banner.
- Restored the first/second-round comparison when a completed Focused Retry session is resumed.
- Added local, no-API, Gemini-optional, and Streamlit Community Cloud deployment instructions.
- Started the learner and instructor prototype against a real local SQLite evidence database,
  checked `/_stcore/health`, and captured the eight requested screenshots at 1440 x 1000.
- Added regression tests for scenario coverage, trace counts, calculated metric counts, CSV/JSON
  agreement, retained legacy limitations, screenshot evidence, and deployment commands.

## Files Added

- `evaluation/run_goai_evaluation.py`
- `evaluation/goai_evaluation_report.md`
- `evaluation/goai_metrics.json`
- `evaluation/goai_metrics.csv`
- `evaluation/results/goai_scenarios.json`
- `evaluation/results/goai_scenarios.csv`
- `tests/test_goai_evaluation.py`
- `docs/deployment.md`
- `assets/screenshots/README.md`
- `assets/screenshots/01_learning_goal_selection.png`
- `assets/screenshots/02_patient_interview.png`
- `assets/screenshots/03_clinical_tool_call.png`
- `assets/screenshots/04_safety_block.png`
- `assets/screenshots/05_learning_diagnosis.png`
- `assets/screenshots/06_personalized_retry.png`
- `assets/screenshots/07_two_round_comparison.png`
- `assets/screenshots/08_teacher_dashboard.png`
- `assets/demo_traces/01_correct_complete.json` through
  `assets/demo_traces/15_session_recovery.json`
- `reports/phase_6_report.md`

## Files Modified

- `streamlit_app.py`
- `README.md`

## Commands Executed

- `python evaluation/run_goai_evaluation.py`
- `LLM_PROVIDER=mock python experiments/run_disclosure_eval.py`
- `LLM_PROVIDER=mock python experiments/run_osce_eval.py`
- `pytest -q tests/test_goai_evaluation.py tests/test_learner_state_isolation.py`
- `pytest -q tests/test_goai_evaluation.py`
- `pytest -q`
- `python -m compileall -q app evaluation streamlit_app.py`
- `git diff --check`
- Learner Streamlit on `127.0.0.1:8511` with `LLM_PROVIDER=mock`, `APP_ROLE=learner`, and a
  dedicated SQLite evidence database.
- Instructor Streamlit on `127.0.0.1:8512` with `LLM_PROVIDER=mock`, `APP_ROLE=instructor`, and the
  same evidence database.
- HTTP requests to `/_stcore/health` for both role-specific processes.
- Headless Chrome capture and visual inspection of all eight requested prototype states.

## Test Results

- Initial combined Phase 6/isolation run: **17 passed, 1 failed**. The failure was the new test's
  exact comparison of the deliberately rounded metric `0.333333` with `1/3`; the assertion was
  corrected to the evaluator's documented six-decimal tolerance.
- Full pytest suite: **67 passed** in **106.1 seconds**.
- Focused Phase 6 evaluation tests after the one assertion-tolerance correction: **6 passed**.
- Python compile check: PASS.
- `git diff --check`: PASS; only Windows line-ending conversion warnings were emitted.
- Streamlit learner health endpoint: HTTP 200, body `ok`.
- Streamlit instructor health endpoint: HTTP 200, body `ok`.
- Disclosure benchmark:
  - policy scenarios: 80
  - challenge scenarios: 180
  - challenge precision / recall: 1.000 / 1.000
  - premature disclosure rate: 0.000
  - prompt-injection resistance: 1.000
- Existing OSCE benchmark:
  - transcripts: 10
  - total-score MAE: 19.100
  - pass/fail agreement: 0.700
  - false pass / false fail: 0 / 3
  - red-flag detection accuracy: 0.700
  - missed-item detection accuracy retained in the report: 0.432

## Demo Evidence

- GOAI scenarios passed: 15/15 authored outcomes.
- Task-loop scenario success: 15/15.
- Premature hidden-information disclosure: 0/7 negative probes.
- Correct hidden-information disclosure: 1/1 direct opportunity.
- Safety-critical findings detected: 8/8.
- Unsafe discharges blocked: 3/3.
- Safe completion attempts allowed: 15/15.
- Action Trace completeness: 152/152 expected service actions.
- No-API adaptive workflow completion: 1/1 with socket access disabled.
- Session recovery: 1/1 persisted state and trace comparison.
- Scoring consistency: 1/1 repeated deterministic baseline comparison.
- Tool-call error rate: 4/100 (4%); this includes deliberately invalid calls and expected safety
  blocks.
- Prompt-injection resistance: 6/6 authored attacks.
- Real screenshots: 8/8 requested views, visually inspected after capture.

## Known Issues

- The legacy OSCE scorer remains inaccurate enough that it must not be used for high-stakes
  assessment; its MAE, three false fails, and low missed-item accuracy are intentionally retained.
- The 15 GOAI scenarios are authored deterministic software tests, not an independent clinical or
  educational validation dataset.
- A successful task-loop scenario includes an expected safety block when blocking is the correct
  system outcome; it does not mean every encounter reached assessment.
- `APP_ROLE=instructor` is an environment-level Demo gate, not production authentication.
- SQLite persistence on Streamlit Community Cloud is ephemeral.
- No public Community Cloud URL was provisioned in this phase; the local learner/instructor
  prototype and deployment runbook were verified.

## Risks

- MockProvider reproducibility does not establish the behavior of optional Gemini free-text output.
- The screenshot evidence reflects one local MockProvider run and should not be presented as proof
  of clinical validity or educational efficacy.
- A second-round score increase may reflect repetition or familiarity and is reported only as an
  individual Demo comparison.
- Production deployment would require identity, authorization, durable storage, privacy review,
  audit retention, and institution-approved clinical content governance.

## Next Phase Inputs

- Use `evaluation/goai_evaluation_report.md`, `evaluation/goai_metrics.json`, the 15 trace files,
  and the eight screenshots as the evidence basis for Phase 7 competition materials.
- Present legacy OSCE limitations next to the stronger deterministic workflow/safety results.
- Keep all claims within formative education, internal software evaluation, and individual Demo
  comparison boundaries.
