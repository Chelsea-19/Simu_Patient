"""
Request / response schemas for Case Templates.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CaseTemplateCreateRequest(BaseModel):
    """Body for POST /teacher/cases/"""

    title: str = Field(..., title="Case Title")
    specialty: str = Field(..., title="Medical Specialty")
    
    language: str = Field("zh-CN")
    setting: str = Field("门诊")
    difficulty: str = Field("intermediate")
    
    learning_objectives: str = Field("")
    chief_complaint: str
    present_illness: str
    past_medical_history: str = Field("")
    medication_history: str = Field("")
    allergy_history: str = Field("")
    family_history: str = Field("")
    social_history: str = Field("")
    review_of_systems: str = Field("")
    
    red_flags: str = Field("")
    hidden_info: str = Field("")
    persona_traits: str = Field("")
    disclosure_rules: str = Field("")
    
    expected_key_questions: str = Field("")
    expected_missed_risks: str = Field("")
    teacher_notes: str = Field("")


class CaseTemplateResponse(CaseTemplateCreateRequest):
    """Returned when fetching cases."""
    
    id: int
    created_at: datetime
    updated_at: datetime


class CaseTemplateListResponse(BaseModel):
    """Response for GET /teacher/cases"""

    cases: list[CaseTemplateResponse]
    total: int
