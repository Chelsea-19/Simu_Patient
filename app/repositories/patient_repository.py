"""
Repository for patient profile CRUD operations.
"""

from __future__ import annotations

import json
from typing import List, Optional

from sqlmodel import Session, select

from app.core.logging import get_logger
from app.models.patient import PatientProfile

logger = get_logger("repositories.patient")


class PatientRepository:
    """Data-access layer for ``PatientProfile``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, profile_data: dict) -> PatientProfile:
        """Persist a new patient from a raw LLM-generated dict."""
        patient = PatientProfile(
            name=str(profile_data.get("name", "Unknown")),
            age=str(profile_data.get("age", "")),
            gender=str(profile_data.get("gender", "")),
            chief_complaint=str(profile_data.get("chief_complaint", "")),
            full_profile_json=json.dumps(profile_data, ensure_ascii=False),
        )
        self._session.add(patient)
        self._session.commit()
        self._session.refresh(patient)
        logger.info("Patient created: id=%s, name=%s", patient.id, patient.name)
        return patient

    def get_by_id(self, patient_id: int) -> Optional[PatientProfile]:
        """Find a patient by primary key."""
        return self._session.get(PatientProfile, patient_id)

    def list_all(self, *, limit: int = 100, offset: int = 0) -> List[PatientProfile]:
        """Return all patients with pagination."""
        statement = select(PatientProfile).offset(offset).limit(limit)
        return list(self._session.exec(statement).all())

    def count(self) -> int:
        """Return the total number of patients."""
        statement = select(PatientProfile)
        return len(list(self._session.exec(statement).all()))
