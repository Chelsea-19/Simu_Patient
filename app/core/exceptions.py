"""
Application-specific exceptions for the shared service layer.
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger("exceptions")


class SimuPatientError(Exception):
    """Base exception for all SimuPatient errors."""

    def __init__(self, message: str = "An internal error occurred"):
        self.message = message
        super().__init__(self.message)


class PatientNotFoundError(SimuPatientError):
    """Raised when a patient ID does not exist."""

    def __init__(self, patient_id: int):
        super().__init__(
            message=f"Patient with id={patient_id} not found",
        )


class LLMGenerationError(SimuPatientError):
    """Raised when the LLM provider fails to return a usable response."""

    def __init__(self, detail: str = "LLM generation failed"):
        super().__init__(message=detail)


class LLMJsonParseError(SimuPatientError):
    """Raised when the LLM output cannot be parsed as valid JSON."""

    def __init__(self, raw_output: str = ""):
        detail = "Failed to parse LLM output as JSON"
        if raw_output:
            detail += f" - raw output (truncated): {raw_output[:200]}"
        super().__init__(message=detail)


class LLMAuthenticationError(SimuPatientError):
    """Raised when the Google API key is invalid or has no quota."""

    def __init__(
        self,
        detail: str = "Google AI API key authentication failed. Check that the key is valid and has quota.",
    ):
        super().__init__(message=detail)


class DatabaseError(SimuPatientError):
    """Raised on unrecoverable database operations."""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(message=detail)
