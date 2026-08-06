from __future__ import annotations

import socket


def _configure_runtime(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "phase2-tools.db"
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("APP_ROLE", "learner")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    from app.core.config import get_settings
    import app.db.session as db_session
    from app.db.session import init_db

    get_settings.cache_clear()
    db_session._engine = None
    init_db()


def _create_patient_and_encounter(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)
    from app.streamlit_services import create_patient_from_case_logic, start_encounter_logic

    created = create_patient_from_case_logic("chest_pain_001")
    state = start_encounter_logic(
        patient_id=created["id"],
        learner_id="learner-phase2",
        case_id="chest_pain_001",
        training_goal="Acute chest pain clinical reasoning",
        difficulty="intermediate",
    )
    return created, state


def test_tool_results_are_loaded_from_yaml(monkeypatch, tmp_path):
    created, state = _create_patient_and_encounter(monkeypatch, tmp_path)

    from app.services.case_loader import load_case_by_id
    from app.streamlit_services import (
        consultation_chat_logic,
        order_ecg_logic,
        order_lab_test_logic,
        perform_physical_exam_logic,
        request_vital_signs_logic,
    )

    consultation_chat_logic(
        created["id"],
        "When did the pain start?",
        [],
        encounter_session_id=state["session_id"],
    )
    case = load_case_by_id("chest_pain_001")

    vitals = request_vital_signs_logic(state["session_id"])
    assert vitals["status"] == "success"
    assert vitals["result"] == case.vital_signs.result
    assert vitals["time_cost"] == case.vital_signs.time_cost

    exam = perform_physical_exam_logic(state["session_id"], "cardiovascular")
    assert exam["result"] == case.physical_examination["cardiovascular"].result

    ecg = order_ecg_logic(state["session_id"])
    assert ecg["result"] == case.investigations["ecg"].result

    troponin = order_lab_test_logic(state["session_id"], "troponin")
    assert troponin["result"] == case.investigations["troponin"].result
    assert troponin["result"]["value"] == "78 ng/L"


def test_nonexistent_test_returns_safe_error_and_is_traced(monkeypatch, tmp_path):
    created, state = _create_patient_and_encounter(monkeypatch, tmp_path)

    from app.streamlit_services import (
        consultation_chat_logic,
        get_action_trace_logic,
        order_lab_test_logic,
        request_vital_signs_logic,
    )

    consultation_chat_logic(
        created["id"],
        "Tell me about the pain.",
        [],
        encounter_session_id=state["session_id"],
    )
    request_vital_signs_logic(state["session_id"])
    result = order_lab_test_logic(state["session_id"], "invented_secret_panel")

    assert result["status"] == "error"
    assert result["result"] == {}
    assert result["evidence_unlocked"] == []
    assert "not configured" in result["learner_message"]
    trace = get_action_trace_logic(state["session_id"])
    assert trace[-1]["tool_name"] == "order_lab_test"
    assert trace[-1]["structured_action"]["status"] == "error"


def test_duplicate_investigation_returns_existing_result_without_extra_time(monkeypatch, tmp_path):
    created, state = _create_patient_and_encounter(monkeypatch, tmp_path)

    from app.streamlit_services import (
        consultation_chat_logic,
        get_encounter_state_logic,
        order_ecg_logic,
        request_vital_signs_logic,
    )

    consultation_chat_logic(
        created["id"],
        "When did this start?",
        [],
        encounter_session_id=state["session_id"],
    )
    request_vital_signs_logic(state["session_id"])
    first = order_ecg_logic(state["session_id"])
    time_after_first = get_encounter_state_logic(state["session_id"])["elapsed_time"]
    duplicate = order_ecg_logic(state["session_id"])
    time_after_duplicate = get_encounter_state_logic(state["session_id"])["elapsed_time"]

    assert first["status"] == "success"
    assert duplicate["status"] == "duplicate"
    assert duplicate["result"] == first["result"]
    assert duplicate["time_cost"] == 0
    assert duplicate["evidence_unlocked"] == []
    assert time_after_duplicate == time_after_first


def test_tool_called_in_wrong_stage_returns_clear_error(monkeypatch, tmp_path):
    _, state = _create_patient_and_encounter(monkeypatch, tmp_path)

    from app.streamlit_services import get_encounter_state_logic, order_ecg_logic

    result = order_ecg_logic(state["session_id"])
    restored = get_encounter_state_logic(state["session_id"])

    assert result["status"] == "error"
    assert result["current_stage"] == "CASE_INTRO"
    assert "not available during CASE_INTRO" in result["learner_message"]
    assert restored["current_stage"] == "CASE_INTRO"
    assert restored["tests_ordered"] == []


def test_every_action_is_appended_to_trace(monkeypatch, tmp_path):
    created, state = _create_patient_and_encounter(monkeypatch, tmp_path)

    from app.streamlit_services import (
        consultation_chat_logic,
        get_action_trace_logic,
        order_ecg_logic,
        perform_physical_exam_logic,
        request_hint_logic,
        request_vital_signs_logic,
    )

    order_ecg_logic(state["session_id"])
    consultation_chat_logic(
        created["id"],
        "Where is the pain?",
        [],
        encounter_session_id=state["session_id"],
    )
    request_vital_signs_logic(state["session_id"])
    perform_physical_exam_logic(state["session_id"], "cardiovascular")
    order_ecg_logic(state["session_id"])
    request_hint_logic(state["session_id"], 1)

    trace = get_action_trace_logic(state["session_id"])
    assert [entry["tool_name"] for entry in trace] == [
        "start_encounter",
        "order_ecg",
        "ask_history_question",
        "request_vital_signs",
        "perform_physical_exam",
        "order_ecg",
        "request_hint",
    ]
    assert len({entry["action_id"] for entry in trace}) == len(trace)
    assert all(entry["session_id"] == state["session_id"] for entry in trace)


def test_session_restores_without_losing_state_or_trace(monkeypatch, tmp_path):
    created, state = _create_patient_and_encounter(monkeypatch, tmp_path)

    from app.core.config import get_settings
    import app.db.session as db_session
    from app.streamlit_services import (
        consultation_chat_logic,
        get_action_trace_logic,
        get_encounter_state_logic,
        request_vital_signs_logic,
    )

    consultation_chat_logic(
        created["id"],
        "When did the pain begin?",
        [],
        encounter_session_id=state["session_id"],
    )
    request_vital_signs_logic(state["session_id"])
    before = get_encounter_state_logic(state["session_id"])
    trace_before = get_action_trace_logic(state["session_id"])

    db_session._engine.dispose()
    db_session._engine = None
    get_settings.cache_clear()

    restored = get_encounter_state_logic(state["session_id"])
    trace_after = get_action_trace_logic(state["session_id"])
    assert restored == before
    assert trace_after == trace_before


def test_mock_provider_completes_full_encounter_without_network(monkeypatch, tmp_path):
    created, state = _create_patient_and_encounter(monkeypatch, tmp_path)

    from app.streamlit_services import (
        consultation_chat_logic,
        evaluate_consultation_logic,
        finish_encounter_logic,
        get_action_trace_logic,
        get_encounter_state_logic,
        order_ecg_logic,
        order_lab_test_logic,
        perform_physical_exam_logic,
        request_vital_signs_logic,
        submit_differential_diagnosis_logic,
        submit_management_plan_logic,
    )

    original_connect = socket.socket.connect

    def blocked_connect(*args, **kwargs):
        raise RuntimeError("network disabled by Phase 2 test")

    socket.socket.connect = blocked_connect
    try:
        reply = consultation_chat_logic(
            created["id"],
            "When did the chest pressure start and where does it radiate?",
            [{"role": "assistant", "content": created["opening_statement"]}],
            encounter_session_id=state["session_id"],
        )
        request_vital_signs_logic(state["session_id"])
        perform_physical_exam_logic(state["session_id"], "cardiovascular")
        order_ecg_logic(state["session_id"])
        order_lab_test_logic(state["session_id"], "troponin")
        differential = submit_differential_diagnosis_logic(
            state["session_id"],
            ["acute coronary syndrome", "aortic dissection", "pulmonary embolism"],
        )
        management = submit_management_plan_logic(
            state["session_id"],
            {
                "disposition": "urgent emergency cardiology assessment",
                "monitoring": "continuous cardiac monitoring",
                "initial_management": "treat as high-risk acute coronary syndrome",
                "safety_net": "do not discharge; escalate deterioration immediately",
            },
        )
        finished = finish_encounter_logic(state["session_id"])
        assessment = evaluate_consultation_logic(
            created["id"],
            [
                {"role": "assistant", "content": created["opening_statement"]},
                {"role": "user", "content": "When did the chest pressure start?"},
                {"role": "assistant", "content": reply},
            ],
            encounter_session_id=state["session_id"],
        )
    finally:
        socket.socket.connect = original_connect

    completed = get_encounter_state_logic(state["session_id"])
    trace = get_action_trace_logic(state["session_id"])
    assert differential["status"] == "success"
    assert management["status"] == "success"
    assert finished["status"] == "success"
    assert finished["current_stage"] == "ASSESSMENT"
    assert assessment.score > 0
    assert completed["current_stage"] == "COMPLETED"
    assert completed["assessment_status"] == "completed"
    assert completed["tests_ordered"] == ["vital_signs", "ecg", "troponin"]
    assert completed["physical_exams_completed"] == ["cardiovascular"]
    assert completed["differential_diagnoses"][0] == "acute coronary syndrome"
    assert completed["management_plan"]["disposition"].startswith("urgent")
    assert trace[-1]["tool_name"] == "complete_assessment"
    assert trace[-1]["score_event"]["formative_score"] == assessment.score


def test_streamlit_workbench_exposes_state_tools_evidence_and_trace(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)

    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("streamlit_app.py", default_timeout=25).run()
    at.radio[0].set_value("Case template").run()
    next(button for button in at.button if button.label == "Start Case Consultation").click().run()

    assert not at.exception
    assert at.session_state["encounter_session_id"]
    assert at.session_state["encounter_state"]["current_stage"] == "CASE_INTRO"
    assert {(metric.label, metric.value) for metric in at.metric} >= {
        ("Current stage", "CASE_INTRO"),
        ("Elapsed time", "0 min"),
    }
    expected_buttons = {
        "Request Vital Signs",
        "Order ECG",
        "Perform Exam",
        "Order Lab",
        "Submit Differential Diagnosis",
        "Submit Management Plan",
        "Request Hint",
        "Finish Encounter and Evaluate",
    }
    assert expected_buttons.issubset({button.label for button in at.button})
    assert len(at.dataframe) == 1
    assert len(at.json) == 0
