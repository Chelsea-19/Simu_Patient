"""
Request / response schemas (DTOs) for patient-related endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.case_views import LearnerVisibleCase


# ── Requests ─────────────────────────────────────────────────────────────

class PatientCreateRequest(BaseModel):
    """Body for POST /patients/create."""

    seed_text: Optional[str] = Field(
        None,
        min_length=5,
        description="Free-text case description used to seed patient generation (for free gen mode)",
        examples=["A 50-year-old male with chest pain triggered by exercise."],
    )
    template_id: Optional[int] = Field(
        None,
        description="ID of the CaseTemplate to use as a structured blueprint for generation",
    )


# ── Responses ────────────────────────────────────────────────────────────

class PatientProfileResponse(BaseModel):
    """Learner-safe patient response."""

    id: int
    case: LearnerVisibleCase
    created_at: datetime


class PatientCreateResponse(BaseModel):
    """Learner-safe response for patient creation."""

    id: int
    case: LearnerVisibleCase


class PatientListResponse(BaseModel):
    """Response for GET /patients."""

    patients: list[PatientProfileResponse]
    total: int
