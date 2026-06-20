"""
Repository for consultation log CRUD operations.
"""

from __future__ import annotations

from typing import List

from sqlmodel import Session, select

from app.core.logging import get_logger
from app.models.consultation import ConsultationLog

logger = get_logger("repositories.consultation")


class ConsultationRepository:
    """Data-access layer for ``ConsultationLog``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        patient_id: int,
        doctor_input: str,
        patient_response: str,
        latency_ms: float | None = None,
        model_used: str | None = None,
        turn_number: int = 1,
        state_snapshot_json: str | None = None,
    ) -> ConsultationLog:
        """Record a single doctor–patient exchange turn with provenance."""
        log = ConsultationLog(
            patient_id=patient_id,
            doctor_input=doctor_input,
            patient_response=patient_response,
            latency_ms=latency_ms,
            model_used=model_used,
            turn_number=turn_number,
            state_snapshot_json=state_snapshot_json,
        )
        self._session.add(log)
        self._session.commit()
        self._session.refresh(log)
        logger.debug("Consultation log saved: id=%s, patient_id=%s, latency_ms=%s", log.id, patient_id, latency_ms)
        return log

    def get_by_patient(self, patient_id: int) -> List[ConsultationLog]:
        """Return all consultation logs for a given patient (chronological)."""
        statement = (
            select(ConsultationLog)
            .where(ConsultationLog.patient_id == patient_id)
            .order_by(ConsultationLog.timestamp)
        )
        return list(self._session.exec(statement).all())
