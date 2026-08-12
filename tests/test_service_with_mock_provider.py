from __future__ import annotations


def test_simu_engine_runs_with_mock_provider(monkeypatch, tmp_path):
    db_path = tmp_path / "simupatient-test.db"
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    from sqlmodel import Session

    from app.core.config import get_settings
    import app.db.session as db_session
    from app.db.session import _get_engine, init_db
    from app.providers.factory import get_llm_provider
    from app.providers.mock_provider import MockProvider
    from app.services.simu_engine import SimuEngine

    get_settings.cache_clear()
    db_session._engine = None
    init_db()

    provider = get_llm_provider()
    assert isinstance(provider, MockProvider)

    engine = SimuEngine(provider=provider)
    with Session(_get_engine()) as session:
        created = engine.generate_patient(
            seed_text="A patient with intermittent headache.",
            template_id=None,
            session=session,
        )

        reply = engine.chat(
            patient_id=created["id"],
            user_input="What brings you in today?",
            history=[],
            session=session,
        )

        assessment = engine.evaluate(
            patient_id=created["id"],
            history=[
                {"role": "user", "content": "What brings you in today?"},
                {"role": "assistant", "content": reply},
            ],
            session=session,
        )

    assert created["profile"]["name"] == "Mock Patient"
    assert "headache" in reply.lower()
    assert assessment.score > 0
    assert assessment.model_used == "mock:deterministic"
