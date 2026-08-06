"""
Abstract base class for LLM providers.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger("providers.base")


class BaseLLMProvider(ABC):
    """Unified interface for model providers used by the service layer."""

    @abstractmethod
    def generate_text(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
    ) -> str:
        """Send a chat request and return the raw text response."""
        ...

    @abstractmethod
    def generate_json(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Send a chat request and parse a JSON object from the response."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the provider is reachable and operational."""
        ...

    @staticmethod
    def parse_json_response(raw: str) -> Dict[str, Any]:
        """
        Best-effort JSON extraction from LLM output.

        Handles markdown code fences, surrounding prose, and whitespace.
        """
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        fence_pattern = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)
        match = fence_pattern.search(raw)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        brace_start = raw.find("{")
        brace_end = raw.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            try:
                return json.loads(raw[brace_start : brace_end + 1])
            except json.JSONDecodeError:
                pass

        logger.error("Failed to parse JSON from LLM output; raw content suppressed")
        from app.core.exceptions import LLMJsonParseError

        raise LLMJsonParseError(raw_output=raw)
