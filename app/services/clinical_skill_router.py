"""Deterministic clinical tools backed exclusively by structured YAML facts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlmodel import Session

from app.repositories.training_repository import ActionTraceRepository, TrainingSessionRepository
from app.schemas.case_template_file import ConfiguredClinicalEvidence
from app.schemas.case_views import UnlockedEvidence
from app.schemas.encounter import ActionTraceEntry, EncounterStage, EncounterState, ToolResult
from app.services.case_loader import load_case_by_id
from app.services.encounter_state_machine import EncounterStateMachine
from app.services.safety_supervisor import SafetySupervisor


HISTORY_REVISIT_STAGES = {
    EncounterStage.HISTORY_TAKING,
    EncounterStage.EXAMINATION,
    EncounterStage.INVESTIGATION,
    EncounterStage.CLINICAL_REASONING,
    EncounterStage.MANAGEMENT,
}
EXAMINATION_STAGES = {
    EncounterStage.HISTORY_TAKING,
    EncounterStage.EXAMINATION,
    EncounterStage.INVESTIGATION,
    EncounterStage.CLINICAL_REASONING,
}
INVESTIGATION_STAGES = {
    EncounterStage.EXAMINATION,
    EncounterStage.INVESTIGATION,
    EncounterStage.CLINICAL_REASONING,
    EncounterStage.MANAGEMENT,
}
STAGE_ORDER = {
    stage: index
    for index, stage in enumerate(
        [
            EncounterStage.CASE_INTRO,
            EncounterStage.HISTORY_TAKING,
            EncounterStage.EXAMINATION,
            EncounterStage.INVESTIGATION,
            EncounterStage.CLINICAL_REASONING,
            EncounterStage.MANAGEMENT,
            EncounterStage.SAFETY_REVIEW,
            EncounterStage.ASSESSMENT,
            EncounterStage.REMEDIATION,
            EncounterStage.COMPLETED,
        ]
    )
}


class ClinicalSkillRouter:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.sessions = TrainingSessionRepository(session)
        self.trace = ActionTraceRepository(session)
        self.machine = EncounterStateMachine()

    def start_encounter(
        self,
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
    ) -> EncounterState:
        state = EncounterState(
            session_id=str(uuid4()),
            learner_id=learner_id,
            patient_id=patient_id,
            case_id=case_id,
            training_goal=training_goal,
            difficulty=difficulty,
            retry_of_session_id=retry_of_session_id,
            focused_retry=focused_retry,
            focus_skills=focus_skills or [],
            history_turn_limit=history_turn_limit,
            actions_taken=["start_encounter"],
        )
        self.sessions.create(state)
        self._append_trace(
            state=state,
            stage=EncounterStage.CASE_INTRO,
            structured_action={"type": "start_encounter"},
            tool_name="start_encounter",
            result_summary={
                "status": "success",
                "case_id": case_id,
                "retry_of_session_id": retry_of_session_id,
                "focused_retry": focused_retry,
                "focus_skills": focus_skills or [],
            },
        )
        return state

    def get_state(self, session_id: str) -> EncounterState:
        state = self.sessions.get(session_id)
        if state is None:
            raise KeyError(f"Encounter session {session_id!r} was not found")
        return state

    def get_trace(self, session_id: str) -> list[ActionTraceEntry]:
        self.get_state(session_id)
        return self.trace.list_by_session(session_id)

    def available_tools(self, session_id: str) -> dict[str, Any]:
        state = self.get_state(session_id)
        case = load_case_by_id(state.case_id)
        return {
            "vital_signs": case.vital_signs is not None,
            "physical_examinations": sorted(case.physical_examination),
            "ecg": "ecg" in case.investigations,
            "lab_tests": sorted(
                name for name, config in case.investigations.items() if config.kind == "lab"
            ),
        }

    def record_history_question(
        self,
        session_id: str,
        question: str,
        patient_response: str,
        revealed_hidden_items: list[str] | None = None,
    ) -> EncounterState:
        state = self.get_state(session_id)
        stage_at_action = state.current_stage
        if state.current_stage == EncounterStage.CASE_INTRO:
            self.machine.transition(state, EncounterStage.HISTORY_TAKING)
        elif state.current_stage not in HISTORY_REVISIT_STAGES:
            self._trace_state_error(
                state,
                "ask_history_question",
                stage_at_action,
                "History questions are unavailable after the encounter is closed.",
                natural_language_input=question,
            )
            return state

        new_evidence = [
            self._evidence(
                evidence_id=f"history:hidden:{index}:{item}",
                category="history",
                label="History disclosure",
                value=item,
                source_action="ask_history_question",
            )
            for index, item in enumerate(revealed_hidden_items or [])
            if not self._has_evidence_value(state, item)
        ]
        state.questions_asked.append(question)
        state.actions_taken.append("ask_history_question")
        state.elapsed_time += 1
        state.evidence_unlocked.extend(new_evidence)
        self.sessions.save(state)
        self._append_trace(
            state=state,
            stage=stage_at_action,
            natural_language_input=question,
            structured_action={"type": "history_question"},
            tool_name="ask_history_question",
            result_summary={"status": "success", "patient_response": patient_response},
            evidence_unlocked=new_evidence,
            time_cost=1,
        )
        return state

    def request_vital_signs(self, session_id: str) -> ToolResult:
        state = self.get_state(session_id)
        case = load_case_by_id(state.case_id)
        config = case.vital_signs
        if config is None:
            return self._error(state, "request_vital_signs", "Vital signs are not configured for this case.")
        return self._configured_tool(
            state=state,
            tool_name="request_vital_signs",
            evidence_id="vital_signs",
            label="Vital signs",
            category="vital_signs",
            config=config,
            duplicate_key="vital_signs",
            duplicate_collection=state.tests_ordered,
            allowed_stages=EXAMINATION_STAGES,
            success_stage=EncounterStage.EXAMINATION,
        )

    def perform_physical_exam(self, session_id: str, system: str) -> ToolResult:
        state = self.get_state(session_id)
        normalized = system.strip().lower()
        case = load_case_by_id(state.case_id)
        config = case.physical_examination.get(normalized)
        if config is None:
            return self._error(
                state,
                "perform_physical_exam",
                f"Physical examination system {system!r} is not configured for this case.",
                parameters={"system": system},
            )
        return self._configured_tool(
            state=state,
            tool_name="perform_physical_exam",
            evidence_id=f"physical_exam:{normalized}",
            label=f"{normalized.replace('_', ' ').title()} examination",
            category="physical_examination",
            config=config,
            duplicate_key=normalized,
            duplicate_collection=state.physical_exams_completed,
            allowed_stages=EXAMINATION_STAGES,
            success_stage=EncounterStage.EXAMINATION,
            parameters={"system": normalized},
        )

    def order_ecg(self, session_id: str) -> ToolResult:
        state = self.get_state(session_id)
        case = load_case_by_id(state.case_id)
        config = case.investigations.get("ecg")
        if config is None:
            return self._error(state, "order_ecg", "ECG is not configured for this case.")
        return self._configured_tool(
            state=state,
            tool_name="order_ecg",
            evidence_id="investigation:ecg",
            label="ECG",
            category="investigation",
            config=config,
            duplicate_key="ecg",
            duplicate_collection=state.tests_ordered,
            allowed_stages=INVESTIGATION_STAGES,
            success_stage=EncounterStage.INVESTIGATION,
        )

    def order_lab_test(self, session_id: str, test_name: str) -> ToolResult:
        state = self.get_state(session_id)
        normalized = test_name.strip().lower()
        case = load_case_by_id(state.case_id)
        config = case.investigations.get(normalized)
        if config is None or config.kind != "lab":
            return self._error(
                state,
                "order_lab_test",
                f"Lab test {test_name!r} is not configured for this case.",
                parameters={"test_name": test_name},
            )
        return self._configured_tool(
            state=state,
            tool_name="order_lab_test",
            evidence_id=f"investigation:{normalized}",
            label=normalized.replace("_", " ").title(),
            category="investigation",
            config=config,
            duplicate_key=normalized,
            duplicate_collection=state.tests_ordered,
            allowed_stages=INVESTIGATION_STAGES,
            success_stage=EncounterStage.INVESTIGATION,
            parameters={"test_name": normalized},
        )

    def submit_differential_diagnosis(
        self,
        session_id: str,
        diagnoses: list[str],
    ) -> ToolResult:
        state = self.get_state(session_id)
        cleaned = list(dict.fromkeys(item.strip() for item in diagnoses if item.strip()))
        if state.current_stage not in {
            EncounterStage.INVESTIGATION,
            EncounterStage.CLINICAL_REASONING,
            EncounterStage.MANAGEMENT,
        }:
            return self._error(
                state,
                "submit_differential_diagnosis",
                "Submit a differential after completing at least one investigation.",
                parameters={"diagnoses": cleaned},
            )
        if not cleaned:
            return self._error(
                state,
                "submit_differential_diagnosis",
                "Provide at least one diagnosis.",
                parameters={"diagnoses": []},
            )
        stage_at_action = state.current_stage
        state.differential_diagnoses = cleaned
        state.actions_taken.append("submit_differential_diagnosis")
        state.elapsed_time += 2
        if state.current_stage == EncounterStage.INVESTIGATION:
            self.machine.transition(state, EncounterStage.CLINICAL_REASONING)
        self.sessions.save(state)
        return self._success_result(
            state,
            stage_at_action,
            "submit_differential_diagnosis",
            result={"diagnoses": cleaned},
            time_cost=2,
            learner_message="Differential diagnosis submitted. You may revise it before finishing.",
            parameters={"diagnoses": cleaned},
        )

    def submit_management_plan(self, session_id: str, plan: dict[str, Any]) -> ToolResult:
        state = self.get_state(session_id)
        cleaned = {str(key): value for key, value in plan.items() if str(value).strip()}
        if state.current_stage not in {EncounterStage.CLINICAL_REASONING, EncounterStage.MANAGEMENT}:
            return self._error(
                state,
                "submit_management_plan",
                "Submit a management plan after the differential diagnosis.",
                parameters={"plan": cleaned},
            )
        if not cleaned:
            return self._error(
                state,
                "submit_management_plan",
                "Management plan cannot be empty.",
                parameters={"plan": {}},
            )
        stage_at_action = state.current_stage
        state.management_plan = cleaned
        state.actions_taken.append("submit_management_plan")
        state.elapsed_time += 3
        if state.current_stage == EncounterStage.CLINICAL_REASONING:
            self.machine.transition(state, EncounterStage.MANAGEMENT)
        self.sessions.save(state)
        return self._success_result(
            state,
            stage_at_action,
            "submit_management_plan",
            result={"plan": cleaned},
            time_cost=3,
            learner_message="Management plan submitted. Review safety before finishing.",
            parameters={"plan": cleaned},
        )

    def request_hint(self, session_id: str, level: int) -> ToolResult:
        state = self.get_state(session_id)
        if level not in {1, 2, 3}:
            return self._error(
                state,
                "request_hint",
                "Hint level must be 1, 2, or 3.",
                parameters={"level": level},
            )
        if state.current_stage == EncounterStage.COMPLETED:
            return self._error(state, "request_hint", "The encounter is already complete.")
        if state.case_id == "chest_pain_001":
            prompts = {
                1: "What potentially life-threatening category of chest pain has not yet been assessed?",
                2: "Recheck the pain characteristics, cardiovascular risks, and drug or stimulant use.",
                3: (
                    "A focused acute chest-pain history usually covers onset, character, radiation, "
                    "associated symptoms, risk factors, and stimulant use."
                ),
            }
        else:
            prompts = {
                1: "Pause and ask which missing information could most change urgency or risk.",
                2: "Review the current stage and identify one high-yield history, examination, or investigation gap.",
                3: (
                    "Use the stage checklist: collect focused evidence, synthesize a differential, "
                    "then propose a safe plan."
                ),
            }
        stage_at_action = state.current_stage
        state.hints_used.append(level)
        state.actions_taken.append("request_hint")
        state.elapsed_time += 1
        self.sessions.save(state)
        return self._success_result(
            state,
            stage_at_action,
            "request_hint",
            result={"hint_level": level, "hint": prompts[level]},
            time_cost=1,
            learner_message=prompts[level],
            parameters={"level": level},
            hint_level=level,
        )

    def finish_encounter(self, session_id: str) -> ToolResult:
        state = self.get_state(session_id)
        if state.current_stage != EncounterStage.MANAGEMENT:
            return self._error(
                state,
                "finish_encounter",
                "Complete the differential diagnosis and management plan before finishing.",
            )
        if not state.differential_diagnoses or not state.management_plan:
            return self._error(
                state,
                "finish_encounter",
                "A differential diagnosis and management plan are required.",
            )
        stage_at_action = state.current_stage
        review = SafetySupervisor().evaluate(state)
        state.safety_flags = review.triggered_rules
        state.actions_taken.append("finish_encounter")
        state.elapsed_time += 1
        if review.decision == "block_completion":
            state.assessment_status = "blocked_by_safety"
            self.sessions.save(state)
            output = ToolResult(
                tool_name="finish_encounter",
                status="error",
                result={"safety_review": review.model_dump(mode="json")},
                time_cost=1,
                safety_events=review.triggered_rules,
                learner_message=review.learner_feedback,
                current_stage=state.current_stage,
            )
            self._append_trace(
                state=state,
                stage=stage_at_action,
                structured_action={
                    "type": "safety_review",
                    "status": "blocked",
                    "decision": review.decision,
                },
                tool_name="finish_encounter",
                result_summary=output.model_dump(mode="json"),
                time_cost=1,
                safety_event=review.triggered_rules,
            )
            return output

        self.machine.transition(state, EncounterStage.SAFETY_REVIEW)
        self.machine.transition(state, EncounterStage.ASSESSMENT)
        state.assessment_status = "ready"
        self.sessions.save(state)
        return self._success_result(
            state,
            stage_at_action,
            "finish_encounter",
            result={
                "assessment_status": "ready",
                "safety_review": review.model_dump(mode="json"),
            },
            time_cost=1,
            learner_message="Encounter locked for formative assessment.",
            safety_events=review.triggered_rules,
        )

    def complete_assessment(
        self,
        session_id: str,
        score: int,
        dimension_scores: dict[str, int] | None = None,
    ) -> EncounterState:
        state = self.get_state(session_id)
        if state.current_stage != EncounterStage.ASSESSMENT:
            raise ValueError("Encounter must be in ASSESSMENT before completion")
        stage_at_action = state.current_stage
        self.machine.transition(state, EncounterStage.COMPLETED)
        state.assessment_status = "completed"
        state.actions_taken.append("complete_assessment")
        self.sessions.save(state)
        self._append_trace(
            state=state,
            stage=stage_at_action,
            structured_action={"type": "complete_assessment"},
            tool_name="complete_assessment",
            result_summary={"status": "success", "score": score},
            score_event={
                "formative_score": score,
                "dimension_scores": dimension_scores or {},
                "learning_profile_session_id": session_id if dimension_scores else None,
            },
        )
        return state

    def _configured_tool(
        self,
        *,
        state: EncounterState,
        tool_name: str,
        evidence_id: str,
        label: str,
        category: str,
        config: ConfiguredClinicalEvidence,
        duplicate_key: str,
        duplicate_collection: list[str],
        allowed_stages: set[EncounterStage],
        success_stage: EncounterStage,
        parameters: dict[str, Any] | None = None,
    ) -> ToolResult:
        parameters = parameters or {}
        if state.current_stage not in allowed_stages or not self._unlock_condition_met(
            config.unlock_condition,
            state.current_stage,
        ):
            return self._error(
                state,
                tool_name,
                f"{tool_name} is not available during {state.current_stage.value}.",
                parameters=parameters,
            )
        if duplicate_key in duplicate_collection:
            return self._duplicate(
                state,
                tool_name,
                f"{label} has already been completed; the existing result remains available.",
                parameters=parameters,
                result=config.result,
            )

        stage_at_action = state.current_stage
        evidence = self._evidence(
            evidence_id=evidence_id,
            category=category,
            label=label,
            value=config.result,
            source_action=tool_name,
        )
        duplicate_collection.append(duplicate_key)
        state.evidence_unlocked.append(evidence)
        state.actions_taken.append(tool_name)
        state.elapsed_time += config.time_cost
        if state.current_stage != success_stage and self.machine.can_transition(
            state.current_stage,
            success_stage,
        ):
            self.machine.transition(state, success_stage)
        self.sessions.save(state)
        return self._success_result(
            state,
            stage_at_action,
            tool_name,
            result=config.result,
            evidence=[evidence],
            time_cost=config.time_cost,
            learner_message=f"{label} completed and added to the evidence panel.",
            parameters=parameters,
        )

    def _success_result(
        self,
        state: EncounterState,
        stage_at_action: EncounterStage,
        tool_name: str,
        *,
        result: dict[str, Any],
        time_cost: int,
        learner_message: str,
        evidence: list[UnlockedEvidence] | None = None,
        parameters: dict[str, Any] | None = None,
        hint_level: int | None = None,
        safety_events: list[str] | None = None,
    ) -> ToolResult:
        evidence = evidence or []
        parameters = parameters or {}
        safety_events = safety_events or []
        output = ToolResult(
            tool_name=tool_name,
            status="success",
            evidence_unlocked=evidence,
            result=result,
            time_cost=time_cost,
            safety_events=safety_events,
            learner_message=learner_message,
            current_stage=state.current_stage,
        )
        self._append_trace(
            state=state,
            stage=stage_at_action,
            structured_action={"type": "tool_call", "status": "success"},
            tool_name=tool_name,
            tool_parameters=parameters,
            result_summary=output.model_dump(mode="json"),
            evidence_unlocked=evidence,
            time_cost=time_cost,
            hint_level=hint_level,
            safety_event=safety_events,
        )
        return output

    def _error(
        self,
        state: EncounterState,
        tool_name: str,
        message: str,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> ToolResult:
        state.actions_taken.append(tool_name)
        self.sessions.save(state)
        output = ToolResult(
            tool_name=tool_name,
            status="error",
            learner_message=message,
            current_stage=state.current_stage,
        )
        self._append_trace(
            state=state,
            stage=state.current_stage,
            structured_action={"type": "tool_call", "status": "error"},
            tool_name=tool_name,
            tool_parameters=parameters or {},
            result_summary=output.model_dump(mode="json"),
        )
        return output

    def _duplicate(
        self,
        state: EncounterState,
        tool_name: str,
        message: str,
        *,
        parameters: dict[str, Any],
        result: dict[str, Any],
    ) -> ToolResult:
        state.actions_taken.append(tool_name)
        self.sessions.save(state)
        output = ToolResult(
            tool_name=tool_name,
            status="duplicate",
            result=result,
            learner_message=message,
            current_stage=state.current_stage,
        )
        self._append_trace(
            state=state,
            stage=state.current_stage,
            structured_action={"type": "tool_call", "status": "duplicate"},
            tool_name=tool_name,
            tool_parameters=parameters,
            result_summary=output.model_dump(mode="json"),
        )
        return output

    def _trace_state_error(
        self,
        state: EncounterState,
        tool_name: str,
        stage: EncounterStage,
        message: str,
        *,
        natural_language_input: str | None = None,
    ) -> None:
        state.actions_taken.append(tool_name)
        self.sessions.save(state)
        self._append_trace(
            state=state,
            stage=stage,
            natural_language_input=natural_language_input,
            structured_action={"type": "tool_call", "status": "error"},
            tool_name=tool_name,
            result_summary={"status": "error", "learner_message": message},
        )

    def _append_trace(
        self,
        *,
        state: EncounterState,
        stage: EncounterStage,
        structured_action: dict[str, Any],
        result_summary: dict[str, Any],
        tool_name: str | None = None,
        natural_language_input: str | None = None,
        tool_parameters: dict[str, Any] | None = None,
        evidence_unlocked: list[UnlockedEvidence] | None = None,
        time_cost: int = 0,
        hint_level: int | None = None,
        safety_event: list[str] | None = None,
        score_event: dict[str, Any] | None = None,
    ) -> ActionTraceEntry:
        entry = ActionTraceEntry(
            action_id=str(uuid4()),
            session_id=state.session_id,
            stage=stage,
            natural_language_input=natural_language_input,
            structured_action=structured_action,
            tool_name=tool_name,
            tool_parameters=tool_parameters or {},
            result_summary=result_summary,
            evidence_unlocked=evidence_unlocked or [],
            time_cost=time_cost,
            hint_level=hint_level,
            safety_event=safety_event or [],
            score_event=score_event or {},
        )
        return self.trace.append(entry)

    @staticmethod
    def _evidence(
        *,
        evidence_id: str,
        category: str,
        label: str,
        value: Any,
        source_action: str,
    ) -> UnlockedEvidence:
        return UnlockedEvidence(
            evidence_id=evidence_id,
            category=category,
            label=label,
            value=value,
            unlocked_at=datetime.now(timezone.utc),
            source_action=source_action,
        )

    @staticmethod
    def _has_evidence_value(state: EncounterState, value: Any) -> bool:
        return any(item.value == value for item in state.evidence_unlocked)

    @staticmethod
    def _unlock_condition_met(condition: str, stage: EncounterStage) -> bool:
        normalized = condition.strip().lower()
        minimum_stage = {
            "available": EncounterStage.CASE_INTRO,
            "history_taking_or_later": EncounterStage.HISTORY_TAKING,
            "examination_or_later": EncounterStage.EXAMINATION,
            "investigation_or_later": EncounterStage.INVESTIGATION,
        }.get(normalized)
        if minimum_stage is None:
            return False
        return STAGE_ORDER[stage] >= STAGE_ORDER[minimum_stage]
