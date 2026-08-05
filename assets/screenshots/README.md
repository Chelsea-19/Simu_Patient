# Phase 6 Prototype Evidence

These PNG files were captured from the running Streamlit prototype on 2026-08-05 at a
1440 x 1000 browser viewport. The learner and instructor processes both used
`LLM_PROVIDER=mock` and the same temporary SQLite evidence database. The database is
not committed; the screenshots and scenario traces are the durable evidence.
The screenshots were recaptured from the release branch after the public project title
was normalized to `SimuPatient`.

| File | Role | Evidence |
|---|---|---|
| `01_learning_goal_selection.png` | learner | Chest-pain case and training-goal selection |
| `02_patient_interview.png` | learner | Restored multi-turn patient interview |
| `03_clinical_tool_call.png` | learner | Deterministic cardiovascular examination result |
| `04_safety_block.png` | learner | Persisted high-risk completion block without answer leakage |
| `05_learning_diagnosis.png` | learner | Trace-grounded multidimensional learning profile |
| `06_personalized_retry.png` | learner | Personalized remediation plan and focused-retry action |
| `07_two_round_comparison.png` | learner | First/second-round score and dimension comparison |
| `08_teacher_dashboard.png` | instructor | Role-gated records, scores, safety events, and retry link |

The images are Demo evidence, not proof of clinical validity or educational efficacy.
