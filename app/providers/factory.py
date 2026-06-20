"""
Provider factory for the active Streamlit runtime.
"""

from __future__ import annotations

from app.core.config import AppSettings, get_settings
from app.core.logging import get_logger
from app.providers.base import BaseLLMProvider

logger = get_logger("providers.factory")


def get_llm_provider(
    settings: AppSettings | None = None,
    api_key: str | None = None,
) -> BaseLLMProvider:
    """
    Return the configured LLM provider for the Streamlit app.

    If api_key is provided, it overrides the settings value.
    """
    if settings is None:
        settings = get_settings()

    provider_name = settings.selected_provider

    if provider_name == "mock":
        from app.providers.mock_provider import MockProvider

        provider = MockProvider()
    elif provider_name == "gemini":
        from app.providers.gemini_provider import GeminiProvider

        provider = GeminiProvider(api_key=api_key)
    elif provider_name == "ollama":
        from app.providers.ollama_provider import OllamaProvider

        provider = OllamaProvider()
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER={settings.LLM_PROVIDER!r}. "
            "Supported values are: mock, gemini, ollama."
        )

    logger.info(
        "LLM provider resolved: %s (dynamic credentials: %s)",
        provider.__class__.__name__,
        api_key is not None,
    )
    return provider
