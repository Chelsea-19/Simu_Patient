"""Persistence for encounter state and append-only action traces."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.training_session import ActionTraceRecord, TrainingSessionRecord
from app.schemas.case_views import UnlockedEvidence
from app.schemas.encounter import ActionTraceEntry, EncounterStage, EncounterState


class TrainingSessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, state: EncounterState) -> EncounterState:
        record = TrainingSessionRecord(
            session_id=state.session_id,
            patient_id=state.patient_id,
            learner_id=state.learner_id,
            case_id=state.case_id,
            current_stage=state.current_stage.value,
            state_json=state.model_dump_json(),
            created_at=state.created_at,
            updated_at=state.updated_at,
        )
        self.session.add(record)
        self.session.commit()
        return state

    def get(self, session_id: str) -> EncounterState | None:
        record = self.session.get(TrainingSessionRecord, session_id)
        if record is None:
            return None
        return EncounterState.model_validate_json(record.state_json)

    def save(self, state: EncounterState) -> EncounterState:
        record = self.session.get(TrainingSessionRecord, state.session_id)
        if record is None:
            raise KeyError(f"Training session {state.session_id!r} does not exist")
        state.updated_at = datetime.now(timezone.utc)
        record.current_stage = state.current_stage.value
        record.state_json = state.model_dump_json()
        record.updated_at = state.updated_at
        self.session.add(record)
        self.session.commit()
        return state

    def get_latest_by_patient(self, patient_id: int) -> EncounterState | None:
        statement = (
            select(TrainingSessionRecord)
            .where(TrainingSessionRecord.patient_id == patient_id)
            .order_by(TrainingSessionRecord.updated_at.desc())  # type: ignore[union-attr]
        )
        record = self.session.exec(statement).first()
        return EncounterState.model_validate_json(record.state_json) if record else None

    def list_all(self) -> list[EncounterState]:
        statement = select(TrainingSessionRecord).order_by(
            TrainingSessionRecord.created_at,
            TrainingSessionRecord.session_id,
        )
        return [
            EncounterState.model_validate_json(record.state_json)
            for record in self.session.exec(statement).all()
        ]

    def list_by_learner(self, learner_id: str) -> list[EncounterState]:
        statement = (
            select(TrainingSessionRecord)
            .where(TrainingSessionRecord.learner_id == learner_id)
            .order_by(TrainingSessionRecord.created_at, TrainingSessionRecord.session_id)
        )
        return [
            EncounterState.model_validate_json(record.state_json)
            for record in self.session.exec(statement).all()
        ]


class ActionTraceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append(self, entry: ActionTraceEntry) -> ActionTraceEntry:
        record = ActionTraceRecord(
            action_id=entry.action_id,
            session_id=entry.session_id,
            timestamp=entry.timestamp,
            stage=entry.stage.value,
            natural_language_input=entry.natural_language_input,
            structured_action_json=json.dumps(entry.structured_action, ensure_ascii=False),
            tool_name=entry.tool_name,
            tool_parameters_json=json.dumps(entry.tool_parameters, ensure_ascii=False),
            result_summary_json=json.dumps(entry.result_summary, ensure_ascii=False),
            evidence_unlocked_json=json.dumps(
                [item.model_dump(mode="json") for item in entry.evidence_unlocked],
                ensure_ascii=False,
            ),
            time_cost=entry.time_cost,
            hint_level=entry.hint_level,
            safety_event_json=json.dumps(entry.safety_event, ensure_ascii=False),
            score_event_json=json.dumps(entry.score_event, ensure_ascii=False),
        )
        self.session.add(record)
        self.session.commit()
        return entry

    def list_by_session(self, session_id: str) -> list[ActionTraceEntry]:
        statement = (
            select(ActionTraceRecord)
            .where(ActionTraceRecord.session_id == session_id)
            .order_by(ActionTraceRecord.timestamp, ActionTraceRecord.action_id)
        )
        records = self.session.exec(statement).all()
        return [self._to_schema(record) for record in records]

    @staticmethod
    def _to_schema(record: ActionTraceRecord) -> ActionTraceEntry:
        evidence = [
            UnlockedEvidence.model_validate(item)
            for item in json.loads(record.evidence_unlocked_json)
        ]
        return ActionTraceEntry(
            action_id=record.action_id,
            session_id=record.session_id,
            timestamp=record.timestamp,
            stage=EncounterStage(record.stage),
            natural_language_input=record.natural_language_input,
            structured_action=json.loads(record.structured_action_json),
            tool_name=record.tool_name,
            tool_parameters=json.loads(record.tool_parameters_json),
            result_summary=json.loads(record.result_summary_json),
            evidence_unlocked=evidence,
            time_cost=record.time_cost,
            hint_level=record.hint_level,
            safety_event=json.loads(record.safety_event_json),
            score_event=json.loads(record.score_event_json),
        )
