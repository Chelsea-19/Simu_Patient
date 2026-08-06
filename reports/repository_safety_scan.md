# Repository Safety Scan

Scan date: 2026-08-05
Branch: `release/goai-submission`

## Result

PASS for public-source preparation. No credential value, tracked local database,
personal absolute path, direct personal identifier, or prohibited product claim
was identified in the release content.

## Secrets and Credentials

Scanned text, source, examples, reports, YAML/JSON/CSV outputs, PPTX XML and notes,
and extracted PDF text for:

- `API_KEY`, `SECRET`, `TOKEN`, and `PASSWORD` identifiers;
- common live-key prefixes;
- bearer credentials;
- private-key headers.

Matches for generic identifiers were limited to configuration field names,
documentation, empty values, `your-key` placeholders, and test-only fake values.
High-confidence live-key patterns returned zero matches in both repository text
and submission binaries. `.env.example` contains an empty Gemini key field, and
`.streamlit/secrets.toml.example` contains an explicit placeholder.

## Local Paths

The initial PPTX notes and audit draft contained a local source prefix. Both were
sanitized to repository-relative references. The final repository text, PPTX XML
and notes, and extracted PDF text contain no Windows user/workspace path,
`/Users/` path, or named `/home/` path.

URLs, localhost addresses, and SQLite URI syntax were retained because they are
portable run configuration rather than personal filesystem paths.

## Databases and Runtime Artifacts

- `git ls-files` returned no database, SQLite, cache, compiled Python, private
  `.env`, or Streamlit secrets file.
- `simupatient.db` and `evaluation/results/ui_evidence_phase6.db` were removed
  from the local workspace before release preparation.
- Test-created caches and temporary databases are ignored and removed again
  before the final commit.
- Reproducible CSV/JSON/Markdown benchmark outputs are retained.

## Patient Data and Personal Identifiers

- Email, phone-number, and national-identifier pattern scans returned no matches.
- Case templates are authored educational YAML cases with synthetic individuals.
- Screenshots use synthetic demo learner/session identifiers and a locally
  generated evidence database.
- No real patient record or real patient ID was identified.

## Claims and Product Naming

- Public text and submission binaries contain no version-suffixed SimuPatient
  branding or upgrade language.
- No claim that the system is clinically validated, hospital-deployed,
  completely safe, or a replacement for clinicians/OSCE examiners was found.
- Occurrences of validation language are explicit negative limitations.
- README, deck, and reports describe benchmarks as internal deterministic
  software evaluation and preserve the known OSCE calibration failures.

## Remaining Boundaries

- Pattern scanning cannot prove the provenance of every medical statement.
- The authored medical cases and scoring rules still require expert review.
- Instructor mode is an environment gate, not public authentication.
- Public deployment requires separate identity, authorization, storage, privacy,
  and governance review.
