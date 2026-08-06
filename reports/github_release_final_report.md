# GitHub Release Final Report

## Status

BLOCKED

Local release preparation is complete and validated. Remote publication is
blocked because GitHub CLI is not authenticated; no push or Pull Request was
attempted after that prerequisite failed.

## Repository

- Repository: `https://github.com/Chelsea-19/Simu_Patient`
- Base branch: `main`
- Head branch: `release/goai-submission`
- Pull request: not created (GitHub authentication required)
- Head commit: the commit containing this report; resolve with
  `git rev-parse HEAD` after checkout

## File Audit

### Kept

- Streamlit application, service/model/schema/repository layers, and supported
  Mock/Gemini/Ollama providers.
- 20 YAML educational cases and all active tests.
- Reproducible experiments, GOAI evaluation, demo traces, and small results.
- Eight real prototype screenshots.
- Documentation, submission PPTX/PDF, technical report, and MIT License.

### Removed

- Local caches, compiled Python files, pytest cache, and two SQLite databases.
- Disconnected OpenAI provider module not exposed or tested by the application.

### Ignored

- Environment and Streamlit secret files.
- Virtual environments and IDE settings.
- Local databases, coverage/build output, logs, temporary files, and `/tmp/`.

### Renamed

- No filesystem rename was required. The apparent encoded documentation path was
  already a valid UTF-8 filename: `docs/中文面试准备_SimuPatient.md`.
- Public title text was normalized to `SimuPatient` across text and binary
  submission materials.

## README

- Project title: SimuPatient
- Contains version-suffixed branding: No
- Quick start verified: Yes (dependency install and local Streamlit startup)
- Safety disclaimer present: Yes
- Data source statement present: Yes
- MIT License link present: Yes

## Tests

- pytest: 67 passed, 0 failed
- disclosure evaluation: PASS, 260 scenarios
- OSCE evaluation: runner PASS with retained MAE 19.100 and 3 false fails
- GOAI evaluation: PASS, 15/15 scenarios
- Streamlit smoke test: PASS, health/root HTTP 200
- PPTX/PDF: PASS, 10 slides/pages rendered and visually reviewed

## Security Scan

- API keys: no credential values; placeholders only
- secrets: no committed secret file or strong secret pattern
- databases: no tracked database
- local paths: none in final text, PPTX notes/XML, or PDF text
- patient data: structured synthetic educational cases only

## Remaining Risks

- The OSCE scorer is not calibrated for high-stakes assessment.
- Optional network providers were not exercised in release validation.
- Medical content and authored rules require professional review.
- Instructor role gating is not production authentication.
- No public demo URL has been provisioned.
- GitHub authentication is required to push and create the draft PR.

## Manual Actions

1. Authenticate GitHub CLI with `gh auth login`.
2. Push `release/goai-submission` to `origin` without force.
3. Create the draft Pull Request using `reports/pr_description.md`.
4. Review GitHub checks and the Pull Request diff.
5. Merge only after human review.
6. Verify the default-branch README after merge.
