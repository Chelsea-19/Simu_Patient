"""Structured output contract for deterministic encounter safety review."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SafetyReview(BaseModel):
    risk_level: Literal["low", "moderate", "high", "critical"]
    decision: Literal["allow_completion", "block_completion"]
    triggered_rules: list[str] = Field(default_factory=list)
    missing_critical_actions: list[str] = Field(default_factory=list)
    learner_feedback: str = ""
    recommended_reflection_questions: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
