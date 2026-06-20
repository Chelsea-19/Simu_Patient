"""
Request / response schemas for consultation (chat) endpoints.
"""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    """Body for POST /consultation/chat."""

    patient_id: int
    user_input: str = Field(..., min_length=1)
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response for POST /consultation/chat."""

    response: str
