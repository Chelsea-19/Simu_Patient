from __future__ import annotations

import json
from typing import Any, Dict, List

from sqlmodel import Session

from app.core.config import get_settings
from app.db.session import _get_engine, init_db
from app.providers.factory import get_llm_provider
from app.repositories.consultation_repository import ConsultationRepository
from app.schemas.assessment import AssessmentResult
from app.schemas.case_views import InstructorCaseView, LearnerVisibleCase
from app.schemas.case_template_file import ClinicalCaseTemplate
from app.schemas.teacher import CaseTemplateValidationResult
from app.services.case_loader import get_available_cases, load_case_by_id
from app.services.case_view_service import (
    export_learner_case,
    load_instructor_case,
    load_learner_case,
    project_learner_case,
)
from app.services.clinical_skill_router import ClinicalSkillRouter
from app.services.learning_diagnosis_service import LearningDiagnosisService
from app.services.case_template_validation_service import CaseTemplateValidationService
from app.services.simu_engine import SimuEngine
from app.services.teacher_dashboard_service import TeacherDashboardService


def get_engine_instance(api_key: str | None = None) -> SimuEngine:
    """Create a SimuEngine instance for the current Streamlit operation."""
    settings = get_settings()
    provider = get_llm_provider(settings, api_key=api_key)
    return SimuEngine(provider=provider)


def ensure_db_ready() -> None:
    """Initialize the database if needed."""
    init_db()


