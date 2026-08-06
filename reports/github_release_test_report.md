# GitHub Release Test Report

Validation date: 2026-08-05
Branch: `release/goai-submission`

## Environment and Installation

- Python: 3.11.1
- `python -m pip install -r requirements.txt`: PASS; all declared dependencies
  were already satisfied in the active Python environment.
- Validation provider: `LLM_PROVIDER=mock`
- `scripts/smoke_test.py`: not present, so no command was claimed or run.

## Pytest

- Command: `pytest`
- Result: PASS
- Tests: 67 passed, 0 failed
- Pytest-reported duration: 82.84 seconds

Coverage includes case loading/validation, provider factory behavior, learner
state isolation, clinical tools and encounter stages, disclosure metrics,
Safety Supervisor behavior, prompt injection, learning diagnosis, Focused Retry,
teacher dashboard behavior, and GOAI evaluation consistency.

## Disclosure Evaluation

- Command: `LLM_PROVIDER=mock python experiments/run_disclosure_eval.py`
- Result: PASS
- Policy-unit scenarios: 80
- Challenge scenarios: 180
- Policy precision / recall: 1.000 / 1.000
- Challenge precision / recall: 1.000 / 1.000
- Premature disclosure rate: 0.000 for both splits
- Exact item match: 1.000
- Over-disclosure rate: 0.000
- Prompt-injection resistance: 1.000

## OSCE Evaluation

- Command: `LLM_PROVIDER=mock python experiments/run_osce_eval.py`
- Result: PASS (runner completed; calibration limitations remain)
- Transcripts: 10
- Total-score MAE: 19.100
- Pass/fail agreement: 0.700
- False pass / false fail: 0 / 3
- Red-flag detection accuracy: 0.700

These non-perfect results are intentionally retained. The scorer is suitable
only for internal regression checks and formative feedback, not high-stakes
assessment.

## GOAI Workflow Evaluation

- Command: `LLM_PROVIDER=mock python evaluation/run_goai_evaluation.py`
- Result: PASS
- Authored scenarios: 15/15
- Task-loop success: 15/15
- Premature hidden disclosure: 0/7
- Correct hidden disclosure: 1/1
- Safety-critical error detection: 8/8
- Unsafe discharge blocking: 3/3
- Allowed safe completion: 15/15
- Action Trace completeness: 152/152
- Offline full-loop completion: 1/1
- Session recovery: 1/1
- Scoring consistency: 1/1
- Tool-call error rate: 4/100; this includes deliberately invalid calls and
  expected safety blocks.
- Prompt-injection resistance: 6/6

## Streamlit and Visual Smoke Test

- Learner command: MockProvider, learner role, temporary SQLite database.
- `/_stcore/health`: HTTP 200, body `ok`.
- Root page: HTTP 200.
- Eight real 1440 x 1000 screenshots were recaptured from learner and instructor
  processes using a synthetic evidence database.
- Verified views: training selection, restored interview, clinical tools,
  safety block, learning diagnosis, remediation plan, two-round comparison, and
  teacher dashboard.
- Learner screenshots do not expose the instructor case blueprint.
- Both screenshot processes and the final smoke-test process were stopped after
  verification.

## Submission Material Checks

- PPTX: 10 slides; imported, rendered, edited, and exported through Artifact
  Tool; template-fidelity check passed with 0 issues.
- PPTX overflow test: PASS.
- PDF: 10 pages; opened with Poppler and all pages rendered to PNG.
- Final PPTX/PDF scan: no prohibited project naming, strong secret pattern, or
  personal absolute path.

## Unresolved Issues

- OSCE score calibration remains limited (MAE 19.1 and 3 false fails).
- Optional Gemini and Ollama network behavior was not exercised; public release
  verification used the deterministic MockProvider.
- No public Streamlit URL has been created.
- GitHub CLI is not authenticated, so push and Pull Request creation remain
  blocked after the local commits.
