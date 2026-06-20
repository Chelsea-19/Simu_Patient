from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_runtime_state(monkeypatch):
    """Keep cached settings and database engines isolated between tests."""
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from app.core.config import get_settings
    import app.db.session as db_session

    get_settings.cache_clear()
    db_session._engine = None
    yield
    get_settings.cache_clear()
    db_session._engine = None
