"""
ORM model for Case Templates (题库蓝图).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class CaseTemplate(SQLModel, table=True):
    """
    Blueprint for generating Standardized Patients.
    Supports teacher authoring and dynamic patient generation.
    """

    __tablename__ = "case_template"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    specialty: str = Field(index=True)
    
    # Localization & Context
    language: str = Field(default="zh-CN")
    setting: str = Field(default="门诊") # Outpatient, Inpatient, Emergency, etc.
    difficulty: str = Field(default="intermediate")
    
    # Clinical Content
    learning_objectives: str = Field(default="")
    chief_complaint: str
    present_illness: str
    past_medical_history: str = Field(default="")
    medication_history: str = Field(default="")
    allergy_history: str = Field(default="")
    family_history: str = Field(default="")
    social_history: str = Field(default="")
    review_of_systems: str = Field(default="")
    
    # Additional Simulation Data
    red_flags: str = Field(default="")
    hidden_info: str = Field(default="")
    persona_traits: str = Field(default="")
    disclosure_rules: str = Field(default="")
    
    # Assessment Hints
    expected_key_questions: str = Field(default="")
    expected_missed_risks: str = Field(default="")
    teacher_notes: str = Field(default="")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
