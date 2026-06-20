"""
Repository for assessment report CRUD operations.
"""

from __future__ import annotations

import json
from typing import List, Optional

from sqlmodel import Session, select

from app.core.logging import get_logger
from app.models.assessment import AssessmentReport

logger = get_logger("repositories.assessment")


class AssessmentRepository:
    """Data-access layer for ``AssessmentReport``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        patient_id: int,
        score: int,
        feedback: str,
        details: dict | None = None,
        latency_ms: float | None = None,
        model_used: str | None = None,
        rubric_version: str = "v1",
    ) -> AssessmentReport:
        """Persist a new assessment report with research metrics."""
        report = AssessmentReport(
            patient_id=patient_id,
            score=score,
            feedback=feedback,
            details_json=json.dumps(details or {}, ensure_ascii=False),
            latency_ms=latency_ms,
            model_used=model_used,
            rubric_version=rubric_version,
        )
        self._session.add(report)
        self._session.commit()
        self._session.refresh(report)
        logger.info(
            "Assessment saved: id=%s, patient_id=%s, score=%s, latency_ms=%s",
            report.id,
            patient_id,
            score,
            latency_ms,
        )
        return report

    def get_by_patient(self, patient_id: int) -> List[AssessmentReport]:
        """Return all assessments for a given patient."""
        statement = (
            select(AssessmentReport)
            .where(AssessmentReport.patient_id == patient_id)
            .order_by(AssessmentReport.generated_at)
        )
        return list(self._session.exec(statement).all())

    def get_latest(self, patient_id: int) -> Optional[AssessmentReport]:
        """Return the most recent assessment for a patient, if any."""
        statement = (
            select(AssessmentReport)
            .where(AssessmentReport.patient_id == patient_id)
            .order_by(AssessmentReport.generated_at.desc())  # type: ignore[union-attr]
        )
        return self._session.exec(statement).first()
