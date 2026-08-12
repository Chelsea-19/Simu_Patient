from __future__ import annotations


EXPECTED_DIMENSIONS = {
    "history_taking",
    "communication",
    "clinical_reasoning",
    "red_flag_recognition",
    "investigation_selection",
    "management_safety",
    "empathy",
    "closure_and_safety_netting",
    "efficiency",
}


def _configure_runtime(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "phase4-learning.db"
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("APP_ROLE", "learner")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    from app.core.config import get_settings
    import app.db.session as db_session
    from app.db.session import init_db

    get_settings.cache_clear()
    db_session._engine = None
    init_db()


def _reach_assessment(monkeypatch, tmp_path, *, use_hints: bool = False):
    _configure_runtime(monkeypatch, tmp_path)
    from app.streamlit_services import (
        consultation_chat_logic,
        create_patient_from_case_logic,
        finish_encounter_logic,
        order_lab_test_logic,
        request_hint_logic,
        request_vital_signs_logic,
        start_encounter_logic,
        submit_differential_diagnosis_logic,
        submit_management_plan_logic,
    )

    patient = create_patient_from_case_logic("chest_pain_001")
    state = start_encounter_logic(
        patient_id=patient["id"],
        learner_id="phase4-learner",
        case_id="chest_pain_001",
        training_goal="Diagnose learning gaps",
        difficulty="intermediate",
    )
    reply = consultation_chat_logic(
        patient["id"],
        "When did the pain start?",
        [{"role": "assistant", "content": patient["opening_statement"]}],
        encounter_session_id=state["session_id"],
    )
    hint_results = []
    if use_hints:
        hint_results = [request_hint_logic(state["session_id"], level) for level in (1, 2, 3)]
    request_vital_signs_logic(state["session_id"])
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
            "safety_net": "escalate immediately if pain worsens or the patient deteriorates",
        },
    )
    assert finish_encounter_logic(state["session_id"])["status"] == "success"
    history = [
        {"role": "assistant", "content": patient["opening_statement"]},
        {"role": "user", "content": "When did the pain start?"},
        {"role": "assistant", "content": reply},
    ]
    return patient, state, history, hint_results


def test_completed_training_generates_traceable_nine_dimension_profile(monkeypatch, tmp_path):
    patient, state, history, _ = _reach_assessment(monkeypatch, tmp_path)
    from app.streamlit_services import evaluate_consultation_logic, get_learning_diagnosis_logic

    result = evaluate_consultation_logic(
        patient["id"],
        history,
        encounter_session_id=state["session_id"],
    )
    persisted = get_learning_diagnosis_logic(state["session_id"])
    profile = result.learning_profile

    assert profile is not None
    assert set(profile["dimensions"]) == EXPECTED_DIMENSIONS
    assert result.score == profile["overall_score"]
    assert persisted["profile"] == profile
    assert 1 <= len(profile["lowest_dimensions"]) <= 3
    for detail in profile["dimensions"].values():
        assert 0 <= detail["score"] <= 100
        assert 0 <= detail["deterministic_score"] <= 100
        assert -5 <= detail["qualitative_adjustment"] <= 5
        assert detail["scoring_evidence"]
        assert isinstance(detail["strengths"], list)
        assert isinstance(detail["omissions"], list)
        assert isinstance(detail["risks"], list)
        assert detail["recommended_practice"]

    remediation = result.remediation_plan
    assert remediation is not None
    assert remediation["priority_skills"] == profile["lowest_dimensions"]
    assert remediation["recommended_case"] == "chest_pain_001"
    assert remediation["specific_actions_to_practice"]
    assert remediation["success_criteria"]


def test_three_hint_levels_are_layered_traced_and_reduce_efficiency(monkeypatch, tmp_path):
    patient, state, history, hints = _reach_assessment(monkeypatch, tmp_path, use_hints=True)
    from app.streamlit_services import (
        evaluate_consultation_logic,
        get_action_trace_logic,
        get_encounter_state_logic,
    )

    assert "life-threatening category" in hints[0]["learner_message"]
    assert "cardiovascular risks" in hints[1]["learner_message"]
    assert "focused acute chest-pain history" in hints[2]["learner_message"]
    result = evaluate_consultation_logic(
        patient["id"],
        history,
        encounter_session_id=state["session_id"],
    )
    restored = get_encounter_state_logic(state["session_id"])
    trace = get_action_trace_logic(state["session_id"])

    assert restored["hints_used"] == [1, 2, 3]
    assert [entry["hint_level"] for entry in trace if entry["tool_name"] == "request_hint"] == [
        1,
        2,
        3,
    ]
    efficiency = result.learning_profile["dimensions"]["efficiency"]
    assert "penalty 17" in " ".join(efficiency["scoring_evidence"])
    assert efficiency["deterministic_score"] < 100


def test_learning_profile_has_template_fallback_when_llm_fails(monkeypatch, tmp_path):
    patient, state, history, _ = _reach_assessment(monkeypatch, tmp_path)
    from sqlmodel import Session

    from app.db.session import _get_engine
    from app.services.simu_engine import SimuEngine

    class FailingAssessmentProvider:
        def generate_json(self, messages, **kwargs):
            raise RuntimeError("simulated LLM failure")

        def generate_text(self, messages, **kwargs):
            raise RuntimeError("simulated LLM failure")

    with Session(_get_engine()) as session:
        result = SimuEngine(provider=FailingAssessmentProvider()).evaluate(
            patient_id=patient["id"],
            history=history,
            session=session,
            encounter_session_id=state["session_id"],
        )

    assert result.learning_profile is not None
    assert set(result.learning_profile["dimensions"]) == EXPECTED_DIMENSIONS
    assert result.feedback == "Completed consultation."
    assert result.learning_profile["dimensions"]["communication"]["qualitative_adjustment"] == 0
    assert result.learning_profile["dimensions"]["empathy"]["qualitative_adjustment"] == 0
    assert result.remediation_plan["priority_skills"]


def test_streamlit_resume_displays_learning_profile_and_retry_action(monkeypatch, tmp_path):
    patient, state, history, _ = _reach_assessment(monkeypatch, tmp_path)
    from app.streamlit_services import evaluate_consultation_logic
    from streamlit.testing.v1 import AppTest

    evaluate_consultation_logic(
        patient["id"],
        history,
        encounter_session_id=state["session_id"],
    )
    at = AppTest.from_file("streamlit_app.py", default_timeout=30).run()
    next(item for item in at.text_input if item.label == "Session ID").set_value(
        state["session_id"]
    )
    next(button for button in at.button if button.label == "Resume encounter").click().run()

    assert not at.exception
    assert "Trace-grounded learning profile" in {item.value for item in at.subheader}
    assert "Personalized remediation plan" in {item.value for item in at.subheader}
    assert "Start focused retry" in {button.label for button in at.button}
    assert at.session_state["assessment"]["learning_profile"]["overall_score"] > 0
