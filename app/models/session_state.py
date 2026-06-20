"""
ORM model for Conversation State and Memory.
Supports Phase 2: 病人角色与信息披露引擎 (Patient Role Engine & Disclosure Controller).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional, List

from sqlmodel import Field, SQLModel


class SessionState(SQLModel, table=True):
    """
    Tracks the dynamic state of a patient throughout a consultation.
    Keeps track of their emotions, trust level, and what they've revealed.
    """

    __tablename__ = "session_state"

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient_profile.id", unique=True)
    
    # Emotional and Persona state (1-10 scale)
    trust_level: int = Field(default=4, description="1 to 10 scale describing trust in the doctor.")
    anxiety_level: int = Field(default=6, description="1 to 10 scale describing current distress.")
    cooperativeness: int = Field(default=5, description="1 to 10 scale describing willingness to answer.")
    
    # Information Disclosure State
    revealed_topics_json: str = Field(default="[]", description="JSON string list of discussed topics.")
    hidden_info_revealed: bool = Field(default=False, description="Whether the red flag/hidden info has been explicitly confessed.")
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def revealed_topics(self) -> List[str]:
        return json.loads(self.revealed_topics_json)

    @revealed_topics.setter
    def revealed_topics(self, val: List[str]) -> None:
        self.revealed_topics_json = json.dumps(val)
