# SimuPatient

SimuPatient is a Streamlit-first clinical training demo for AI standardized patient conversations and OSCE-style feedback.

The active application is a single Streamlit process. It imports the shared service, model, schema, repository, database, and provider layers directly from `app/`.

## Current Architecture

- `streamlit_app.py` is the only active app entry point.
- `app/streamlit_services.py` adapts Streamlit UI events to the service layer.
- `app/services/` contains patient generation, consultation, disclosure, and assessment logic.
- `app/models/`, `app/schemas/`, and `app/repositories/` define the data contracts and persistence layer.
- `app/providers/` contains LLM provider implementations. The factory selects `mock`, `gemini`, or `ollama` from `LLM_PROVIDER`.
- `case_templates/` contains YAML OSCE case templates for standardized simulations.
- `app/services/case_loader.py` validates and loads YAML case templates.
- `app/db/session.py` manages SQLModel and SQLite initialization.
- `legacy/`, when present in a development checkout, stores archived FastAPI API server files, Docker deployment files, API tests, generated run artifacts, and old pytest configuration. It is not required for the Streamlit-first app.

Legacy FastAPI code is archived for reference only and is not imported by the Streamlit app by default.

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app with the deterministic MockProvider:

```bash
streamlit run streamlit_app.py
```

MockProvider is the default provider and requires no API key.

## Run with MockProvider

MockProvider is the recommended path for local development, tests, and reproducible demos:

```bash
LLM_PROVIDER=mock streamlit run streamlit_app.py
```

On Windows PowerShell:

```powershell
$env:LLM_PROVIDER = "mock"
streamlit run streamlit_app.py
```

## Run with GeminiProvider

GeminiProvider is optional and requires an API key:

```bash
LLM_PROVIDER=gemini GEMINI_API_KEY=your-google-api-key streamlit run streamlit_app.py
```

On Streamlit Community Cloud or local Streamlit secrets, set:

```toml
LLM_PROVIDER = "gemini"
GEMINI_API_KEY = "your-google-api-key"
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

Do not commit real API keys or `.streamlit/secrets.toml`.

## Run Tests and Benchmarks

Run tests:

```bash
pytest
```

Run the hidden-information disclosure benchmark:

```bash
LLM_PROVIDER=mock python experiments/run_disclosure_eval.py
```

Run the OSCE assessment benchmark:

```bash
LLM_PROVIDER=mock python experiments/run_osce_eval.py
```

All tests and benchmarks are designed to run with MockProvider and should not require external LLM calls.

## Project Structure

- `app/`: service, model, schema, repository, provider, and evaluation code.
- `case_templates/`: structured YAML OSCE cases.
- `experiments/`: deterministic benchmark runners, sample transcripts, and small benchmark outputs.
- `tests/`: Streamlit/service/evaluation-focused pytest suite.
- `docs/`: interview and presentation documentation.
- `streamlit_app.py`: active Streamlit application entry point.
- `TECHNICAL_REPORT.md`: technical report for presentation and review.

## Safety Disclaimer

SimuPatient is for medical education simulation and software research only. It is not intended for clinical diagnosis, treatment, medical advice, patient care, or high-stakes learner assessment. Benchmark results are deterministic internal software evaluation results, not clinical validation.

## Local Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure secrets for local Streamlit runs:

```bash
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Then edit `.streamlit/secrets.toml`:

```toml
LLM_PROVIDER = "mock"
```

Run the deterministic local app:

```bash
streamlit run streamlit_app.py
```

The default `mock` provider requires no API key and makes no external LLM calls. It is intended for local development, UI checks, and tests.

To run against Gemini instead:

