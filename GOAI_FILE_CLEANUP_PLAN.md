# GOAI File Cleanup Plan — SimuPatient

**Decision rule:** inspect first, search all tracked references, then make only low-risk changes. If publication intent or reproducibility impact was uncertain, the file was kept.

## Safe cleanup executed

| Change | Why it was safe | Reference / reproducibility check |
|---|---|---|
| Restored active `docs/**` and tracked `submission/**` material removed from remote `main` | These are required safety, deployment, reproducibility, and competition-evidence artifacts, not process clutter. | Required by the audit's KEEP / DO NOT DELETE classification; no application component is altered. |
| Moved `TECHNICAL_REPORT.md` to `docs/technical_report.md` | It is retained technical evidence but did not belong at root. | README link updated; no broken Markdown links remain. |
| Deleted `docs/goai_gap_analysis.md` and `docs/goai_upgrade_plan.md` | Obsolete planning snapshots, including statements superseded by the implemented safety and evaluation system. | No tracked code, README, test, deployment, evaluation, or demo references. |
| Deleted `docs/中文面试准备_SimuPatient.md` | Personal interview notes did not explain or run the product. | No tracked references. |
| Deleted 13 files under `reports/` | Release reports, PR text, safety scan, and phase logs were unreferenced process artifacts. | No tracked references; active tests, evaluation results, traces, and product docs are retained. |
| Added `~$*` to `.gitignore` | Microsoft Office creates short-lived lock files next to editable decks/documents. | Does not ignore project source or authored assets. |

Deleted report paths:

- `reports/github_release_audit.md`
- `reports/github_release_final_report.md`
- `reports/github_release_test_report.md`
- `reports/phase_0_report.md` through `reports/phase_7_report.md`
- `reports/pr_description.md`
- `reports/repository_safety_scan.md`

## Do not delete

| Evidence group | Reason |
|---|---|
| `app/**` and `streamlit_app.py` | Core application, agent workflow, state, disclosure, tools, safety, learning, provider, and persistence logic. |
| `case_templates/**` | Structured synthetic cases consumed by the app and benchmarks. |
| `tests/**` | Regression proof for the core interactions and safety boundaries. |
| `evaluation/**`, `experiments/**` | Executable evaluation plus compact underlying results. |
| `assets/demo_traces/**`, `assets/screenshots/**` | Reviewer-verifiable behavior and demo evidence. |
| Active `docs/**` | Deployment, authoring, safety, tool, state, teacher, and technical-context documentation. |
| Tracked `submission/**` material | Competition deck, PDF, demo script, checklist, manifest, and prototype guide. |
| `LICENSE`, `README.md`, dependency files, configuration examples | Open-source, onboarding, and reproducibility essentials. |

## Review manually; no action taken

| Path | Why manual review is required |
|---|---|
| `submission/Geometric Minimalist Pitch Deck.pptx` | An untracked presentation asset with no clear publication relationship to the tracked competition deck. |
| `submission/SimuPatient_GOAI_Preliminary_polished.pptx` | It is untracked and may be intended to replace the tracked presentation; this cannot be safely inferred. |
| `submission/ai_taste_audit.md` | Untracked authoring/audit material; decide whether it belongs in a public submission. |
| `submission/change_log.md` | Untracked presentation working note; preserve or exclude based on the submitter's packaging decision. |

These files were deliberately neither deleted nor staged.

## Gitignore-only material

Local databases, environment files, Streamlit secrets, Python/tool caches, IDE files, logs, temporary files, and Office `~$` locks should remain local. Their safe examples (such as `.env.example` and Streamlit secret templates) remain tracked. The audit found no need to add Git LFS: the largest tracked artifact is a roughly 0.49 MiB PDF, and no duplicate tracked file hashes were found.

## Remaining optional improvements before submission

1. If a stable public deployment exists, add its URL and a one-line demo path to the README; do not claim availability until it is tested.
2. Decide whether the polished presentation replaces the tracked deck, then stage exactly one intended version.
3. Keep public deployment in learner mode; treat `APP_ROLE=instructor` as a controlled local deployment setting, not authentication.
4. Recheck third-party dependency notices before commercial redistribution.
5. Preserve the education-only and non-high-stakes wording in future slides, README edits, and demos.
