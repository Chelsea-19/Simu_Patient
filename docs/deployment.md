# Deployment and Demo Runbook

## Supported deployment targets

- Local Streamlit on a normal laptop.
- Streamlit Community Cloud.
- Deterministic MockProvider with no API key or network model call.
- Optional GeminiProvider with a configured API key.

The application is one Streamlit process backed by SQLModel and SQLite. FastAPI, Docker, React, and
an external database are not required for the competition prototype.

## Local no-API Demo

From the repository root:

```bash
pip install -r requirements.txt
LLM_PROVIDER=mock streamlit run streamlit_app.py
```

Windows PowerShell equivalent:

```powershell
pip install -r requirements.txt
$env:LLM_PROVIDER = "mock"
streamlit run streamlit_app.py
```

Open the printed local URL, normally `http://localhost:8501`. The default role is `learner`; no
hidden case blueprint or teacher Dashboard is exposed.

## Instructor Demo

Use instructor mode only in a controlled local environment:

```powershell
$env:LLM_PROVIDER = "mock"
$env:APP_ROLE = "instructor"
streamlit run streamlit_app.py
```

`APP_ROLE=instructor` is an environment-level competition Demo gate, not authentication. Do not
publish instructor mode to an untrusted audience.

## Optional Gemini

Linux/macOS:

```bash
LLM_PROVIDER=gemini GEMINI_API_KEY=your-key streamlit run streamlit_app.py
```

PowerShell:

```powershell
$env:LLM_PROVIDER = "gemini"
$env:GEMINI_API_KEY = "your-key"
$env:GEMINI_MODEL = "gemini-2.5-flash-lite"
streamlit run streamlit_app.py
```

Never commit `.streamlit/secrets.toml` or real API keys. Gemini is optional; all core competition
flows and evaluation scenarios run with MockProvider.

## Streamlit Community Cloud

1. Push the repository branch to GitHub.
2. Create a Streamlit Community Cloud app.
3. Set the entry point to `streamlit_app.py`.
4. Use Python 3.11 or another version compatible with `requirements.txt`.
5. Add only the required secrets.

Recommended deterministic learner Demo secrets:

```toml
LLM_PROVIDER = "mock"
APP_ROLE = "learner"
```

Optional Gemini learner Demo:

```toml
LLM_PROVIDER = "gemini"
APP_ROLE = "learner"
GEMINI_API_KEY = "your-key"
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

SQLite files on Community Cloud are ephemeral and can reset when the application sleeps or is
redeployed. This is acceptable for the competition Demo, not for durable learner records.

## Verification

Run automated tests and evaluations before deployment:

```bash
pytest
LLM_PROVIDER=mock python experiments/run_disclosure_eval.py
LLM_PROVIDER=mock python experiments/run_osce_eval.py
python evaluation/run_goai_evaluation.py
```

Expected generated competition artifacts:

- `evaluation/goai_metrics.json`
- `evaluation/goai_metrics.csv`
- `evaluation/goai_evaluation_report.md`
- `evaluation/results/goai_scenarios.json`
- `assets/demo_traces/*.json`

For a process health check, start Streamlit headlessly and request `/_stcore/health`. A healthy app
returns HTTP 200 and `ok`.

## Troubleshooting

### App stops with a Gemini configuration error

Set `LLM_PROVIDER=mock`, or configure both `GEMINI_API_KEY` and `GEMINI_MODEL`.

### SQLite is locked

Stop duplicate Streamlit processes that use the same database. For automated checks, use a unique
temporary `DATABASE_URL` and dispose the SQLModel engine before deleting the file on Windows.

### A clinical tool says “not configured”

The selected YAML case has no authored result for that tool. Use the chest-pain Demo or add and
validate an instructor-reviewed result in YAML. The system intentionally does not invent one.

### Teacher tab is missing

The default is learner mode. Set `APP_ROLE=instructor` before starting the process and use that mode
only for controlled teacher review.

## Deployment boundaries

- Educational simulation only; not medical advice or clinical decision support.
- Formative feedback only; not a validated OSCE or high-stakes assessment.
- No production identity, authorization, encryption-at-rest, or institutional retention workflow.
- Do not claim that second-round score changes prove educational effectiveness.
- Clinician/instructor review is required for every case and safety configuration.
