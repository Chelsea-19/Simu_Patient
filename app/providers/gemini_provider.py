"""
Google Gemini provider for the active Streamlit runtime.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.exceptions import LLMGenerationError
from app.core.logging import get_logger
from app.providers.base import BaseLLMProvider

logger = get_logger("providers.gemini")


class GeminiProvider(BaseLLMProvider):
    """Provider that delegates to the Google Gemini API."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        final_api_key = api_key or settings.resolved_gemini_api_key

        if not final_api_key:
            raise ValueError(
                "Gemini provider selected but no API key is configured. "
                "Set GEMINI_API_KEY in the environment or Streamlit secrets."
            )

        self._api_key = final_api_key
        self._genai = None
        self._generation_config_cls = None

        raw_model_name = settings.GEMINI_MODEL
        if raw_model_name.startswith("models/"):
            self._model_name = raw_model_name
        else:
            self._model_name = f"models/{raw_model_name}"

        self._temperature = settings.GEMINI_TEMPERATURE

        logger.info("GeminiProvider initialized: model=%s", self._model_name)

    def _ensure_sdk(self) -> None:
        """Import and configure the Gemini SDK only when an API call is made."""
        if self._genai is not None and self._generation_config_cls is not None:
            return

        try:
            import google.generativeai as genai
            from google.generativeai.types import GenerationConfig
        except ImportError as exc:
            raise ImportError(
                "The 'google-generativeai' package is required to call Gemini. "
                "Install project dependencies with: pip install -r requirements.txt"
            ) from exc

        genai.configure(api_key=self._api_key)
        self._genai = genai
        self._generation_config_cls = GenerationConfig

    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple[List[Dict[str, Any]], str]:
        """
        Convert OpenAI-style messages to Gemini format.

        Gemini expects roles of user and model. System messages are combined
        into a single system instruction string.
        """
        gemini_messages = []
        system_instructions = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_instructions.append(content)
            elif role == "user":
                gemini_messages.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                gemini_messages.append({"role": "model", "parts": [content]})

        return gemini_messages, "\n".join(system_instructions)

    def generate_text(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
    ) -> str:
        temp = temperature if temperature is not None else self._temperature
        gemini_msgs, system_instr = self._convert_messages(messages)

        try:
            self._ensure_sdk()
            model = self._genai.GenerativeModel(
                model_name=self._model_name,
                system_instruction=system_instr if system_instr else None,
            )

            response = model.generate_content(
                gemini_msgs,
                generation_config=self._generation_config_cls(temperature=temp),
            )
            return response.text
        except Exception as exc:
            logger.error("Gemini generate_text failed: %s", exc)
            raise LLMGenerationError(detail=f"Gemini call failed: {exc}") from exc

    def generate_json(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        temp = temperature if temperature is not None else self._temperature
        gemini_msgs, system_instr = self._convert_messages(messages)

        try:
            self._ensure_sdk()
            model = self._genai.GenerativeModel(
                model_name=self._model_name,
                system_instruction=system_instr if system_instr else None,
            )

            response = model.generate_content(
                gemini_msgs,
                generation_config=self._generation_config_cls(
                    temperature=temp,
                    response_mime_type="application/json",
                ),
            )
            raw = response.text
            return self.parse_json_response(raw)
        except Exception as exc:
            logger.error("Gemini generate_json failed: %s", exc)
            raise LLMGenerationError(detail=f"Gemini call failed: {exc}") from exc

    def health_check(self) -> bool:
        try:
            self._ensure_sdk()
            self._genai.get_model(self._model_name)
            return True
        except Exception:
            return False
