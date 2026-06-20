"""
Centralized configuration for the Streamlit application.

Settings are read from Streamlit secrets first, then environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Application-wide settings loaded from env, .env, or Streamlit secrets."""

    APP_NAME: str = "SimuPatient"
    APP_ENV: str = "production"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///simupatient.db"

    LLM_PROVIDER: str = "mock"

    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    GEMINI_TEMPERATURE: float = 0.7

    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen3:32b"
    OLLAMA_TEMPERATURE: float = 0.8

    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "validate_assignment": True,
    }

    @property
    def selected_provider(self) -> str:
        """Normalized provider name used by the provider factory."""
        return self.LLM_PROVIDER.strip().lower()

    @property
    def resolved_gemini_api_key(self) -> Optional[str]:
        """Gemini key from the current name or the older Google key name."""
        return self.GEMINI_API_KEY or self.GOOGLE_API_KEY


@lru_cache()
def get_settings() -> AppSettings:
    """
    Return cached application settings.

    Streamlit secrets override environment and .env values when available.
    """
    overrides = {}

    try:
        import streamlit as st

        if hasattr(st, "secrets"):
            for key, value in st.secrets.items():
                upper_key = key.upper()
                if upper_key in AppSettings.model_fields:
                    overrides[upper_key] = value
    except Exception:
        pass

    return AppSettings(**overrides)
