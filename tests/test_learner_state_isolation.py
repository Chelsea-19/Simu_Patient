from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.schemas.case_views import LEARNER_FORBIDDEN_FIELDS, LearnerVisibleCase


def _configure_runtime(monkeypatch, tmp_path, *, role: str = "learner") -> None:
    db_path = tmp_path / f"state-isolation-{role}.db"
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("APP_ROLE", role)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    from app.core.config import get_settings
    import app.db.session as db_session
    from app.db.session import init_db

    get_settings.cache_clear()
    db_session._engine = None
    init_db()


def _create_chest_pain_case():
    from app.streamlit_services import create_patient_from_case_logic

    return create_patient_from_case_logic("chest_pain_001")


def _serialized(payload) -> str:
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(mode="json")
    return json.dumps(payload, ensure_ascii=False).lower()


def test_learner_schema_forbids_instructor_only_fields():
    allowed = {
        "patient_id": 1,
        "case_id": "chest_pain_001",
        "age": "58",
        "gender": "male",
        "encounter_setting": "Emergency Medicine",
        "chief_complaint": "Chest pain for 2 hours",
        "opening_statement": "Doctor, I have chest pressure.",
        "unlocked_evidence": [],
    }
    LearnerVisibleCase.model_validate(allowed)

    for forbidden in LEARNER_FORBIDDEN_FIELDS:
        with pytest.raises(ValidationError):
            LearnerVisibleCase.model_validate({**allowed, forbidden: "must not pass"})


def test_learner_case_response_contains_no_hidden_answers_questions_or_rubric(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)
    created = _create_chest_pain_case()

    assert set(created) == {"id", "case", "opening_statement"}
    assert set(created["case"]) == {
        "patient_id",
        "case_id",
        "age",
        "gender",
        "encounter_setting",
        "chief_complaint",
        "opening_statement",
        "unlocked_evidence",
    }

    serialized = _serialized(created)
    for forbidden in LEARNER_FORBIDDEN_FIELDS:
        assert forbidden not in serialized
    assert "recent cocaine use" not in serialized
    assert "acute coronary syndrome" not in serialized
    assert "recreational drug use" not in serialized
    assert '"history_taking": 40' not in serialized


def test_normal_learner_export_cannot_access_unreleased_hidden_state(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)
    created = _create_chest_pain_case()

    from app.streamlit_services import export_learner_case_logic

    exported = export_learner_case_logic(created["id"])
    exported_payload = json.loads(exported)
    LearnerVisibleCase.model_validate(exported_payload)

    serialized = exported.lower()
    for forbidden in LEARNER_FORBIDDEN_FIELDS:
        assert forbidden not in serialized
    assert "cocaine" not in serialized
    assert "acute coronary syndrome" not in serialized


def test_instructor_case_view_is_role_gated_and_can_read_full_case(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)
    created = _create_chest_pain_case()

    from app.core.config import get_settings
    from app.streamlit_services import get_instructor_case_view_logic

    with pytest.raises(PermissionError, match="APP_ROLE=instructor"):
        get_instructor_case_view_logic(created["id"])

    monkeypatch.setenv("APP_ROLE", "instructor")
    get_settings.cache_clear()
    view = get_instructor_case_view_logic(created["id"])

    assert view.full_case.profile["hidden_information"][0]["item"] == "recent cocaine use"
    assert "acute coronary syndrome" in view.full_case.profile["red_flags"]
    assert "recreational drug use" in view.full_case.profile["expected_key_questions"]
    assert view.rubric["history_taking"] == 40


def test_instructor_view_reads_existing_trace_unlock_and_scoring_evidence(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)
    created = _create_chest_pain_case()

    from app.core.config import get_settings
    from app.streamlit_services import (
        consultation_chat_logic,
        evaluate_consultation_logic,
        get_instructor_case_view_logic,
    )

    reply = consultation_chat_logic(
        created["id"],
        "Do you use recreational drugs or stimulants?",
        [{"role": "assistant", "content": created["opening_statement"]}],
    )
    assert "cocaine" in reply.lower()
    evaluate_consultation_logic(
        created["id"],
        [
            {"role": "assistant", "content": created["opening_statement"]},
            {"role": "user", "content": "Do you use recreational drugs or stimulants?"},
            {"role": "assistant", "content": reply},
        ],
    )

    monkeypatch.setenv("APP_ROLE", "instructor")
    get_settings.cache_clear()
    view = get_instructor_case_view_logic(created["id"])

    assert len(view.learner_action_trace) == 1
    assert view.unlock_history[0]["hidden_info_revealed"] is True
    assert view.unlock_history[0]["revealed_hidden_items"] == ["recent cocaine use"]
    assert len(view.scoring_evidence) == 1


def test_unrelated_question_does_not_unlock_hidden_state_but_direct_question_does(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)
    created = _create_chest_pain_case()

    from sqlmodel import Session

    from app.db.session import _get_engine
    from app.repositories.session_state_repository import SessionStateRepository
    from app.streamlit_services import consultation_chat_logic

    unrelated_reply = consultation_chat_logic(created["id"], "How are you feeling today?", [])
    assert "chest" in unrelated_reply.lower()
    assert "cocaine" not in unrelated_reply.lower()
    with Session(_get_engine()) as session:
        state = SessionStateRepository(session).get_or_create_by_patient_id(created["id"])
        assert state.hidden_info_revealed is False

    direct_reply = consultation_chat_logic(
        created["id"],
        "Have you used cocaine, recreational drugs, or stimulants recently?",
        [],
    )
    assert "cocaine" in direct_reply.lower()
    with Session(_get_engine()) as session:
        state = SessionStateRepository(session).get_or_create_by_patient_id(created["id"])
        assert state.hidden_info_revealed is True


