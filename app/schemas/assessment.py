"""
Request / response schemas for assessment (evaluation) endpoints.
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.schemas.chat import ChatMessage


class AssessmentRequest(BaseModel):
    """Body for POST /assessment/evaluate."""

    patient_id: int
    history: List[ChatMessage] = Field(default_factory=list)


class AssessmentResult(BaseModel):
    """
    Structured evaluation result.
    
    Now supports highly detailed Hybrid outputs: rules-based checklists + qualitative scores.
    """

    score: int = Field(default=0, ge=0, le=100)
    history_taking_score: int = Field(default=0, ge=0, le=100)
    communication_score: int = Field(default=0, ge=0, le=100)
    empathy_score: int = Field(default=0, ge=0, le=100)
    clinical_reasoning_score: int = Field(default=0, ge=0, le=100)
    safety_score: int = Field(default=0, ge=0, le=100)
    closure_score: int = Field(default=0, ge=0, le=100)
    
    feedback: str = Field(default="")
    strengths: List[str] = Field(default_factory=list)
    missed_questions: List[str] = Field(default_factory=list)
    critical_omissions: List[str] = Field(default_factory=list, description="Crucial questions missed.")
    safety_flags: List[str] = Field(default_factory=list)
    good_followups: List[str] = Field(default_factory=list)
    unnecessary_questions: List[str] = Field(default_factory=list)
    suggested_next_questions: List[str] = Field(default_factory=list)
    
    state_revealed: bool = Field(default=False, description="Did the student uncover the hidden info?")
    
    # Provenance
    latency_ms: Optional[float] = None
    model_used: Optional[str] = None
    rubric_version: Optional[str] = None
    learning_profile: dict[str, Any] | None = None
    remediation_plan: dict[str, Any] | None = None

    model_config = {"protected_namespaces": ()}


class AssessmentResponse(BaseModel):
    """Response for POST /assessment/evaluate."""

    patient_id: int
    result: AssessmentResult
