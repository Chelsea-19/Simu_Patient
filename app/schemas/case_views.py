"""Role-separated case view models.

The learner model is intentionally explicit and ``extra='forbid'`` so adding a
field to the internal case cannot silently expose it to the browser.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


LEARNER_FORBIDDEN_FIELDS = frozenset(
    {
        "hidden_info",
        "hidden_information",
        "red_flags",
        "expected_key_questions",
        "scoring_rubric",
        "ground_truth_diagnosis",
        "unreleased_test_results",
    }
)


class UnlockedEvidence(BaseModel):
    """One fact that a learner legitimately unlocked during an encounter."""

    evidence_id: str
    category: str
    label: str
    value: Any
    unlocked_at: datetime | None = None
    source_action: str | None = None

    model_config = ConfigDict(extra="forbid")


class LearnerVisibleCase(BaseModel):
    """The complete case payload allowed in learner-facing responses/state."""

    patient_id: int
    case_id: str | None = None
    age: str
    gender: str
    encounter_setting: str
    chief_complaint: str
    opening_statement: str
    unlocked_evidence: list[UnlockedEvidence] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class FullPatientCase(BaseModel):
    """Server-side source of truth, including instructor-only case facts."""

    patient_id: int
    profile: dict[str, Any]
    opening_statement: str

    model_config = ConfigDict(extra="forbid")


class InstructorCaseView(BaseModel):
    """Instructor-only review payload assembled from server-side persistence."""

    full_case: FullPatientCase
    rubric: dict[str, Any] = Field(default_factory=dict)
    learner_action_trace: list[dict[str, Any]] = Field(default_factory=list)
    unlock_history: list[dict[str, Any]] = Field(default_factory=list)
    scoring_evidence: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
