"""Lightweight, local learner-id teacher dashboard with role-gated exports."""

from __future__ import annotations

import json
from typing import Any

from sqlmodel import Session

from app.core.config import AppSettings
from app.repositories.learning_repository import LearningDiagnosisRepository
from app.repositories.training_repository import ActionTraceRepository, TrainingSessionRepository
from app.schemas.teacher import TeacherDashboard, TeacherTrainingRecord
from app.services.learning_diagnosis_service import LearningDiagnosisService


class TeacherDashboardService:
    def __init__(self, session: Session, settings: AppSettings) -> None:
        self.session = session
        self.settings = settings
        self.sessions = TrainingSessionRepository(session)
        self.traces = ActionTraceRepository(session)
        self.learning = LearningDiagnosisRepository(session)

    def build(self, learner_id: str | None = None) -> TeacherDashboard:
        self._require_instructor()
        all_states = self.sessions.list_all()
        available_learners = sorted({state.learner_id for state in all_states})
        selected = (
            [state for state in all_states if state.learner_id == learner_id]
            if learner_id
            else all_states
        )
        records: list[TeacherTrainingRecord] = []
        for state in selected:
            trace = self.traces.list_by_session(state.session_id)
            learning = self.learning.get(state.session_id)
            dimension_scores = (
                {
                    name: diagnosis.score
                    for name, diagnosis in learning.profile.dimensions.items()
                }
                if learning
                else {}
            )
            safety_events = sorted(
                set(state.safety_flags).union(
                    event for entry in trace for event in entry.safety_event
                )
            )
            progress = None
            if state.retry_of_session_id and learning:
                try:
                    progress = LearningDiagnosisService(self.session).compare(
                        state.retry_of_session_id,
                        state.session_id,
                    )
                except (KeyError, ValueError):
                    progress = None
            records.append(
                TeacherTrainingRecord(
                    session_id=state.session_id,
                    learner_id=state.learner_id,
                    patient_id=state.patient_id,
                    case_id=state.case_id,
                    training_goal=state.training_goal,
                    difficulty=state.difficulty,
                    current_stage=state.current_stage.value,
                    retry_of_session_id=state.retry_of_session_id,
                    overall_score=learning.profile.overall_score if learning else None,
                    dimension_scores=dimension_scores,
                    action_trace=[entry.model_dump(mode="json") for entry in trace],
                    safety_events=safety_events,
                    hints_used=state.hints_used,
                    elapsed_time=state.elapsed_time,
                    progress_report=progress,
                    created_at=state.created_at,
                    updated_at=state.updated_at,
                )
            )
        return TeacherDashboard(
            learner_filter=learner_id,
            available_learners=available_learners,
            records=records,
        )

    def export_json(self, learner_id: str | None = None) -> str:
        dashboard = self.build(learner_id)
        return json.dumps(dashboard.model_dump(mode="json"), ensure_ascii=False, indent=2)

    def export_markdown(self, learner_id: str | None = None) -> str:
        dashboard = self.build(learner_id)
        label = dashboard.learner_filter or "All local learners"
        lines = [
            "# SimuPatient Teacher Training Report",
            "",
            f"- Learner filter: {label}",
            f"- Generated at: {dashboard.generated_at.isoformat()}",
            "- Use: formative teaching support only; not a validated OSCE grade.",
            "",
        ]
        if not dashboard.records:
            lines.append("No structured training records found.")
            return "\n".join(lines) + "\n"

        for record in dashboard.records:
            lines.extend(
                [
                    f"## Session {record.session_id}",
                    "",
                    f"- Learner: {record.learner_id}",
                    f"- Case: {record.case_id}",
                    f"- Goal: {record.training_goal}",
                    f"- Difficulty / stage: {record.difficulty} / {record.current_stage}",
                    f"- Retry of: {record.retry_of_session_id or '—'}",
                    f"- Overall formative score: {record.overall_score if record.overall_score is not None else 'not assessed'}",
                    f"- Simulated time: {record.elapsed_time} min",
                    f"- Hints used: {record.hints_used or 'none'}",
                    f"- Safety events: {record.safety_events or 'none'}",
                    "",
                    "### Dimension scores",
                    "",
                ]
            )
            if record.dimension_scores:
                lines.extend(
                    f"- {name}: {score}/100"
                    for name, score in record.dimension_scores.items()
                )
            else:
                lines.append("- Not assessed")
            lines.extend(["", "### Action Trace", "", "| Stage | Tool | Status | Time | Safety |", "|---|---|---|---:|---|"])
            for entry in record.action_trace:
                result = entry.get("result_summary") or {}
                safety = ", ".join(entry.get("safety_event") or [])
                lines.append(
                    "| {stage} | {tool} | {status} | {time} | {safety} |".format(
                        stage=self._cell(entry.get("stage", "")),
                        tool=self._cell(entry.get("tool_name") or ""),
                        status=self._cell(result.get("status", "")),
                        time=entry.get("time_cost", 0),
                        safety=self._cell(safety),
                    )
                )
            if record.progress_report:
                progress = record.progress_report
                lines.extend(
                    [
                        "",
                        "### First vs second attempt",
                        "",
                        f"- Total: {progress.first_total_score} → {progress.second_total_score}",
                        f"- Dimension changes: {progress.dimension_changes}",
                        f"- Resolved safety omissions: {progress.safety_critical_omissions_change.resolved or 'none'}",
                        f"- Hints: {progress.first_hints_used} → {progress.second_hints_used}",
                        f"- Time: {progress.first_completion_time} → {progress.second_completion_time} min",
                        f"- Interpretation: {progress.interpretation}",
                    ]
                )
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _require_instructor(self) -> None:
        if not self.settings.is_instructor:
            raise PermissionError("Teacher dashboard access requires APP_ROLE=instructor")

    @staticmethod
    def _cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")
