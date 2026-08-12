# GOAI Claim-to-Code Matrix — SimuPatient

This matrix checks externally visible capability claims against source, tests, and retained evaluation evidence. `VERIFIED` means the claim is supported within this repository; it does not imply clinical validation.

| Claim | Code evidence | Test / evaluation evidence | Status |
|---|---|---|---|
| Stateful Patient Agent workflow | `app/services/simu_engine.py` (`SimuEngine`); `app/services/encounter_state_machine.py` (`EncounterStateMachine`) | `tests/test_clinical_tools_state_machine.py`; 15/15 end-to-end GOAI scenarios | VERIFIED |
| Controlled hidden-information disclosure | `app/services/disclosure_service.py` (`DisclosureService`) | Learner-isolation and prompt-injection tests; 80 policy and 180 challenge disclosure cases | VERIFIED |
| Typed clinical skill tools | `app/services/clinical_skill_router.py` (`ClinicalSkillRouter`); `app/streamlit_services.py` tool functions | State-machine tests cover YAML-loaded tools, invalid calls, duplicate investigations, and wrong stages | VERIFIED |
| Deterministic safety blocking | `app/services/safety_supervisor.py` (`SafetySupervisor`) | `tests/test_safety_supervisor.py`; 8/8 expected detections and 3/3 unsafe-discharge blocks | VERIFIED |
| Persisted Action Trace | `app/services/encounter_state_machine.py`; `get_action_trace_logic` in `app/streamlit_services.py` | Trace, persistence, and GOAI tests; 152/152 expected actions recorded | VERIFIED |
| Formative learning diagnosis and focused retry | `app/services/learning_diagnosis_service.py` (`LearningDiagnosisService`); learning service endpoints | `tests/test_learning_diagnosis.py` covers multidimensional profile, hints, fallback, resume, and retry | VERIFIED |
| Offline/no-API demo | `app/providers/mock_provider.py` (`MockProvider`) and provider factory | Mock full-encounter test; GOAI no-API scenario 1/1 with network disabled | VERIFIED |
| Gemini provider | `app/providers/gemini_provider.py` (`GeminiProvider`) | Provider selection is covered in the suite; no external Gemini request was made in this audit | PARTIAL |
| Ollama provider | `app/providers/ollama_provider.py` (`OllamaProvider`) | Provider selection is covered in the suite; no running Ollama server was required or tested in this audit | PARTIAL |
| Explainable formative OSCE scoring | `app/evaluation/osce_metrics.py` (`rule_based_rubric_scorer`, `benchmark_metric_calculator`) | 10 authored transcript benchmark: MAE 19.1, pass/fail agreement 0.7, 3 false fails | VERIFIED — formative only |
| Learner/instructor state separation | Learner schemas, projections, and `APP_ROLE` checks across `app/` | `tests/test_learner_state_isolation.py` exercises hidden-state exclusion and role gating | VERIFIED — local role gate, not authentication |
| Synthetic educational cases and no patient-care role | `case_templates/**`; README safety/data sections | README, documentation, and evaluation reports consistently state the restriction | VERIFIED within repository scope |

## Claims intentionally not made

| Unsupported or bounded statement | Treatment in repository |
|---|---|
| Clinical diagnosis, treatment advice, medical-device use, or patient-care decision support | Explicitly disclaimed in README and evaluation materials. |
| Certified or high-stakes OSCE scoring | Explicitly disclaimed; imperfect benchmark results are retained. |
| Clinical validation or educational-effectiveness validation | Not claimed; metrics are labelled internal authored regression evidence. |
| Production security authentication for instructor mode | Not claimed; documentation states that the role flag is for controlled local/separate deployment. |
| Performance of optional cloud/local LLMs | Not inferred from the deterministic MockProvider evaluation. |

## Audit conclusion

No active README or documentation claim was found without a corresponding implementation boundary. The two optional provider claims are deliberately `PARTIAL` because this audit verified their code paths but did not make external network/service calls. The OSCE scorer remains a transparent regression aid, not a high-stakes assessment claim.
