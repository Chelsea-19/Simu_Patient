from __future__ import annotations

from typing import Any, Dict, List

from sqlmodel import Session

from app.core.config import get_settings
from app.db.session import _get_engine, init_db
from app.providers.factory import get_llm_provider
from app.schemas.assessment import AssessmentResult
from app.schemas.case_template_file import ClinicalCaseTemplate
from app.services.case_loader import get_available_cases, load_case_by_id
from app.services.simu_engine import SimuEngine


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
    """Generate and persist a patient profile."""
    engine = get_engine_instance(api_key)
    db_engine = _get_engine()
    with Session(db_engine) as session:
        return engine.generate_patient(seed_text=seed_text, template_id=template_id, session=session)


def list_case_templates_logic() -> List[ClinicalCaseTemplate]:
    """Return validated YAML case templates for the Streamlit selector."""
    return list(get_available_cases())


def create_patient_from_case_logic(
    case_id: str,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """Initialize and persist a patient from a YAML case template."""
    case = load_case_by_id(case_id)
    engine = get_engine_instance(api_key)
    db_engine = _get_engine()
    with Session(db_engine) as session:
        return engine.generate_patient_from_case_template(case=case, session=session)


def consultation_chat_logic(
    patient_id: int,
    user_input: str,
    history: List[Dict[str, str]],
    api_key: str | None = None,
) -> str:
    """Generate the next patient chat response."""
    engine = get_engine_instance(api_key)
    db_engine = _get_engine()
    with Session(db_engine) as session:
        return engine.chat(patient_id=patient_id, user_input=user_input, history=history, session=session)


def evaluate_consultation_logic(
    patient_id: int,
    history: List[Dict[str, str]],
    api_key: str | None = None,
) -> AssessmentResult:
    """Evaluate a completed consultation transcript."""
    engine = get_engine_instance(api_key)
    db_engine = _get_engine()
    with Session(db_engine) as session:
        return engine.evaluate(patient_id=patient_id, history=history, session=session)
