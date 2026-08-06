# SimuPatient

SimuPatient is an adaptive clinical reasoning and OSCE training agent for
medical education.

It combines structured standardized-patient cases, controlled hidden-information
disclosure, clinical skill tools, safety supervision, formative assessment, and
focused retraining in a reproducible Streamlit application.

SimuPatient 面向医学生、OSCE 学习者与医学教育者，用于可重复的临床推理训练、
形成性反馈和针对性复训。

## Who It Is For

- Medical students practicing structured history-taking and clinical reasoning.
- OSCE learners rehearsing evidence gathering, differential diagnosis, and safe
  management decisions.
- Medical educators reviewing formative learning traces in a controlled local
  instructor environment.

The project is an education simulator. It supports practice and formative
feedback; it is not a diagnostic, treatment, or high-stakes examination system.

## Learning Loop

```text
Learning Goal
-> Standardized Patient Interview
-> Clinical Skill Tools
-> Differential Diagnosis
-> Management Plan
-> Safety Review
-> Learning Diagnosis
-> Focused Retry
```

The learner selects a goal and completes a structured encounter. The application
records questions, tool calls, reasoning, and management actions; checks unsafe
completion attempts; then produces a multidimensional learning diagnosis and a
focused retry plan.

## Core Features

- Validated YAML standardized-patient cases.
- Conditional disclosure of hidden case information.
- Vital signs and physical-examination tools.
- Deterministic ECG and laboratory investigations.
- Differential-diagnosis and management-plan submission.
- A Safety Supervisor that blocks authored high-risk completion patterns.
- An Action Trace for learner-visible evidence and formative review.
- Multidimensional learning diagnosis and formative feedback.
- Focused Retry with first/second-attempt comparison.
- A role-gated local teacher view.
- A deterministic MockProvider for offline tests and demos.

## Quick Start

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/Chelsea-19/Simu_Patient.git
cd Simu_Patient
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

MockProvider is the default and does not require an API key. To select it
explicitly on Windows PowerShell:

```powershell
$env:LLM_PROVIDER = "mock"
streamlit run streamlit_app.py
```

On macOS/Linux:

```bash
LLM_PROVIDER=mock streamlit run streamlit_app.py
```

The app creates a local SQLite database when it starts. Local databases are
ignored by Git.

## Providers

The provider factory exposes three providers:

- `mock`: deterministic, offline, and the default for tests and public demos.
- `gemini`: optional; requires `GEMINI_API_KEY` and the installed Gemini SDK.
- `ollama`: optional local experimentation with a running Ollama server and SDK.

Provider modules import optional SDKs only when selected. For Gemini, copy the
example configuration and supply a real key only in your local environment or
Streamlit secrets:

```bash
LLM_PROVIDER=gemini GEMINI_API_KEY=your-key streamlit run streamlit_app.py
```

Never commit `.env`, `.streamlit/secrets.toml`, or credential values.

## Tests and Evaluation

Run the active test suite:

```bash
pytest
```

Run the deterministic disclosure benchmark:

```bash
LLM_PROVIDER=mock python experiments/run_disclosure_eval.py
```

Run the deterministic OSCE benchmark:

```bash
LLM_PROVIDER=mock python experiments/run_osce_eval.py
```

Run the authored GOAI workflow scenarios:

```bash
LLM_PROVIDER=mock python evaluation/run_goai_evaluation.py
```

The runners write small CSV, JSON, and Markdown outputs under
`experiments/results/`, `evaluation/`, and `evaluation/results/`. These are
internal software regression results, not clinical or educational validation.

## Project Structure

- `app/`: models, schemas, repositories, providers, services, and evaluation
  utilities used by the Streamlit application.
- `case_templates/`: structured synthetic educational cases.
- `tests/`: service, safety, state-isolation, provider, and evaluation tests.
- `experiments/`: disclosure and OSCE benchmark runners and authored transcripts.
- `evaluation/`: end-to-end workflow scenario runner and aggregate metrics.
- `assets/demo_traces/`: reproducible authored scenario evidence.
- `assets/screenshots/`: screenshots captured from the local Streamlit prototype.
- `docs/`: authoring, deployment, safety, state-separation, and tool guides.
- `submission/`: competition introduction, deck, prototype guide, and demo script.
- `streamlit_app.py`: the public application entry point.

## Submission Materials

- Project introduction: `submission/project_intro_zh.md`
- Presentation: `submission/SimuPatient_GOAI_Preliminary.pptx`
- PDF deck: `submission/SimuPatient_GOAI_Preliminary.pdf`
- Prototype guide: `submission/prototype_guide.md`
- Demo script: `submission/demo_script_3min.md`

## Learner and Instructor Boundaries

The public learner workflow exposes only learner-visible case data. Full case
facts and teacher records are behind the server-side `APP_ROLE=instructor` gate.
The default public demo must remain in learner mode and must not offer instructor
permissions or expose authored hidden state.

Instructor mode is intended only for a controlled local or separately secured
teacher instance. It is not an authentication system and must not be treated as
one for a public deployment.

## Safety and Intended Use

- SimuPatient is for medical education simulation and software research.
- It must not be used for diagnosis, treatment, medical advice, or patient care.
- It does not replace medical teachers, standardized patients, or formal OSCE
  examiners.
- Internal tests and benchmarks are not clinical validation or proof of
  educational effectiveness.
- The default public demo does not provide instructor access.
- Safety rules are authored software checks and require professional review
  before any broader educational deployment.

## Data Sources and Privacy

- Cases are structured educational scenarios stored as YAML.
- Individual people and encounter identifiers are synthetic.
- Examination, ECG, and laboratory results come from the selected case template.
- The repository does not include real patient records or local runtime databases.
- Medical content and scoring rules still require review by qualified educators
  and clinical professionals.

## Documentation

- Local and Streamlit deployment: `docs/deployment.md`
- Case schema: `docs/case_schema.md`
- Case authoring: `docs/case_authoring_guide.md`
- Learner/instructor state separation: `docs/state_separation.md`
- Safety supervisor: `docs/safety_supervisor.md`
- Clinical tool interface: `docs/tool_interface.md`
- Learning diagnosis: `docs/learning_diagnosis.md`
- Teacher workflow: `docs/teacher_workflow.md`

## License

SimuPatient is released under the [MIT License](LICENSE).
