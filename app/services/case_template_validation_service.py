"""Instructor-facing YAML schema, disclosure, and safety-rule validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.core.config import AppSettings
from app.schemas.case_template_file import ClinicalCaseTemplate
from app.schemas.case_views import LearnerVisibleCase
from app.schemas.teacher import CaseTemplateValidationResult, ValidationIssue
from app.services.case_loader import DEFAULT_CASE_TEMPLATE_DIR


class CaseTemplateValidationService:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def list_templates(self) -> list[dict[str, str]]:
        self._require_instructor()
        templates: list[dict[str, str]] = []
        for path in sorted(DEFAULT_CASE_TEMPLATE_DIR.glob("*.y*ml")):
            try:
                raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            except (OSError, yaml.YAMLError):
                raw = {}
            templates.append(
                {
                    "filename": path.name,
                    "case_id": str(raw.get("case_id", "")) if isinstance(raw, dict) else "",
                    "title": str(raw.get("title", "")) if isinstance(raw, dict) else "",
                }
            )
        return templates

    def validate_case_id(self, case_id: str) -> CaseTemplateValidationResult:
        self._require_instructor()
        matches = [item for item in self.list_templates() if item["case_id"] == case_id]
        if len(matches) != 1:
            raise KeyError(f"Expected one template for case_id={case_id!r}; found {len(matches)}")
        return self.validate_path(DEFAULT_CASE_TEMPLATE_DIR / matches[0]["filename"])

    def validate_path(self, path: Path | str) -> CaseTemplateValidationResult:
        self._require_instructor()
        template_path = Path(path)
        schema_issues: list[ValidationIssue] = []
        hidden_issues: list[ValidationIssue] = []
        safety_issues: list[ValidationIssue] = []
        try:
            raw = yaml.safe_load(template_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raw = {}
            schema_issues.append(
                ValidationIssue(
                    severity="error",
                    code="file_read_error",
                    path="$",
                    message=f"Could not read template: {exc}",
                )
            )
        except yaml.YAMLError as exc:
            raw = {}
            schema_issues.append(
                ValidationIssue(
                    severity="error",
                    code="invalid_yaml",
                    path="$",
                    message=f"Invalid YAML: {exc}",
                )
            )
        if not isinstance(raw, dict):
            raw = {}
            schema_issues.append(
                ValidationIssue(
                    severity="error",
                    code="top_level_mapping_required",
                    path="$",
                    message="The YAML top level must be a mapping.",
                )
            )

        required_fields = {
            name for name, field in ClinicalCaseTemplate.model_fields.items() if field.is_required()
        }
        missing_fields = sorted(required_fields - set(raw))
        for field in missing_fields:
            schema_issues.append(
                ValidationIssue(
                    severity="error",
                    code="missing_required_field",
                    path=field,
                    message=f"Required top-level field {field!r} is missing.",
                )
            )

        validated: ClinicalCaseTemplate | None = None
        try:
            validated = ClinicalCaseTemplate.model_validate(raw)
        except ValidationError as exc:
            existing_missing = set(missing_fields)
            for error in exc.errors(include_url=False):
                path_text = ".".join(str(part) for part in error["loc"])
                if error["type"] == "missing" and path_text in existing_missing:
                    continue
                schema_issues.append(
                    ValidationIssue(
                        severity="error",
                        code=str(error["type"]),
                        path=path_text or "$",
                        message=str(error["msg"]),
                    )
                )

        hidden_items = raw.get("hidden_information") or []
        if not hidden_items:
            hidden_issues.append(
                ValidationIssue(
                    severity="warning",
                    code="no_hidden_information",
                    path="hidden_information",
                    message="No hidden-information teaching rule is configured.",
                )
            )
        elif isinstance(hidden_items, list):
            visible_seed = " ".join(
                str(raw.get(field, ""))
                for field in ("chief_complaint", "opening_statement")
            ).casefold()
            for index, item in enumerate(hidden_items):
                if not isinstance(item, dict):
                    continue
                condition = str(item.get("reveal_condition", "")).casefold()
                if not any(marker in condition for marker in ("ask", "direct", "only", "when")):
                    hidden_issues.append(
                        ValidationIssue(
                            severity="warning",
                            code="ambiguous_reveal_condition",
                            path=f"hidden_information.{index}.reveal_condition",
                            message="Reveal condition should state an explicit learner question or gate.",
                        )
                    )
                hidden_fact = str(item.get("item", "")).strip().casefold()
                if hidden_fact and hidden_fact in visible_seed:
                    hidden_issues.append(
                        ValidationIssue(
                            severity="error",
                            code="hidden_fact_in_initial_learner_view",
                            path=f"hidden_information.{index}.item",
                            message="A hidden fact appears in the chief complaint or opening statement.",
                        )
                    )

        safety = raw.get("safety_supervision")
        if not safety:
            safety_issues.append(
                ValidationIssue(
                    severity="warning",
                    code="safety_rules_not_configured",
                    path="safety_supervision",
                    message="No case-specific hard-block safety rule is configured.",
                )
            )
        elif isinstance(safety, dict):
            investigations = raw.get("investigations") or {}
            for test_name in safety.get("critical_tests") or []:
                if test_name not in investigations:
                    safety_issues.append(
                        ValidationIssue(
                            severity="error",
                            code="critical_test_not_configured",
                            path="safety_supervision.critical_tests",
                            message=f"Critical test {test_name!r} has no investigation result.",
                        )
                    )
            for field in (
                "unsafe_disposition_keywords",
                "escalation_keywords",
                "safety_net_keywords",
                "reflection_questions",
            ):
                if not safety.get(field):
                    safety_issues.append(
                        ValidationIssue(
                            severity="error",
                            code="empty_safety_rule_component",
                            path=f"safety_supervision.{field}",
                            message=f"Safety configuration field {field!r} must not be empty.",
                        )
                    )

        learner_preview: dict[str, Any] = {}
        if validated is not None:
            learner_preview = LearnerVisibleCase(
                patient_id=0,
                case_id=validated.case_id,
                age=str(validated.demographics.age),
                gender=validated.demographics.gender,
                encounter_setting=validated.specialty.replace("_", " ").title(),
                chief_complaint=validated.chief_complaint,
                opening_statement=validated.opening_statement,
                unlocked_evidence=[],
            ).model_dump(mode="json")

        all_issues = schema_issues + hidden_issues + safety_issues
        return CaseTemplateValidationResult(
            case_id=str(raw.get("case_id")) if raw.get("case_id") else None,
            filename=template_path.name,
            valid=not any(issue.severity == "error" for issue in all_issues),
            metadata={
                key: raw.get(key)
                for key in ("title", "specialty", "difficulty", "chief_complaint")
                if key in raw
            },
            missing_fields=missing_fields,
            schema_issues=schema_issues,
            hidden_rule_issues=hidden_issues,
            safety_rule_issues=safety_issues,
            learner_preview=learner_preview,
        )

    def export_json(self, result: CaseTemplateValidationResult) -> str:
        self._require_instructor()
        return json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)

    def export_markdown(self, result: CaseTemplateValidationResult) -> str:
        self._require_instructor()
        lines = [
            f"# Case Template Validation: {result.case_id or result.filename}",
            "",
            f"- File: {result.filename}",
            f"- Status: {'PASS' if result.valid else 'FAIL'}",
            f"- Checked at: {result.checked_at.isoformat()}",
            "",
            "## Metadata",
            "",
        ]
        lines.extend(f"- {key}: {value}" for key, value in result.metadata.items())
        for title, issues in (
            ("Schema", result.schema_issues),
            ("Hidden-information rules", result.hidden_rule_issues),
            ("Safety rules", result.safety_rule_issues),
        ):
            lines.extend(["", f"## {title}", ""])
            if issues:
                lines.extend(
                    f"- [{issue.severity.upper()}] `{issue.path}` {issue.code}: {issue.message}"
                    for issue in issues
                )
            else:
                lines.append("- PASS")
        lines.extend(["", "## Learner-visible preview", "", "```json"])
        lines.append(json.dumps(result.learner_preview, ensure_ascii=False, indent=2))
        lines.extend(["```", ""])
        return "\n".join(lines)

    def _require_instructor(self) -> None:
        if not self.settings.is_instructor:
            raise PermissionError("Case template validation requires APP_ROLE=instructor")
