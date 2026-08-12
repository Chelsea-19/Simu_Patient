# GOAI 2026 Repository Audit — SimuPatient

**Audited:** 2026-08-12
**Scope:** tracked repository content, local working-tree safety, reproducibility, claim-to-code consistency, and competition-facing presentation.
**Baseline:** `goai-final-audit`, created from the merged GOAI submission baseline and reconciled against remote `main` at `79136a7`.

## Verdict

**GOAI Repository Readiness: 84 / 100 — B: Ready after minor cleanup**

SimuPatient presents a real, runnable education-simulation product: it has a clear Streamlit entry point, deterministic stateful workflow, authored cases, safety checks, persisted traces, tests, and reproducible offline evaluations. The remaining restraint is deliberate: its formative rubric and authored benchmarks are not clinical validation or a certified OSCE system.

## Evidence snapshot

- The pre-cleanup repository contained 188 tracked files. Classification was **171 KEEP**, **1 MOVE**, and **16 DELETE** candidates; no core component was removed.
- The subsequent remote removal of the entire `docs/` and `submission/` directories would remove required deployment, safety, reproducibility, and competition evidence. This change restores the active material, while keeping the three obsolete documentation deletions.
- `python -m pytest -q` passed **67 tests** on 2026-08-12.
- `python evaluation/run_goai_evaluation.py` reproduced all **15/15** authored MockProvider scenarios: **152/152** expected trace actions, **8/8** safety detections, **3/3** unsafe-discharge blocks, and **6/6** prompt-injection attempts resisted.
- The disclosure runner reproduced 80 policy cases and 180 challenge cases; its reported precision/recall were 1.000 with zero premature disclosures.
- The OSCE runner reproduced the retained, non-perfect result on 10 authored transcripts: MAE 19.100, pass/fail agreement 0.700, 0 false passes, and 3 false fails. This is appropriate evidence for a formative regression tool, not for high-stakes assessment.
- No broken tracked Markdown links or stale references to the moved/deleted paths were found after cleanup.

## File decision table

| Path | Decision | Reason | Risk | Action |
|---|---|---|---|---|
| `README.md`, `LICENSE`, `pyproject.toml`, `requirements.txt`, `.gitignore` | KEEP | Run, license, dependency, and repository-entry evidence. | LOW | Retain. |
| `streamlit_app.py`, `app/**` | KEEP | Public application and all agent, state, tool, safety, provider, persistence, and scoring components. | CRITICAL | Retain. |
| `case_templates/**` | KEEP | Synthetic, authored clinical-learning cases required for the app and benchmarks. | HIGH | Retain. |
| `tests/**` | KEEP | Regression evidence for state, safety, disclosure, UI service, and evaluation behavior. | HIGH | Retain. |
| `evaluation/**`, `experiments/**` | KEEP | Runners plus compact CSV/JSON/Markdown regression evidence. | HIGH | Retain. |
| `assets/demo_traces/**`, `assets/screenshots/**` | KEEP | Reproducible scenario evidence and demo evidence. | MEDIUM | Retain. |
| Active `docs/**` guides | KEEP | Deployment, safety, case, tool, state, teacher, learning, and technical interpretation references. | MEDIUM | Retain. |
| Tracked `submission/**` deck, PDF, guide, script, checklist, and manifest | KEEP | Submission-facing evidence. | HIGH | Retain. |
| `TECHNICAL_REPORT.md` | MOVE | Valuable technical and benchmark interpretation was misplaced at repository root. | LOW | Moved to `docs/technical_report.md`; README updated. |
| `docs/goai_gap_analysis.md`, `docs/goai_upgrade_plan.md` | DELETE | Superseded development plans; no tracked references and no runtime/evaluation role. | LOW | Deleted. |
| `docs/中文面试准备_SimuPatient.md` | DELETE | Personal interview-preparation material, not project or reproducibility documentation; no tracked references. | LOW | Deleted. |
| `reports/github_release_audit.md`, `reports/github_release_final_report.md`, `reports/github_release_test_report.md`, `reports/pr_description.md`, `reports/repository_safety_scan.md` | DELETE | Unreferenced release/process logs duplicated by the retained product docs, tests, and evaluation artifacts. | LOW | Deleted. |
| `reports/phase_0_report.md` through `reports/phase_7_report.md` | DELETE | Development-phase logs create Markdown inflation and have no runtime or evidence dependency. | LOW | Deleted. |
| `.env`, `.streamlit/secrets.toml`, local `*.db`, caches, `~$*` Office locks | GITIGNORE | Local configuration, secrets, runtime state, and editor artifacts must not enter Git. | HIGH if committed | Ignore; examples remain tracked. |
| Untracked `submission/Geometric Minimalist Pitch Deck.pptx`, `submission/SimuPatient_GOAI_Preliminary_polished.pptx`, `submission/ai_taste_audit.md`, `submission/change_log.md` | REVIEW MANUALLY | User-created, untracked submission materials; their publication intent cannot be inferred safely. | HIGH | Preserved without modification or staging. |

