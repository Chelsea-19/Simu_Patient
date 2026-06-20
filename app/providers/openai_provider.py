"""
OpenAI / OpenAI-compatible LLM provider.

Works with:
  - Official OpenAI API
  - Azure OpenAI (via ``openai`` SDK's ``AzureOpenAI`` client)
  - Any OpenAI-compatible endpoint (e.g. vLLM, LiteLLM, Together, etc.)
    by setting OPENAI_BASE_URL.

Required environment variables:
  OPENAI_API_KEY    – your API key
  OPENAI_MODEL      – e.g. gpt-4o
  OPENAI_BASE_URL   – (optional) override for compatible endpoints
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.exceptions import LLMGenerationError
from app.core.logging import get_logger
from app.providers.base import BaseLLMProvider

logger = get_logger("providers.openai")


class OpenAIProvider(BaseLLMProvider):
    """
    Provider for OpenAI and OpenAI-compatible APIs.

    Lazily imports ``openai`` so the dependency is optional at install time.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        settings = get_settings()

        try:
            from openai import OpenAI  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "The 'openai' package is required for OpenAIProvider. "
                "Install it with: pip install openai"
            ) from exc

        # Use passed credentials or fall back to settings (BYOK support)
        final_api_key = api_key or settings.OPENAI_API_KEY
        final_base_url = base_url or settings.OPENAI_BASE_URL

        if not final_api_key and settings.LLM_PROVIDER == "openai":
            logger.warning("OpenAI API key is missing. Ensure it is provided in headers or .env")

        client_kwargs: Dict[str, Any] = {"api_key": final_api_key}
        if final_base_url:
            client_kwargs["base_url"] = final_base_url

        self._client = OpenAI(**client_kwargs)
        self._model = settings.OPENAI_MODEL
        self._temperature = settings.OPENAI_TEMPERATURE
        logger.info(
            "OpenAIProvider initialised – model=%s, dynamic_key=%s", 
            self._model, 
            api_key is not None
        )

    # ── Interface implementation ─────────────────────────────────────────

    def generate_text(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
    ) -> str:
        temp = temperature if temperature is not None else self._temperature
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temp,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            # Handle API Key authentication / quota issues specifically
            from openai import AuthenticationError # type: ignore[import-untyped]
            if isinstance(exc, AuthenticationError):
                logger.warning("OpenAI Authentication failed: %s", exc)
                from app.core.exceptions import LLMAuthenticationError
                raise LLMAuthenticationError(detail=f"API Key 认证失败或额度已耗尽: {exc}") from exc
            
            logger.error("OpenAI generate_text failed: %s", exc)
            raise LLMGenerationError(detail=f"OpenAI call failed: {exc}") from exc

    def generate_json(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        temp = temperature if temperature is not None else self._temperature
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temp,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            return self.parse_json_response(raw)
        except Exception as exc:
            # Handle API Key authentication / quota issues specifically
            from openai import AuthenticationError # type: ignore[import-untyped]
            if isinstance(exc, AuthenticationError):
                logger.warning("OpenAI Authentication failed: %s", exc)
                from app.core.exceptions import LLMAuthenticationError
                raise LLMAuthenticationError(detail=f"API Key 认证失败或额度已耗尽: {exc}") from exc
            
            if isinstance(exc, LLMGenerationError):
                raise
            
            logger.error("OpenAI generate_json failed: %s", exc)
            raise LLMGenerationError(detail=f"OpenAI call failed: {exc}") from exc

    def health_check(self) -> bool:
        try:
            self._client.models.list()
            return True
        except Exception:
            return False
