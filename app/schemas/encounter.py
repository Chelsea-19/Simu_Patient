"""Schemas for the deterministic clinical training state machine."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.case_views import UnlockedEvidence


class EncounterStage(StrEnum):
    CASE_INTRO = "CASE_INTRO"
    HISTORY_TAKING = "HISTORY_TAKING"
    EXAMINATION = "EXAMINATION"
    INVESTIGATION = "INVESTIGATION"
    CLINICAL_REASONING = "CLINICAL_REASONING"
    MANAGEMENT = "MANAGEMENT"
    SAFETY_REVIEW = "SAFETY_REVIEW"
    ASSESSMENT = "ASSESSMENT"
    REMEDIATION = "REMEDIATION"
    COMPLETED = "COMPLETED"


class EncounterState(BaseModel):
    session_id: str
    learner_id: str
    patient_id: int
    case_id: str
    training_goal: str
    difficulty: str
    current_stage: EncounterStage = EncounterStage.CASE_INTRO
    elapsed_time: int = Field(default=0, ge=0)
    actions_taken: list[str] = Field(default_factory=list)
    questions_asked: list[str] = Field(default_factory=list)
    evidence_unlocked: list[UnlockedEvidence] = Field(default_factory=list)
    tests_ordered: list[str] = Field(default_factory=list)
    physical_exams_completed: list[str] = Field(default_factory=list)
    differential_diagnoses: list[str] = Field(default_factory=list)
    management_plan: dict[str, Any] = Field(default_factory=dict)
    safety_flags: list[str] = Field(default_factory=list)
    hints_used: list[int] = Field(default_factory=list)
    assessment_status: str = "not_started"
    retry_of_session_id: str | None = None
    focused_retry: bool = False
    focus_skills: list[str] = Field(default_factory=list)
    history_turn_limit: int | None = Field(default=None, ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(extra="forbid")


class ActionTraceEntry(BaseModel):
    action_id: str
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    stage: EncounterStage
    natural_language_input: str | None = None
    structured_action: dict[str, Any] = Field(default_factory=dict)
    tool_name: str | None = None
    tool_parameters: dict[str, Any] = Field(default_factory=dict)
    result_summary: dict[str, Any] = Field(default_factory=dict)
    evidence_unlocked: list[UnlockedEvidence] = Field(default_factory=list)
    time_cost: int = Field(default=0, ge=0)
    hint_level: int | None = None
    safety_event: list[str] = Field(default_factory=list)
    score_event: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class ToolResult(BaseModel):
    tool_name: str
    status: Literal["success", "error", "duplicate"]
    evidence_unlocked: list[UnlockedEvidence] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    time_cost: int = Field(default=0, ge=0)
    safety_events: list[str] = Field(default_factory=list)
    learner_message: str = ""
    current_stage: EncounterStage

    model_config = ConfigDict(extra="forbid")