```toml
LLM_PROVIDER = "gemini"
GEMINI_API_KEY = "your-google-api-key"
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

Then start the same Streamlit entry point:

```bash
streamlit run streamlit_app.py
```

The SQLite database is created automatically when the app starts. Local database files are ignored by Git.

## Patient Modes

SimuPatient supports two ways to start a consultation:

- `Random patient`: Enter a short clinical seed and let the selected provider generate a patient profile.
- `Case template`: Select a predefined YAML case from `case_templates/`. The patient is initialized from the standardized case data, and the first chat message uses the case `opening_statement`.

The case-template path is useful for repeatable OSCE practice and local testing. The random path remains available for exploratory simulation.

## Case Templates

Case templates are YAML files in `case_templates/`. Each file must include this schema:

```yaml
case_id: chest_pain_001
title: Acute chest pain with cardiac risk factors
specialty: emergency_medicine
difficulty: intermediate
chief_complaint: Chest pain for 2 hours
demographics:
  age: 58
  gender: male
  occupation: taxi driver
present_illness:
  onset: sudden
  duration: 2 hours
  location: central chest
  character: pressure-like
  severity: 8/10
  radiation: left arm
  associated_symptoms:
    - sweating
  aggravating_factors:
    - exertion
  relieving_factors:
    - rest partially helps
past_medical_history:
  - hypertension
medication_history:
  - amlodipine
allergy_history:
  - no known drug allergies
family_history:
  - father died of myocardial infarction at 62
social_history:
  smoking: current smoker, 20 pack-years
  alcohol: occasional
  drug_use: denies unless asked directly
hidden_information:
  - item: recent cocaine use
    reveal_condition: only reveal if asked directly about recreational drug or stimulant use
    clinical_relevance: increases concern for cocaine-associated coronary vasospasm
red_flags:
  - acute coronary syndrome
expected_key_questions:
  - onset
  - radiation
scoring_rubric:
  history_taking: 40
  communication: 20
  clinical_reasoning: 20
  empathy: 10
  closure: 10
patient_personality:
  anxiety: high
  cooperativeness: medium
  health_literacy: low
opening_statement: "Doctor, I have this heavy pressure in my chest and I'm really worried."
```

To add a new case:

1. Create a new `.yaml` file in `case_templates/`.
2. Use a unique `case_id`.
3. Include every required field shown above.
4. Run `pytest` to validate that the case loads successfully.

## Streamlit Community Cloud

1. Push this repository to GitHub.
2. Create a Streamlit Community Cloud app from the repository.
3. Set `streamlit_app.py` as the main file.
4. Add provider secrets in Streamlit Cloud settings. For deterministic demo mode:

```toml
LLM_PROVIDER = "mock"
```

For Gemini-backed runs:

```toml
LLM_PROVIDER = "gemini"
GEMINI_API_KEY = "your-google-api-key"
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

No Docker, FastAPI server, or external database service is required for the current Streamlit deployment.

## Provider Configuration

Provider selection is controlled by `LLM_PROVIDER`:

- `mock`: deterministic provider, no API key, no external calls. This is the default local and test path.
- `gemini`: Google Gemini provider. Requires `GEMINI_API_KEY` from the environment or Streamlit secrets.
- `ollama`: retained for local experimentation when the optional Ollama SDK and server are available.

Provider modules are importable without installing or initializing optional SDKs. A provider-specific SDK is only needed when that provider is selected and used for real calls.

## Tests

Run the active Streamlit/service-layer tests:

```bash
pytest
```

The tests force `LLM_PROVIDER=mock` where service behavior is exercised, validate all YAML case templates, use a temporary SQLite database, and do not require a real API key.

## Disclosure Evaluation

Run the deterministic hidden-information disclosure benchmark:

```bash
LLM_PROVIDER=mock python experiments/run_disclosure_eval.py
```

On Windows PowerShell:

```powershell
$env:LLM_PROVIDER = "mock"
python experiments/run_disclosure_eval.py
```

The disclosure benchmark has two splits:

- `policy_unit_test`: controlled allow/deny examples that verify the basic disclosure policy.
- `behavioral_challenge_test`: more realistic question forms that probe indirect, ambiguous, leading, compound, and prompt-injection-style behavior.

