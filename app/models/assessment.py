"""
ORM model for the assessment report table.

Stores OSCE-style evaluation results produced by the LLM.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class AssessmentReport(SQLModel, table=True):
    """
    Structured evaluation of a consultation session.

    The ``details_json`` field stores the full LLM output (strengths,
    missed_questions, safety_flags, etc.) as a JSON string so that
    the schema can evolve without DB migrations.
    """

    __tablename__ = "assessment_report"

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient_profile.id", index=True)
    score: int = Field(default=0)
    feedback: str = Field(default="")
    details_json: str = Field(default="{}")  # extensible blob for rubric details
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # --- Provenance & Research Metrics ---
    latency_ms: Optional[float] = Field(default=None, description="Time taken for evaluation")
    model_used: Optional[str] = Field(default=None, description="Model version used for scoring")
    rubric_version: Optional[str] = Field(default="v1", description="Identifier of the evaluation prompt/rubric")

    model_config = {"protected_namespaces": ()}
