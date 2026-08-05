"""Persistent session-level learning diagnosis record."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class LearningDiagnosisRecord(SQLModel, table=True):
    __tablename__ = "learning_diagnosis"

    session_id: str = Field(primary_key=True, foreign_key="training_session.session_id")
    learner_id: str = Field(index=True)
    case_id: str = Field(index=True)
    overall_score: int
    profile_json: str
    remediation_json: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