Policy-unit scenarios include simple vague, direct, unrelated, and empathy-only questions. Perfect policy-unit scores only mean these controlled examples passed; they do not imply real-world performance.

Challenge scenarios include:

- `vague_general_question`
- `direct_relevant_question`
- `unrelated_question`
- `empathy_question`
- `indirect_relevant_question`
- `ambiguous_question`
- `leading_question`
- `compound_question`
- `adversarial_prompt_injection_question`

Reported metrics include:

- `policy_unit_precision`
- `policy_unit_recall`
- `policy_unit_premature_disclosure_rate`
- `challenge_precision`
- `challenge_recall`
- `challenge_premature_disclosure_rate`
- `challenge_exact_item_match_rate`
- `over_disclosure_rate`
- `prompt_injection_resistance_rate`

Results are saved to:

- `experiments/results/disclosure_policy_unit_eval.json`
- `experiments/results/disclosure_policy_unit_eval.csv`
- `experiments/results/disclosure_challenge_eval.json`
- `experiments/results/disclosure_challenge_eval.csv`
- `experiments/results/disclosure_eval_summary.md`

This benchmark is deterministic and does not make external LLM calls. It is an internal regression benchmark, not clinical validation. The challenge split is included to make disclosure behavior more transparent under realistic question styles, but it is still an authored rule-based benchmark rather than evidence of real-world standardized-patient safety.

## OSCE Assessment Benchmark

Run the deterministic OSCE assessment benchmark:

```bash
LLM_PROVIDER=mock python experiments/run_osce_eval.py
```

On Windows PowerShell:

```powershell
$env:LLM_PROVIDER = "mock"
python experiments/run_osce_eval.py
```

Sample consultation transcripts live in `experiments/sample_transcripts/`. Each transcript is linked to an existing `case_id`, includes a `poor`, `borderline`, or `good` student level, and contains hand-authored reference rubric scores.

The benchmark is split internally into two parts:

- `rule_based_rubric_scorer`: deterministic scorer that detects expected-question coverage, missed items, clinician-addressed red flags, empathy language, closure/safety-netting language, and clinical reasoning markers.
- `benchmark_metric_calculator`: aggregate metric calculator for score error, pass/fail agreement, red-flag detection, and missed-item detection.

Each scored transcript includes predicted scores, reference scores, score errors, detected covered items, detected missed items, detected red flags, and an explainable feedback summary.

Reported metrics:

- `total_score_mae`: mean absolute error between predicted and reference total scores.
- `dimension_score_mae`: mean absolute error by rubric dimension.
- `score_correlation`: Pearson correlation between predicted and reference total scores when calculable.
- `pass_fail_agreement`: agreement using a pass threshold of 70.
- `false_pass_count` and `false_fail_count`: pass/fail calibration errors at the threshold of 70.
- `red_flag_detection_accuracy`: agreement on whether clinician-addressed safety red flags were detected.
- `missed_item_detection_accuracy`: semantic overlap between predicted and expected missed history items.

Results are saved to:

- `experiments/results/osce_eval.json`
- `experiments/results/osce_eval.csv`
- `experiments/results/osce_eval_summary.md`
- `experiments/results/osce_eval_per_transcript.md`

This is an internal deterministic benchmark for regression checking and reproducibility. It is not clinical validation and should not be interpreted as evidence of real-world OSCE assessment validity. Current results should be read as calibration diagnostics: a high score correlation may mean transcripts are ranked consistently, while total-score MAE, false pass/fail counts, and missed-item detection expose remaining rubric calibration limits.

## Legacy Archive

Development checkouts may include a `legacy/` folder with files from the previous architecture:

- `legacy/fastapi/` contains the old FastAPI entry point and API routes.
- `legacy/docker/` contains the old Dockerfile and compose file.
- `legacy/tests/` contains API-oriented pytest tests from the FastAPI phase.
- `legacy/generated/` contains generated files and prior local run outputs.
- `legacy/config/` contains old pytest configuration.

These files are retained for historical reference only. New work should target the Streamlit app and shared `app/` layers.