The named delete candidates were checked against tracked code, README, tests, deployment, evaluation, and demo references before deletion. No references were found; reproducibility is retained through the active documentation, runners, results, tests, and traces.

## Judge-facing review

### First 60 seconds — 8.6 / 10

The README immediately identifies the user, the education-only boundary, the workflow, offline quick start, evaluation commands, safety posture, repository map, and MIT license. The added agent explanation makes the controlled state, typed tools, disclosure policy, trace, safety gate, and feedback/retry loop easy to distinguish from an open-ended chatbot. The main opportunity is a short hosted-demo URL if a stable public deployment is available; none is claimed here.

### Agent and engineering depth

The architecture is proportionate to the product: a deterministic `SimuEngine`, `EncounterStateMachine`, `DisclosureService`, `ClinicalSkillRouter`, `SafetySupervisor`, `LearningDiagnosisService`, and provider boundary. The design uses optional LLM dialogue inside authored workflow boundaries rather than asking a model to enforce safety alone.

### Evaluation integrity

The repository keeps executable runners, raw compact result files, scenario traces, and tests that verify the metric counts. Metrics are labelled as authored deterministic regression evidence. The retained imperfect OSCE values are a positive credibility signal because they prevent a high-stakes claim.

### Medical safety and privacy

README and evaluation artifacts consistently define the project as medical education simulation and formative feedback, not diagnosis, treatment, medical-device software, or a certified examination. Learner projections protect hidden case facts; instructor mode is explicitly described as a local role gate, not public authentication. Cases and identifiers are documented as synthetic.

### Security and open source

No credential-shaped values, private runtime databases, or committed secret files were found in the tracked repository. `.env`, Streamlit secrets, SQLite files, caches, and Office locks are ignored while safe templates remain tracked. The repository carries an MIT license. Installed-package metadata reports Apache-2.0/MIT licenses for the checked core packages; `pydantic` does not publish a license field through the local metadata, so dependency notices should be reviewed again before any commercial redistribution.

### Repository quality and AI-smell assessment

The active repository is compact and product-centred after removing 16 unreferenced process documents. There are no duplicated tracked file hashes and no tracked file large enough to require Git LFS (the largest submission PDF is about 0.49 MiB). The remaining documentation is evidence-bearing rather than a sequence of agent-work logs. No active overclaimed capability was found.

## Judge simulation

| Judge | Score | Top strengths | Top concern |
|---|---:|---|---|
| Product | 8.3 / 10 | Clear learner loop, coherent Streamlit workflow, focused retry. | No stable hosted-demo URL is documented. |
| Technical | 8.6 / 10 | Deterministic state/tool/safety boundaries, MockProvider, 67 passing tests, reproducible runners. | Optional Gemini/Ollama runtime paths were not network-tested in this audit. |
| Medical / academic | 8.2 / 10 | Explicit formative boundary, synthetic data posture, safety blocking, candid OSCE limitations. | Authored internal benchmarks are not independent clinical or educational validation. |

## Final scorecard

| Dimension | Score |
|---|---:|
| Product clarity | 9 / 10 |
| Agent depth | 8 / 10 |
| Engineering quality | 9 / 10 |
| Reproducibility | 9 / 10 |
| Evaluation credibility | 8 / 10 |
| Medical safety | 8 / 10 |
| Open-source quality | 8 / 10 |
| Repository cleanliness | 9 / 10 |
| Human-authored credibility | 8 / 10 |
| GOAI submission readiness | 8 / 10 |

## Recommended final structure

```text
SimuPatient/
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── streamlit_app.py
├── app/
├── case_templates/
├── tests/
├── evaluation/
├── experiments/
├── assets/
├── docs/
├── submission/
└── GOAI_*                 # required final audit deliverables
```

The root remains intentionally small; the `GOAI_*` files are the explicit competition-audit deliverables requested for this review.