def test_learner_streamlit_state_and_reset_do_not_carry_hidden_state(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)

    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("streamlit_app.py", default_timeout=20).run()
    at.radio[0].set_value("Case template").run()
    start_button = next(button for button in at.button if button.label == "Start structured encounter")
    start_button.click().run()

    assert not at.exception
    first_patient_id = at.session_state["patient_id"]
    learner_case = at.session_state["learner_case"]
    assert LEARNER_FORBIDDEN_FIELDS.isdisjoint(learner_case)
    assert "cocaine" not in _serialized(learner_case)
    assert len(at.json) == 0
    with pytest.raises(KeyError):
        _ = at.session_state["patient_profile"]

    reset_button = next(button for button in at.button if button.label == "Reset session data")
    reset_button.click().run()
    next(button for button in at.button if button.label == "Confirm reset").click().run()
    assert at.session_state["patient_id"] is None
    assert at.session_state["learner_case"] is None
    assert at.session_state["chat_history"] == []
    assert at.session_state["assessment"] is None

    at.radio[0].set_value("Case template").run()
    start_button = next(button for button in at.button if button.label == "Start structured encounter")
    start_button.click().run()
    assert at.session_state["patient_id"] != first_patient_id
    assert "cocaine" not in _serialized(at.session_state["learner_case"])


def test_default_app_role_is_learner(monkeypatch):
    monkeypatch.delenv("APP_ROLE", raising=False)
    from app.core.config import get_settings

    get_settings.cache_clear()
    assert get_settings().APP_ROLE == "learner"
    assert get_settings().is_instructor is False


def test_all_existing_cases_project_to_the_same_safe_learner_contract(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)

    from app.services.case_loader import get_available_cases
    from app.streamlit_services import create_patient_from_case_logic

    cases = get_available_cases()
    assert len(cases) == 20
    for case in cases:
        created = create_patient_from_case_logic(case.case_id)
        LearnerVisibleCase.model_validate(created["case"])
        serialized = _serialized(created)
        assert LEARNER_FORBIDDEN_FIELDS.isdisjoint(created["case"])
        for forbidden in LEARNER_FORBIDDEN_FIELDS:
            assert forbidden not in serialized


def test_instructor_streamlit_role_exposes_controlled_review_tab(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path, role="instructor")

    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("streamlit_app.py", default_timeout=20).run()
    assert "Instructor" in [tab.label for tab in at.tabs]
    at.radio[0].set_value("Case template").run()
    start_button = next(button for button in at.button if button.label == "Start structured encounter")
    start_button.click().run()

    assert not at.exception
    assert len(at.json) == 5
    assert any("recent cocaine use" in str(item.value) for item in at.json)
    assert LEARNER_FORBIDDEN_FIELDS.isdisjoint(at.session_state["learner_case"])


def test_json_parse_errors_suppress_hidden_raw_content_from_message_and_logs(caplog):
    from app.core.exceptions import LLMJsonParseError
    from app.providers.base import BaseLLMProvider

    secret = "recent cocaine use must stay instructor-only"
    with caplog.at_level("ERROR"):
        with pytest.raises(LLMJsonParseError) as exc_info:
            BaseLLMProvider.parse_json_response(secret)

    assert secret not in str(exc_info.value)
    assert secret not in caplog.text
    assert "raw content suppressed" in str(exc_info.value)


def test_patient_agent_prompt_cannot_see_hidden_fact_before_deterministic_unlock(monkeypatch, tmp_path):
    _configure_runtime(monkeypatch, tmp_path)

    from sqlmodel import Session

    from app.db.session import _get_engine
    from app.providers.mock_provider import MockProvider
    from app.services.case_loader import load_case_by_id
    from app.services.simu_engine import SimuEngine

    class CapturingMockProvider(MockProvider):
        def __init__(self):
            super().__init__()
            self.last_text_messages = []

        def generate_text(self, messages, *, temperature=None):
            self.last_text_messages = messages
            return super().generate_text(messages, temperature=temperature)

    provider = CapturingMockProvider()
    engine = SimuEngine(provider=provider)
    with Session(_get_engine()) as session:
        created = engine.generate_patient_from_case_template(
            case=load_case_by_id("chest_pain_001"),
            session=session,
        )
        engine.chat(
            patient_id=created["id"],
            user_input="How are you feeling today?",
            history=[],
            session=session,
        )
        locked_prompt = provider.last_text_messages[0]["content"].lower()
        assert "recent cocaine use" not in locked_prompt
        assert "expected_key_questions" not in locked_prompt
        assert "scoring_rubric" not in locked_prompt
        assert "acute coronary syndrome" not in locked_prompt

        engine.chat(
            patient_id=created["id"],
            user_input="Have you used cocaine or recreational stimulants?",
            history=[],
            session=session,
        )
        unlocked_prompt = provider.last_text_messages[0]["content"].lower()
        assert "recent cocaine use" in unlocked_prompt
        assert "expected_key_questions" not in unlocked_prompt
        assert "scoring_rubric" not in unlocked_prompt
