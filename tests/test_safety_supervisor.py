from __future__ import annotations


def _configure_runtime(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "phase3-safety.db"
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("APP_ROLE", "learner")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    from app.core.config import get_settings
    import app.db.session as db_session
    from app.db.session import init_db

    get_settings.cache_clear()
    db_session._engine = None
    init_db()


def _start_case(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)
    from app.streamlit_services import create_patient_from_case_logic, start_encounter_logic

    patient = create_patient_from_case_logic("chest_pain_001")
    state = start_encounter_logic(
        patient_id=patient["id"],
        learner_id="learner-phase3",
        case_id="chest_pain_001",
        training_goal="Safe disposition of high-risk chest pain",
        difficulty="intermediate",
    )
    return patient, state


def _reach_management(patient, state, *, include_ecg: bool, focused_history: bool = True):
    from app.streamlit_services import (
        consultation_chat_logic,
        order_ecg_logic,
        order_lab_test_logic,
        request_vital_signs_logic,
        submit_differential_diagnosis_logic,
    )

    question = (
        "Does the pain radiate, and do you smoke or have hypertension, a family history, "
        "or use cocaine, recreational drugs, or stimulants?"
        if focused_history
        else "When did the pain start?"
    )
    consultation_chat_logic(
        patient["id"],
        question,
        [{"role": "assistant", "content": patient["opening_statement"]}],
        encounter_session_id=state["session_id"],
    )
    request_vital_signs_logic(state["session_id"])
    if include_ecg:
        order_ecg_logic(state["session_id"])
    else:
        order_lab_test_logic(state["session_id"], "troponin")
    submit_differential_diagnosis_logic(
        state["session_id"],
        ["acute coronary syndrome", "aortic dissection", "pulmonary embolism"],
    )


def _safe_plan() -> dict[str, str]:
    return {
        "disposition": "urgent hospital admission for cardiology review and monitored care",
        "initial_management": "continuous monitoring and emergency treatment while reassessing",
        "safety_net": "escalate immediately if pain or breathing worsens or the patient deteriorates",
    }


def test_high_risk_home_plan_without_ecg_is_blocked_and_traced(monkeypatch, tmp_path):
    patient, state = _start_case(monkeypatch, tmp_path)
    _reach_management(patient, state, include_ecg=False)

    from app.streamlit_services import (
        finish_encounter_logic,
        get_action_trace_logic,
        get_encounter_state_logic,
        submit_management_plan_logic,
    )

    submit_management_plan_logic(
        state["session_id"],
        {
            "disposition": "discharge home to observe symptoms",
            "initial_management": "rest at home",
            "safety_net": "return if symptoms worsen",
        },
    )
    result = finish_encounter_logic(state["session_id"])
    review = result["result"]["safety_review"]
    restored = get_encounter_state_logic(state["session_id"])
    trace = get_action_trace_logic(state["session_id"])

    assert result["status"] == "error"
    assert review["risk_level"] == "high"
    assert review["decision"] == "block_completion"
    assert "unsafe_home_disposition" in review["triggered_rules"]
    assert "critical_ecg_not_reviewed" in review["triggered_rules"]
    assert "urgent_escalation_missing" in review["triggered_rules"]
    assert review["missing_critical_actions"]
    assert review["recommended_reflection_questions"]
    assert "acute coronary syndrome" not in review["learner_feedback"].lower()
    assert "correct answer" not in review["learner_feedback"].lower()
    assert restored["current_stage"] == "MANAGEMENT"
    assert restored["assessment_status"] == "blocked_by_safety"
    assert trace[-1]["structured_action"]["status"] == "blocked"
    assert trace[-1]["safety_event"] == review["triggered_rules"]


def test_blocked_encounter_can_be_corrected_and_completed(monkeypatch, tmp_path):
    patient, state = _start_case(monkeypatch, tmp_path)
    _reach_management(patient, state, include_ecg=False)

    from app.streamlit_services import (
        finish_encounter_logic,
        get_action_trace_logic,
        get_encounter_state_logic,
        order_ecg_logic,
        submit_management_plan_logic,
    )

    submit_management_plan_logic(
        state["session_id"],
        {"disposition": "home", "initial_management": "observe", "safety_net": "return if worse"},
    )
    assert finish_encounter_logic(state["session_id"])["status"] == "error"

    assert order_ecg_logic(state["session_id"])["status"] == "success"
    submit_management_plan_logic(state["session_id"], _safe_plan())
    result = finish_encounter_logic(state["session_id"])
    restored = get_encounter_state_logic(state["session_id"])
    trace = get_action_trace_logic(state["session_id"])

    assert result["status"] == "success"
    assert result["result"]["safety_review"]["decision"] == "allow_completion"
    assert restored["current_stage"] == "ASSESSMENT"
    assert restored["assessment_status"] == "ready"
    finish_events = [entry for entry in trace if entry["tool_name"] == "finish_encounter"]
    assert [entry["structured_action"]["status"] for entry in finish_events] == [
        "blocked",
        "success",
    ]


def test_reasonable_plan_passes_while_nonblocking_history_gaps_remain_explainable(
    monkeypatch, tmp_path
):
    patient, state = _start_case(monkeypatch, tmp_path)
    _reach_management(patient, state, include_ecg=True, focused_history=False)

    from app.streamlit_services import finish_encounter_logic, submit_management_plan_logic

    submit_management_plan_logic(state["session_id"], _safe_plan())
    result = finish_encounter_logic(state["session_id"])
    review = result["result"]["safety_review"]

    assert result["status"] == "success"
    assert review["decision"] == "allow_completion"
    assert "pain_radiation_not_assessed" in review["triggered_rules"]
    assert "cardiovascular_risk_factors_not_assessed" in review["triggered_rules"]
    assert "drug_or_stimulant_use_not_assessed" in review["triggered_rules"]
    assert "unsafe_home_disposition" not in review["triggered_rules"]
    assert review["recommended_reflection_questions"] == []
