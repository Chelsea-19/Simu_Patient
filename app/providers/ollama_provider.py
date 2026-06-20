"""
Ollama LLM provider retained for local experimentation.

The active Streamlit factory resolves Gemini; this module remains importable
without requiring the Ollama SDK until the provider is instantiated.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.exceptions import LLMGenerationError
from app.core.logging import get_logger
from app.providers.base import BaseLLMProvider

logger = get_logger("providers.ollama")


class OllamaProvider(BaseLLMProvider):
    """Provider that delegates to a local or remote Ollama server."""

    def __init__(self, base_url: str | None = None) -> None:
        try:
            import ollama
        except ImportError as exc:
            raise ImportError(
                "The 'ollama' package is required for OllamaProvider. Install it with: pip install ollama"
            ) from exc

        settings = get_settings()
        final_base_url = base_url or getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self._model = getattr(settings, "OLLAMA_MODEL", "qwen3:32b")
        self._temperature = getattr(settings, "OLLAMA_TEMPERATURE", 0.8)
        self._client = ollama.Client(host=final_base_url)
        logger.info(
            "OllamaProvider initialized: model=%s, base_url=%s, dynamic_url=%s",
            self._model,
            final_base_url,
            base_url is not None,
        )

    def generate_text(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
    ) -> str:
        temp = temperature if temperature is not None else self._temperature
        try:
            response = self._client.chat(
                model=self._model,
                messages=messages,
                options={"temperature": temp},
            )
            return response["message"]["content"]
        except Exception as exc:
            logger.error("Ollama generate_text failed: %s", exc)
            raise LLMGenerationError(detail=f"Ollama call failed: {exc}") from exc

    def generate_json(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        temp = temperature if temperature is not None else self._temperature
        try:
            response = self._client.chat(
                model=self._model,
                messages=messages,
                format="json",
                options={"temperature": temp},
            )
            raw = response["message"]["content"]
            return self.parse_json_response(raw)
        except LLMGenerationError:
            raise
        except Exception as exc:
            logger.error("Ollama generate_json failed: %s", exc)
            raise LLMGenerationError(detail=f"Ollama call failed: {exc}") from exc

    def health_check(self) -> bool:
        try:
            self._client.list()
            return True
        except Exception:
            return False
