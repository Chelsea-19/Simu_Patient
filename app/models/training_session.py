"""Persistent encounter state and append-only action trace records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class TrainingSessionRecord(SQLModel, table=True):
    __tablename__ = "training_session"

    session_id: str = Field(primary_key=True)
    patient_id: int = Field(foreign_key="patient_profile.id", index=True)
    learner_id: str = Field(index=True)
    case_id: str = Field(index=True)
    current_stage: str = Field(index=True)
    state_json: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActionTraceRecord(SQLModel, table=True):
    __tablename__ = "action_trace"

    action_id: str = Field(primary_key=True)
    session_id: str = Field(foreign_key="training_session.session_id", index=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    stage: str
    natural_language_input: Optional[str] = None
    structured_action_json: str = "{}"
    tool_name: Optional[str] = Field(default=None, index=True)
    tool_parameters_json: str = "{}"
    result_summary_json: str = "{}"
    evidence_unlocked_json: str = "[]"
    time_cost: int = 0
    hint_level: Optional[int] = None
    safety_event_json: str = "[]"
    score_event_json: str = "{}"
