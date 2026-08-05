"""Projection and role-gated access for patient case views."""

from __future__ import annotations

import json
from typing import Any

from sqlmodel import Session

from app.core.config import AppSettings
from app.core.exceptions import PatientNotFoundError
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.training_repository import ActionTraceRepository, TrainingSessionRepository
from app.schemas.case_views import FullPatientCase, InstructorCaseView, LearnerVisibleCase


def _opening_statement(profile: dict[str, Any]) -> str:
    opening = str(profile.get("opening_statement", "")).strip()
    if opening:
        return opening
    complaint = str(profile.get("chief_complaint", "")).strip()
    return complaint or "I would like to discuss why I came in today."


def _encounter_setting(profile: dict[str, Any]) -> str:
    raw = (
        profile.get("encounter_setting")
        or profile.get("setting")
        or profile.get("specialty")
        or "clinical_consultation"
    )
    return str(raw).replace("_", " ").strip().title()


def project_learner_case(patient_id: int, profile: dict[str, Any]) -> LearnerVisibleCase:
    """Create the only payload permitted in learner-facing state or responses."""
    return LearnerVisibleCase(
        patient_id=patient_id,
        case_id=str(profile["case_id"]) if profile.get("case_id") else None,
        age=str(profile.get("age", "")),
        gender=str(profile.get("gender", "")),
        encounter_setting=_encounter_setting(profile),
        chief_complaint=str(profile.get("chief_complaint", "")),
        opening_statement=_opening_statement(profile),
        unlocked_evidence=[],
    )


def load_learner_case(patient_id: int, session: Session) -> LearnerVisibleCase:
    """Rebuild a learner-safe view from server-side persistence."""
    patient = PatientRepository(session).get_by_id(patient_id)
    if patient is None:
        raise PatientNotFoundError(patient_id)
    profile = json.loads(patient.full_profile_json)
    return project_learner_case(patient_id, profile)


def export_learner_case(patient_id: int, session: Session) -> str:
    """Serialize only the learner projection for normal downloads/exports."""
    payload = load_learner_case(patient_id, session).model_dump(mode="json")
    return json.dumps(payload, ensure_ascii=False, indent=2)


def load_instructor_case(
    patient_id: int,
    session: Session,
    settings: AppSettings,
) -> InstructorCaseView:
    """Load full case and audit evidence after a server-side instructor check."""
    if not settings.is_instructor:
        raise PermissionError("Instructor case access requires APP_ROLE=instructor")

    patient = PatientRepository(session).get_by_id(patient_id)
    if patient is None:
        raise PatientNotFoundError(patient_id)
    profile = json.loads(patient.full_profile_json)

    action_trace: list[dict[str, Any]] = []
    unlock_history: list[dict[str, Any]] = []
    for entry in ConsultationRepository(session).get_by_patient(patient_id):
        state_snapshot: dict[str, Any] = {}
        if entry.state_snapshot_json:
            try:
                parsed = json.loads(entry.state_snapshot_json)
                if isinstance(parsed, dict):
                    state_snapshot = parsed
            except json.JSONDecodeError:
                state_snapshot = {"parse_error": True}

        action_trace.append(
            {
                "turn_number": entry.turn_number,
                "doctor_input": entry.doctor_input,
                "patient_response": entry.patient_response,
                "timestamp": entry.timestamp.isoformat(),
                "latency_ms": entry.latency_ms,
                "model_used": entry.model_used,
            }
        )
        unlock_history.append(
            {
                "turn_number": entry.turn_number,
                "topic_discussed": state_snapshot.get("topic_discussed"),
                "hidden_info_revealed": bool(state_snapshot.get("should_reveal_hidden", False)),
                "revealed_hidden_items": state_snapshot.get("revealed_hidden_items", []),
            }
        )

    scoring_evidence: list[dict[str, Any]] = []
    for report in AssessmentRepository(session).get_by_patient(patient_id):
        try:
            details = json.loads(report.details_json)
        except json.JSONDecodeError:
            details = {"parse_error": True}
        scoring_evidence.append(
            {
                "assessment_id": report.id,
                "score": report.score,
                "rubric_version": report.rubric_version,
                "generated_at": report.generated_at.isoformat(),
                "details": details,
            }
        )

    encounter = TrainingSessionRepository(session).get_latest_by_patient(patient_id)
    if encounter is not None:
        formal_trace = ActionTraceRepository(session).list_by_session(encounter.session_id)
        action_trace = [entry.model_dump(mode="json") for entry in formal_trace]
        unlock_history = [
            {
                "action_id": entry.action_id,
                "stage": entry.stage.value,
                "evidence_unlocked": [
                    evidence.model_dump(mode="json") for evidence in entry.evidence_unlocked
                ],
            }
            for entry in formal_trace
            if entry.evidence_unlocked
        ]

    return InstructorCaseView(
        full_case=FullPatientCase(
            patient_id=patient_id,
            profile=profile,
            opening_statement=_opening_statement(profile),
        ),
        rubric=dict(profile.get("scoring_rubric") or {}),
        learner_action_trace=action_trace,
        unlock_history=unlock_history,
        scoring_evidence=scoring_evidence,
    )
