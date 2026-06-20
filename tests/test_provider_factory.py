from __future__ import annotations

import pytest


def test_provider_factory_selects_mock(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    from app.core.config import get_settings
    from app.providers.factory import get_llm_provider
    from app.providers.mock_provider import MockProvider

    get_settings.cache_clear()

    provider = get_llm_provider()

    assert isinstance(provider, MockProvider)
    assert provider.health_check() is True


def test_provider_factory_selects_gemini_with_fake_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")

    from app.core.config import get_settings
    from app.providers.factory import get_llm_provider
    from app.providers.gemini_provider import GeminiProvider

    get_settings.cache_clear()

    provider = get_llm_provider()

    assert isinstance(provider, GeminiProvider)


def test_provider_factory_gemini_missing_key_is_clear(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")

    from app.core.config import get_settings
    from app.providers.factory import get_llm_provider

    get_settings.cache_clear()

    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        get_llm_provider()
