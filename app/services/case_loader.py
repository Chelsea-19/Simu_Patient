from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable, List

import yaml
from pydantic import ValidationError

from app.schemas.case_template_file import ClinicalCaseTemplate, CaseTemplateValidationError

DEFAULT_CASE_TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "case_templates"


def _case_files(case_dir: Path) -> Iterable[Path]:
    return sorted(list(case_dir.glob("*.yaml")) + list(case_dir.glob("*.yml")))


def load_case_template_file(path: Path | str) -> ClinicalCaseTemplate:
    """Load and validate a single YAML case template."""
    template_path = Path(path)
    try:
        raw = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CaseTemplateValidationError(f"Could not read case template {template_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise CaseTemplateValidationError(f"Invalid YAML in {template_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise CaseTemplateValidationError(f"{template_path} must contain a YAML mapping at the top level.")

    try:
        return ClinicalCaseTemplate.model_validate(raw)
    except ValidationError as exc:
        raise CaseTemplateValidationError(f"Invalid case template {template_path}: {exc}") from exc


def load_case_templates(case_dir: Path | str = DEFAULT_CASE_TEMPLATE_DIR) -> List[ClinicalCaseTemplate]:
    """Read and validate all YAML case templates from a directory."""
    directory = Path(case_dir)
    if not directory.exists():
        raise CaseTemplateValidationError(f"Case template directory does not exist: {directory}")

    cases = [load_case_template_file(path) for path in _case_files(directory)]
    case_ids = [case.case_id for case in cases]
    duplicates = sorted({case_id for case_id in case_ids if case_ids.count(case_id) > 1})
    if duplicates:
        raise CaseTemplateValidationError(f"Duplicate case_id values found: {', '.join(duplicates)}")

    return sorted(cases, key=lambda case: case.title.lower())


@lru_cache()
def get_available_cases() -> tuple[ClinicalCaseTemplate, ...]:
    """Return cached validated case templates from the default case directory."""
    return tuple(load_case_templates(DEFAULT_CASE_TEMPLATE_DIR))


def load_case_by_id(case_id: str, case_dir: Path | str = DEFAULT_CASE_TEMPLATE_DIR) -> ClinicalCaseTemplate:
    """Load one case template by case_id."""
    for case in load_case_templates(case_dir):
        if case.case_id == case_id:
            return case
    raise CaseTemplateValidationError(f"No case template found with case_id={case_id!r}")
