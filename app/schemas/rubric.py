"""
Schemas for Rubric creation and visualization.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

class RubricCreateRequest(BaseModel):
    name: str
    version: str = "1.0"
    weight_history_taking: float = 0.4
    weight_communication: float = 0.2
    weight_reasoning: float = 0.2
    weight_empathy: float = 0.1
    weight_closure: float = 0.1
    safety_penalty_max: int = 20

class RubricResponse(RubricCreateRequest):
    id: int
    created_at: datetime
