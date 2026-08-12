from __future__ import annotations


def _configure_runtime(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "phase4-retry.db"
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("APP_ROLE", "learner")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    from app.core.config import get_settings
    import app.db.session as db_session
    from app.db.session import init_db

    get_settings.cache_clear()
    db_session._engine = None
    init_db()


def _complete_round(patient, state, question: str, *, include_ecg: bool, include_troponin: bool):
    from app.streamlit_services import (
        consultation_chat_logic,
        evaluate_consultation_logic,
        finish_encounter_logic,
        order_ecg_logic,
        order_lab_test_logic,
        request_vital_signs_logic,
        submit_differential_diagnosis_logic,
        submit_management_plan_logic,
    )

    history = [{"role": "assistant", "content": patient["opening_statement"]}]
    reply = consultation_chat_logic(
        patient["id"],
        question,
        history,
        encounter_session_id=state["session_id"],
    )
    history.extend([{"role": "user", "content": question}, {"role": "assistant", "content": reply}])
    request_vital_signs_logic(state["session_id"])
    if include_ecg:
        order_ecg_logic(state["session_id"])
    if include_troponin:
        order_lab_test_logic(state["session_id"], "troponin")
    submit_differential_diagnosis_logic(
        state["session_id"],
        ["acute coronary syndrome", "aortic dissection", "pulmonary embolism"],
    )
    submit_management_plan_logic(
        state["session_id"],
        {
            "disposition": "urgent hospital admission for monitored cardiology care",
            "initial_management": "emergency monitoring and reassessment",
            "safety_net": "escalate immediately if symptoms worsen or the patient deteriorates",
        },
    )
    assert finish_encounter_logic(state["session_id"])["status"] == "success"
    return evaluate_consultation_logic(
        patient["id"],
        history,
        encounter_session_id=state["session_id"],
    )


def test_focused_retry_resets_case_state_and_generates_two_round_comparison(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)
    from app.streamlit_services import (
        compare_learning_progress_logic,
        create_patient_from_case_logic,
        get_encounter_state_logic,
        start_encounter_logic,
        start_focused_retry_logic,
    )

    first_patient = create_patient_from_case_logic("chest_pain_001")
    first_state = start_encounter_logic(
        patient_id=first_patient["id"],
        learner_id="retry-learner",
        case_id="chest_pain_001",
        training_goal="Initial chest-pain attempt",
        difficulty="intermediate",
    )
    first_result = _complete_round(
        first_patient,
        first_state,
        "When did the pain start?",
        include_ecg=False,
        include_troponin=True,
    )

    retry = start_focused_retry_logic(first_state["session_id"])
    second_patient = retry["patient"]
    second_state = retry["encounter"]

    assert second_patient["id"] != first_patient["id"]
    assert second_state["session_id"] != first_state["session_id"]
    assert second_state["retry_of_session_id"] == first_state["session_id"]
    assert second_state["focused_retry"] is True
    assert second_state["focus_skills"] == first_result.remediation_plan["priority_skills"]
    assert second_state["history_turn_limit"] == 6
    assert second_state["evidence_unlocked"] == []
    assert second_state["tests_ordered"] == []
    assert second_state["questions_asked"] == []

    second_result = _complete_round(
        second_patient,
        second_state,
        (
            "I understand this is worrying. When did the pressure start, how severe is it, "
            "does it radiate to your arm, do you have sweating or shortness of breath, do you "
            "smoke or have hypertension or family history, and do you use cocaine, recreational "
            "drugs, or stimulants?"
        ),
        include_ecg=True,
        include_troponin=True,
    )
    progress = compare_learning_progress_logic(
        first_state["session_id"],
        second_state["session_id"],
    )
    restored_retry = get_encounter_state_logic(second_state["session_id"])

    assert progress["first_total_score"] == first_result.score
    assert progress["second_total_score"] == second_result.score
    assert progress["second_total_score"] > progress["first_total_score"]
    assert progress["dimension_changes"]["history_taking"] > 0
    assert progress["dimension_changes"]["investigation_selection"] > 0
    assert "critical_ecg_not_reviewed" in progress["safety_critical_omissions_change"]["resolved"]
    assert progress["first_hints_used"] == 0
    assert progress["second_hints_used"] == 0
    assert restored_retry["current_stage"] == "COMPLETED"
    assert "当前 Demo 中的个体训练表现对比" in progress["interpretation"]
    assert "真实教学效果证明" in progress["interpretation"]
