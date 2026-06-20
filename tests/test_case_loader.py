from __future__ import annotations

import pytest


def test_all_yaml_case_templates_load_successfully():
    from app.services.case_loader import load_case_templates

    cases = load_case_templates()

    assert len(cases) >= 20
    assert all(case.case_id for case in cases)
    assert all(case.title for case in cases)


def test_loading_by_case_id_works():
    from app.services.case_loader import load_case_by_id

    case = load_case_by_id("chest_pain_001")

    assert case.title == "Acute chest pain with cardiac risk factors"
    assert case.chief_complaint == "Chest pain for 2 hours"


def test_missing_required_fields_raise_validation_error(tmp_path):
    from app.schemas.case_template_file import CaseTemplateValidationError
    from app.services.case_loader import load_case_templates

    invalid = tmp_path / "invalid_case.yaml"
    invalid.write_text(
        """
case_id: invalid_001
title: Missing required fields
specialty: primary_care
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(CaseTemplateValidationError, match="chief_complaint"):
        load_case_templates(tmp_path)
