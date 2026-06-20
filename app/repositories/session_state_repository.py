"""
Repository for SessionState DB access.
"""

from __future__ import annotations

from sqlmodel import Session, select
from typing import Optional

from app.models.session_state import SessionState

class SessionStateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_by_patient_id(self, patient_id: int) -> SessionState:
        """
        Retrieves the session state for a patient.
        If it does not exist, initialize a new state.
        """
        statement = select(SessionState).where(SessionState.patient_id == patient_id)
        state = self.session.exec(statement).first()
        
        if not state:
            state = SessionState(patient_id=patient_id)
            self.session.add(state)
            self.session.commit()
            self.session.refresh(state)

        return state

    def update(self, state: SessionState) -> SessionState:
        self.session.add(state)
        self.session.commit()
        self.session.refresh(state)
        return state
