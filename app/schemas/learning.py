"""Schemas for session-level learning diagnosis, remediation, and retry comparison."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


LearningDimensionName = Literal[
    "history_taking",
    "communication",
    "clinical_reasoning",
    "red_flag_recognition",
    "investigation_selection",
    "management_safety",
    "empathy",
    "closure_and_safety_netting",
    "efficiency",
]


class DimensionDiagnosis(BaseModel):
    score: int = Field(ge=0, le=100)
    deterministic_score: int = Field(ge=0, le=100)
    qualitative_adjustment: int = Field(default=0, ge=-5, le=5)
    scoring_evidence: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    omissions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommended_practice: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class LearningProfile(BaseModel):
    session_id: str
    learner_id: str
    case_id: str
    overall_score: int = Field(ge=0, le=100)
    dimensions: dict[LearningDimensionName, DimensionDiagnosis]
    lowest_dimensions: list[LearningDimensionName] = Field(default_factory=list, max_length=3)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scoring_version: str = "learning-profile-v1"
    formative_use_only: bool = True

    model_config = ConfigDict(extra="forbid")


class PersonalizedRemediationPlan(BaseModel):
    priority_skills: list[LearningDimensionName] = Field(default_factory=list, max_length=3)
    learning_objective: str
    recommended_case: str
    recommended_difficulty: str
    specific_actions_to_practice: list[str] = Field(default_factory=list)
    hint_policy: str
    success_criteria: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class SafetyOmissionChange(BaseModel):
    first_round: list[str] = Field(default_factory=list)
    second_round: list[str] = Field(default_factory=list)
    resolved: list[str] = Field(default_factory=list)
    new: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class LearningProgressReport(BaseModel):
    first_session_id: str
    second_session_id: str
    first_total_score: int = Field(ge=0, le=100)
    second_total_score: int = Field(ge=0, le=100)
    dimension_changes: dict[LearningDimensionName, int]
    safety_critical_omissions_change: SafetyOmissionChange
    first_hints_used: int = Field(ge=0)
    second_hints_used: int = Field(ge=0)
    hints_used_change: int
    first_completion_time: int = Field(ge=0)
    second_completion_time: int = Field(ge=0)
    completion_time_change: int
    still_needs_improvement: list[LearningDimensionName] = Field(default_factory=list)
    interpretation: str

    model_config = ConfigDict(extra="forbid")


class LearningDiagnosisBundle(BaseModel):
    profile: LearningProfile
    remediation_plan: PersonalizedRemediationPlan

    model_config = ConfigDict(extra="forbid")
