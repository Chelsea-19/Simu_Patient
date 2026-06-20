from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class CaseTemplateValidationError(ValueError):
    """Raised when a YAML case template cannot be loaded or validated."""


class CaseDemographics(BaseModel):
    age: int
    gender: str
    occupation: str

    model_config = ConfigDict(extra="forbid")


class HiddenInformationItem(BaseModel):
    item: str
    reveal_condition: str
    clinical_relevance: str

    model_config = ConfigDict(extra="forbid")


class PatientPersonality(BaseModel):
    anxiety: str
    cooperativeness: str
    health_literacy: str

    model_config = ConfigDict(extra="forbid")


class ScoringRubric(BaseModel):
    history_taking: int = Field(ge=0, le=100)
    communication: int = Field(ge=0, le=100)
    clinical_reasoning: int = Field(ge=0, le=100)
    empathy: int = Field(ge=0, le=100)
    closure: int = Field(ge=0, le=100)

    model_config = ConfigDict(extra="forbid")


class ClinicalCaseTemplate(BaseModel):
    case_id: str
    title: str
    specialty: str
    difficulty: str
    chief_complaint: str
    demographics: CaseDemographics
    present_illness: Dict[str, Any]
    past_medical_history: List[str]
    medication_history: List[str]
    allergy_history: List[str]
    family_history: List[str]
    social_history: Dict[str, Any]
    hidden_information: List[HiddenInformationItem]
    red_flags: List[str]
    expected_key_questions: List[str]
    scoring_rubric: ScoringRubric
    patient_personality: PatientPersonality
    opening_statement: str

    model_config = ConfigDict(extra="forbid")
