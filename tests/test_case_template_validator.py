from __future__ import annotations

import json

import pytest

from app.schemas.case_views import LEARNER_FORBIDDEN_FIELDS


def _configure_role(monkeypatch, *, role: str = "instructor") -> None:
    monkeypatch.setenv("APP_ROLE", role)
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    from app.core.config import get_settings

    get_settings.cache_clear()


def test_chest_pain_template_passes_schema_hidden_and_safety_checks(monkeypatch):
    _configure_role(monkeypatch)
    from app.streamlit_services import (
        export_case_validation_logic,
        validate_case_template_logic,
    )

    result = validate_case_template_logic("chest_pain_001")
    assert result["valid"] is True
    assert result["missing_fields"] == []
    assert result["schema_issues"] == []
    assert not [issue for issue in result["hidden_rule_issues"] if issue["severity"] == "error"]
    assert not [issue for issue in result["safety_rule_issues"] if issue["severity"] == "error"]
    assert result["metadata"]["specialty"] == "emergency_medicine"
    assert set(result["learner_preview"]).isdisjoint(LEARNER_FORBIDDEN_FIELDS)
    preview = json.dumps(result["learner_preview"], ensure_ascii=False).lower()
    assert "cocaine" not in preview
    assert "acute coronary syndrome" not in preview
    assert "scoring_rubric" not in preview

    markdown = export_case_validation_logic(result, format="markdown")
    exported = json.loads(export_case_validation_logic(result, format="json"))
    assert "Status: PASS" in markdown
    assert "## Learner-visible preview" in markdown
    assert exported["valid"] is True


def test_all_existing_templates_remain_schema_compatible_and_nonacute_case_warns(monkeypatch):
    _configure_role(monkeypatch)
    from app.streamlit_services import (
        list_case_templates_for_validation_logic,
        validate_case_template_logic,
    )

    templates = list_case_templates_for_validation_logic()
    assert len(templates) == 20
    results = [validate_case_template_logic(item["case_id"]) for item in templates]
    assert all(result["valid"] for result in results)

    nonacute = next(result for result in results if result["case_id"] == "hypertension_followup_001")
    assert nonacute["metadata"]["difficulty"] == "beginner"
    assert any(
        issue["code"] == "safety_rules_not_configured"
        and issue["severity"] == "warning"
        for issue in nonacute["safety_rule_issues"]
    )


def test_invalid_author_template_reports_missing_fields_and_hidden_leak(monkeypatch, tmp_path):
    _configure_role(monkeypatch)
    from app.core.config import get_settings
    from app.services.case_template_validation_service import CaseTemplateValidationService

    invalid = tmp_path / "invalid_author_case.yaml"
    invalid.write_text(
        "\n".join(
            [
                "case_id: invalid_author_case",
                "title: Invalid author case",
                "chief_complaint: Secret medicine use",
                "opening_statement: I am hiding secret medicine use",
                "hidden_information:",
                "  - item: secret medicine use",
                "    reveal_condition: always",
                "    clinical_relevance: test fixture",
            ]
        ),
        encoding="utf-8",
    )
    result = CaseTemplateValidationService(get_settings()).validate_path(invalid)

    assert result.valid is False
    assert "demographics" in result.missing_fields
    assert "scoring_rubric" in result.missing_fields
    assert any(issue.code == "hidden_fact_in_initial_learner_view" for issue in result.hidden_rule_issues)
    assert any(issue.code == "safety_rules_not_configured" for issue in result.safety_rule_issues)
    assert result.learner_preview == {}


def test_template_validator_is_not_available_to_learner(monkeypatch):
    _configure_role(monkeypatch, role="learner")
    from app.streamlit_services import validate_case_template_logic

    with pytest.raises(PermissionError, match="APP_ROLE=instructor"):
        validate_case_template_logic("chest_pain_001")
