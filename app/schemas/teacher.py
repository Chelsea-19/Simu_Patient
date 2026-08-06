"""Role-gated teacher dashboard and YAML validation contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.learning import LearningProgressReport


class TeacherTrainingRecord(BaseModel):
    session_id: str
    learner_id: str
    patient_id: int
    case_id: str
    training_goal: str
    difficulty: str
    current_stage: str
    retry_of_session_id: str | None = None
    overall_score: int | None = Field(default=None, ge=0, le=100)
    dimension_scores: dict[str, int] = Field(default_factory=dict)
    action_trace: list[dict[str, Any]] = Field(default_factory=list)
    safety_events: list[str] = Field(default_factory=list)
    hints_used: list[int] = Field(default_factory=list)
    elapsed_time: int = Field(ge=0)
    progress_report: LearningProgressReport | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class TeacherDashboard(BaseModel):
    learner_filter: str | None = None
    available_learners: list[str] = Field(default_factory=list)
    records: list[TeacherTrainingRecord] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    formative_use_only: bool = True

    model_config = ConfigDict(extra="forbid")


class ValidationIssue(BaseModel):
    severity: Literal["error", "warning", "info"]
    code: str
    path: str
    message: str

    model_config = ConfigDict(extra="forbid")


class CaseTemplateValidationResult(BaseModel):
    case_id: str | None = None
    filename: str
    valid: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    schema_issues: list[ValidationIssue] = Field(default_factory=list)
    hidden_rule_issues: list[ValidationIssue] = Field(default_factory=list)
    safety_rule_issues: list[ValidationIssue] = Field(default_factory=list)
    learner_preview: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(extra="forbid")
