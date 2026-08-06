## Summary

This pull request prepares SimuPatient for public review and the GOAI
AI+Education preliminary submission.

It preserves the existing Streamlit-first application while cleaning repository
artifacts, normalizing public naming, improving documentation, refreshing real
prototype evidence, and validating the reproducible learner workflow.

## Changes

- removed local databases, caches, compiled files, and temporary artifacts;
- strengthened `.gitignore` for secrets, databases, build output, coverage,
  logs, and temporary files;
- removed a disconnected provider module that was not supported by the factory,
  dependencies, settings, or tests;
- updated the README around the clinical reasoning and OSCE training workflow;
- documented learner/instructor boundaries, data sources, and educational-use
  limitations;
- normalized public naming across the app, docs, screenshots, PPTX, and PDF;
- recaptured eight real MockProvider Streamlit screenshots with synthetic data;
- retained reproducible evaluation outputs and submission materials;
- added repository audit, security scan, test, and final release reports.

## Validation

- `pytest`: 67 passed, 0 failed;
- disclosure evaluation: 80 policy + 180 challenge scenarios; precision/recall
  1.000, premature disclosure 0.000;
- OSCE evaluation: 10 transcripts; runner passed with retained limitations
  (MAE 19.100, agreement 0.700, 3 false fails);
- GOAI workflow evaluation: 15/15 scenarios passed; unsafe discharge blocking
  3/3; Action Trace completeness 152/152;
- MockProvider Streamlit smoke test: health HTTP 200 (`ok`), root HTTP 200;
- submission deck: 10-slide fidelity check passed with 0 issues, no overflow;
- PDF deck: 10 pages rendered successfully.

## Safety and Scope

- no real patient data is included;
- local SQLite databases are excluded;
- no API keys or Streamlit secrets are committed;
- the project is for medical education simulation and formative feedback;
- internal benchmarks are not clinical validation;
- the public learner workflow does not expose instructor-only case information;
- instructor mode remains a controlled environment gate, not authentication.

## Known Limitations

- the deterministic OSCE scorer remains insufficient for high-stakes assessment;
- Gemini and Ollama were not network-tested in this release validation;
- no public Streamlit deployment URL is included.

## Review Focus

Please verify:

1. the learner workflow runs with MockProvider;
2. hidden case information is not exposed;
3. tests and evaluation scripts are reproducible;
4. submission materials open correctly;
5. no local artifacts, secrets, or personal paths are included.
