"""
ORM model for the consultation log table.

Each row represents one doctor–patient exchange turn.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ConsultationLog(SQLModel, table=True):
    """Audit log for every doctor ↔ patient exchange with provenance metrics."""

    __tablename__ = "consultation_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient_profile.id", index=True)
    doctor_input: str
    patient_response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # --- Provenance & Research Metrics ---
    latency_ms: Optional[float] = Field(default=None, description="Time taken for LLM generation")
    model_used: Optional[str] = Field(default=None, description="Exact model version used for response")
    turn_number: int = Field(default=1, description="Sequential turn index in the conversation")
    
    # --- Internal patient state at this specific turn ---
    state_snapshot_json: Optional[str] = Field(default=None, description="JSON representing internal trust/anxiety and topics at this turn")

    model_config = {"protected_namespaces": ()}
