from __future__ import annotations

import json

import pytest


def _configure_runtime(monkeypatch, tmp_path, *, role: str = "instructor") -> None:
    db_path = tmp_path / f"phase5-teacher-{role}.db"
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("APP_ROLE", role)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    from app.core.config import get_settings
    import app.db.session as db_session
    from app.db.session import init_db

    get_settings.cache_clear()
    db_session._engine = None
    init_db()


def _complete_round(patient, state, question: str, *, include_ecg: bool, use_hint: bool = False):
    from app.streamlit_services import (
        consultation_chat_logic,
        evaluate_consultation_logic,
        finish_encounter_logic,
        order_ecg_logic,
        order_lab_test_logic,
        request_hint_logic,
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
    if use_hint:
        request_hint_logic(state["session_id"], 1)
    request_vital_signs_logic(state["session_id"])
    if include_ecg:
        order_ecg_logic(state["session_id"])
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


def test_teacher_dashboard_contains_sessions_trace_safety_hints_and_progress(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)
    from app.streamlit_services import (
        create_patient_from_case_logic,
        export_teacher_dashboard_logic,
        get_teacher_dashboard_logic,
        start_encounter_logic,
        start_focused_retry_logic,
    )

    first_patient = create_patient_from_case_logic("chest_pain_001")
    first_state = start_encounter_logic(
        patient_id=first_patient["id"],
        learner_id="teacher-demo-learner",
        case_id="chest_pain_001",
        training_goal="Initial teacher dashboard attempt",
        difficulty="intermediate",
    )
    first_result = _complete_round(
        first_patient,
        first_state,
        "When did the pain start?",
        include_ecg=False,
        use_hint=True,
    )
    retry = start_focused_retry_logic(first_state["session_id"])
    second_result = _complete_round(
        retry["patient"],
        retry["encounter"],
        (
            "I understand this is worrying. When did the pressure start, how severe is it, "
            "does it radiate, do you feel sweaty or short of breath, do you smoke or have "
            "hypertension or family history, and do you use cocaine or stimulants?"
        ),
        include_ecg=True,
    )

    dashboard = get_teacher_dashboard_logic("teacher-demo-learner")
    assert dashboard["available_learners"] == ["teacher-demo-learner"]
    assert len(dashboard["records"]) == 2
    first, second = dashboard["records"]
    assert first["overall_score"] == first_result.score
    assert second["overall_score"] == second_result.score
    assert len(first["dimension_scores"]) == 9
    assert first["action_trace"][-1]["tool_name"] == "complete_assessment"
    assert first["hints_used"] == [1]
    assert "critical_ecg_not_reviewed" in first["safety_events"]
    assert second["retry_of_session_id"] == first["session_id"]
    assert second["progress_report"] is not None
    assert second["progress_report"]["first_total_score"] == first_result.score
    assert "critical_ecg_not_reviewed" in second["progress_report"][
        "safety_critical_omissions_change"
    ]["resolved"]

    markdown = export_teacher_dashboard_logic("teacher-demo-learner", format="markdown")
    json_export = export_teacher_dashboard_logic("teacher-demo-learner", format="json")
    assert "# SimuPatient Teacher Training Report" in markdown
    assert "### Action Trace" in markdown
    assert "First vs second attempt" in markdown
    assert first["session_id"] in markdown
    exported = json.loads(json_export)
    assert len(exported["records"]) == 2
    assert exported["records"][1]["progress_report"]["interpretation"].startswith("当前 Demo")


def test_teacher_services_are_denied_in_learner_role(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path, role="learner")
    from app.streamlit_services import (
        export_teacher_dashboard_logic,
        get_teacher_dashboard_logic,
        list_case_templates_for_validation_logic,
    )

    with pytest.raises(PermissionError, match="APP_ROLE=instructor"):
        get_teacher_dashboard_logic()
    with pytest.raises(PermissionError, match="APP_ROLE=instructor"):
        export_teacher_dashboard_logic(format="json")
    with pytest.raises(PermissionError, match="APP_ROLE=instructor"):
        list_case_templates_for_validation_logic()


def test_instructor_streamlit_exposes_dashboard_exports_and_validator(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("streamlit_app.py", default_timeout=30).run()

    assert not at.exception
    assert "Instructor Case View" in {tab.label for tab in at.tabs}
    assert "Teacher Dashboard" in {header.value for header in at.header}
    assert "YAML Case Template Validator" in {header.value for header in at.header}
    download_labels = {button.label for button in at.get("download_button")}
    assert "Download Teacher Report (Markdown)" in download_labels
    assert "Download Teacher Report (JSON)" in download_labels
    next(button for button in at.button if button.label == "Validate YAML Template").click().run()
    assert not at.exception
    assert at.session_state["case_validation_result"]["valid"] is True
    assert at.session_state["case_validation_result"]["case_id"]
    download_labels = {button.label for button in at.get("download_button")}
    assert "Download Validation (Markdown)" in download_labels
    assert "Download Validation (JSON)" in download_labels
