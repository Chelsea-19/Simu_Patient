"""
Request / response schemas (DTOs) for patient-related endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


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
    """Returned when a patient is created or queried."""

    id: int
    name: str
    age: str
    gender: str
    chief_complaint: str
    profile: Dict[str, Any]  # the full JSON profile
    created_at: datetime


class PatientCreateResponse(BaseModel):
    """Response for POST /patients/create."""

    id: int
    profile: Dict[str, Any]


class PatientListResponse(BaseModel):
    """Response for GET /patients."""

    patients: list[PatientProfileResponse]
    total: int
