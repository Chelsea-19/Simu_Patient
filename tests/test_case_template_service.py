from __future__ import annotations


def test_simu_engine_initializes_case_template_with_mock_provider(monkeypatch, tmp_path):
    db_path = tmp_path / "simupatient-case-test.db"
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    from sqlmodel import Session

    from app.core.config import get_settings
    import app.db.session as db_session
    from app.db.session import _get_engine, init_db
    from app.providers.factory import get_llm_provider
    from app.services.case_loader import load_case_by_id
    from app.services.simu_engine import SimuEngine

    get_settings.cache_clear()
    db_session._engine = None
    init_db()

    case = load_case_by_id("chest_pain_001")
    engine = SimuEngine(provider=get_llm_provider())

    with Session(_get_engine()) as session:
        created = engine.generate_patient_from_case_template(case=case, session=session)
        reply = engine.chat(
            patient_id=created["id"],
            user_input="When did the chest pain start?",
            history=[{"role": "assistant", "content": created["opening_statement"]}],
            session=session,
        )

    assert created["profile"]["source"] == "case_template"
    assert created["profile"]["case_id"] == "chest_pain_001"
    assert created["opening_statement"] == case.opening_statement
    assert isinstance(reply, str)
    assert reply