def create_patient_logic(
    seed_text: str | None,
    template_id: int | None,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """Generate a patient and return only its learner-safe projection."""
    engine = get_engine_instance(api_key)
    db_engine = _get_engine()
    with Session(db_engine) as session:
        created = engine.generate_patient(seed_text=seed_text, template_id=template_id, session=session)
        learner_case = project_learner_case(created["id"], created["profile"])
        return {
            "id": created["id"],
            "case": learner_case.model_dump(mode="json"),
            "opening_statement": learner_case.opening_statement,
        }


def list_case_templates_logic() -> List[ClinicalCaseTemplate]:
    """Return validated YAML case templates for the Streamlit selector."""
    return list(get_available_cases())


def create_patient_from_case_logic(
    case_id: str,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """Initialize a YAML case and return only its learner-safe projection."""
    case = load_case_by_id(case_id)
    engine = get_engine_instance(api_key)
    db_engine = _get_engine()
    with Session(db_engine) as session:
        created = engine.generate_patient_from_case_template(case=case, session=session)
        learner_case = project_learner_case(created["id"], created["profile"])
        return {
            "id": created["id"],
            "case": learner_case.model_dump(mode="json"),
            "opening_statement": learner_case.opening_statement,
        }


def get_learner_case_logic(patient_id: int) -> LearnerVisibleCase:
    """Read a persisted case through the learner-safe projection."""
    with Session(_get_engine()) as session:
        return load_learner_case(patient_id, session)


def export_learner_case_logic(patient_id: int) -> str:
    """Return a safe JSON export containing no instructor-only state."""
    with Session(_get_engine()) as session:
        return export_learner_case(patient_id, session)


def get_instructor_case_view_logic(patient_id: int) -> InstructorCaseView:
    """Read full case/evidence only when APP_ROLE is instructor."""
    settings = get_settings()
    with Session(_get_engine()) as session:
        return load_instructor_case(patient_id, session, settings)


def get_consultation_history_logic(patient_id: int) -> list[dict[str, str]]:
    """Rebuild the learner's own chat transcript for session recovery."""
    learner_case = get_learner_case_logic(patient_id)
    history: list[dict[str, str]] = [
        {"role": "assistant", "content": learner_case.opening_statement}
    ]
    with Session(_get_engine()) as session:
        for entry in ConsultationRepository(session).get_by_patient(patient_id):
            history.append({"role": "user", "content": entry.doctor_input})
            history.append({"role": "assistant", "content": entry.patient_response})
    return history


def consultation_chat_logic(
    patient_id: int,
    user_input: str,
    history: List[Dict[str, str]],
    api_key: str | None = None,
    encounter_session_id: str | None = None,
) -> str:
    """Generate the next patient chat response."""
    engine = get_engine_instance(api_key)
    db_engine = _get_engine()
    with Session(db_engine) as session:
        reply = engine.chat(patient_id=patient_id, user_input=user_input, history=history, session=session)
        if encounter_session_id:
            revealed_items: list[str] = []
            logs = ConsultationRepository(session).get_by_patient(patient_id)
            if logs and logs[-1].state_snapshot_json:
                try:
                    snapshot = json.loads(logs[-1].state_snapshot_json)
                    revealed_items = list(snapshot.get("revealed_hidden_items") or [])
                except (json.JSONDecodeError, AttributeError):
                    revealed_items = []
            ClinicalSkillRouter(session).record_history_question(
                encounter_session_id,
                user_input,
                reply,
                revealed_items,
            )
        return reply


def evaluate_consultation_logic(
    patient_id: int,
    history: List[Dict[str, str]],
    api_key: str | None = None,
    encounter_session_id: str | None = None,
) -> AssessmentResult:
    """Evaluate a completed consultation transcript."""
    engine = get_engine_instance(api_key)
    db_engine = _get_engine()
    with Session(db_engine) as session:
        result = engine.evaluate(
            patient_id=patient_id,
            history=history,
            session=session,
            encounter_session_id=encounter_session_id,
        )
        if encounter_session_id:
            dimension_scores = {
                name: detail["score"]
                for name, detail in (result.learning_profile or {}).get("dimensions", {}).items()
            }
            ClinicalSkillRouter(session).complete_assessment(
                encounter_session_id,
                result.score,
                dimension_scores=dimension_scores,
            )
        return result


def start_encounter_logic(
    *,
    patient_id: int,
    learner_id: str,
    case_id: str,
    training_goal: str,
    difficulty: str,
    retry_of_session_id: str | None = None,
    focused_retry: bool = False,
    focus_skills: list[str] | None = None,
    history_turn_limit: int | None = None,
) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        state = ClinicalSkillRouter(session).start_encounter(
            patient_id=patient_id,
            learner_id=learner_id,
            case_id=case_id,
            training_goal=training_goal,
            difficulty=difficulty,
            retry_of_session_id=retry_of_session_id,
            focused_retry=focused_retry,
            focus_skills=focus_skills,
            history_turn_limit=history_turn_limit,
        )
        return state.model_dump(mode="json")


def get_encounter_state_logic(session_id: str) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        return ClinicalSkillRouter(session).get_state(session_id).model_dump(mode="json")


def get_action_trace_logic(session_id: str) -> list[dict[str, Any]]:
    with Session(_get_engine()) as session:
        return [
            entry.model_dump(mode="json")
            for entry in ClinicalSkillRouter(session).get_trace(session_id)
        ]


def get_available_tools_logic(session_id: str) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        return ClinicalSkillRouter(session).available_tools(session_id)


def request_vital_signs_logic(session_id: str) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        return ClinicalSkillRouter(session).request_vital_signs(session_id).model_dump(mode="json")


def perform_physical_exam_logic(session_id: str, system: str) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        return ClinicalSkillRouter(session).perform_physical_exam(session_id, system).model_dump(mode="json")


def order_ecg_logic(session_id: str) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        return ClinicalSkillRouter(session).order_ecg(session_id).model_dump(mode="json")


def order_lab_test_logic(session_id: str, test_name: str) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        return ClinicalSkillRouter(session).order_lab_test(session_id, test_name).model_dump(mode="json")


def submit_differential_diagnosis_logic(
    session_id: str,
    diagnoses: list[str],
) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        return ClinicalSkillRouter(session).submit_differential_diagnosis(
            session_id,
            diagnoses,
        ).model_dump(mode="json")


def submit_management_plan_logic(session_id: str, plan: dict[str, Any]) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        return ClinicalSkillRouter(session).submit_management_plan(session_id, plan).model_dump(mode="json")


def request_hint_logic(session_id: str, level: int) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        return ClinicalSkillRouter(session).request_hint(session_id, level).model_dump(mode="json")


def finish_encounter_logic(session_id: str) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        return ClinicalSkillRouter(session).finish_encounter(session_id).model_dump(mode="json")


def get_learning_diagnosis_logic(session_id: str) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        return LearningDiagnosisService(session).get(session_id).model_dump(mode="json")


def start_focused_retry_logic(
    source_session_id: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    engine = get_engine_instance(api_key)
    with Session(_get_engine()) as session:
        router = ClinicalSkillRouter(session)
        source = router.get_state(source_session_id)
        if source.current_stage.value != "COMPLETED":
            raise ValueError("Focused retry requires a completed source encounter")
        learning = LearningDiagnosisService(session).get(source_session_id)
        case = load_case_by_id(learning.remediation_plan.recommended_case)
        created = engine.generate_patient_from_case_template(case=case, session=session)
        learner_case = project_learner_case(created["id"], created["profile"])
        retry = router.start_encounter(
            patient_id=created["id"],
            learner_id=source.learner_id,
            case_id=case.case_id,
            training_goal=learning.remediation_plan.learning_objective,
            difficulty=learning.remediation_plan.recommended_difficulty,
            retry_of_session_id=source_session_id,
            focused_retry=True,
            focus_skills=list(learning.remediation_plan.priority_skills),
            history_turn_limit=6,
        )
        return {
            "patient": {
                "id": created["id"],
                "case": learner_case.model_dump(mode="json"),
                "opening_statement": learner_case.opening_statement,
            },
            "encounter": retry.model_dump(mode="json"),
            "remediation_plan": learning.remediation_plan.model_dump(mode="json"),
        }


def compare_learning_progress_logic(
    first_session_id: str,
    second_session_id: str,
) -> dict[str, Any]:
    with Session(_get_engine()) as session:
        return LearningDiagnosisService(session).compare(
            first_session_id,
            second_session_id,
        ).model_dump(mode="json")


def get_teacher_dashboard_logic(learner_id: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    with Session(_get_engine()) as session:
        return TeacherDashboardService(session, settings).build(learner_id).model_dump(mode="json")


def export_teacher_dashboard_logic(
    learner_id: str | None = None,
    *,
    format: str = "markdown",
) -> str:
    settings = get_settings()
    with Session(_get_engine()) as session:
        service = TeacherDashboardService(session, settings)
        if format == "markdown":
            return service.export_markdown(learner_id)
        if format == "json":
            return service.export_json(learner_id)
        raise ValueError("Teacher report format must be 'markdown' or 'json'")


def list_case_templates_for_validation_logic() -> list[dict[str, str]]:
    return CaseTemplateValidationService(get_settings()).list_templates()


def validate_case_template_logic(case_id: str) -> dict[str, Any]:
    return CaseTemplateValidationService(get_settings()).validate_case_id(case_id).model_dump(
        mode="json"
    )


def export_case_validation_logic(
    result: dict[str, Any],
    *,
    format: str = "markdown",
) -> str:
    service = CaseTemplateValidationService(get_settings())
    validated = CaseTemplateValidationResult.model_validate(result)
    if format == "markdown":
        return service.export_markdown(validated)
    if format == "json":
        return service.export_json(validated)
    raise ValueError("Validation export format must be 'markdown' or 'json'")
