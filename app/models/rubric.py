"""
ORM model for Rubric versioning.
Supports different schools, courses, and exam formats.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Rubric(SQLModel, table=True):
    """
    Standardized Evaluation Rubric.
    """

    __tablename__ = "rubric"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="Human readable name of the rubric.")
    version: str = Field(default="1.0", description="Rubric format version.")
    
    # Weights for fusion
    weight_history_taking: float = Field(default=0.4)
    weight_communication: float = Field(default=0.2)
    weight_reasoning: float = Field(default=0.2)
    weight_empathy: float = Field(default=0.1)
    weight_closure: float = Field(default=0.1)
    
    # Penalties
    safety_penalty_max: int = Field(default=20, description="Max points deducted for safety flags")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
