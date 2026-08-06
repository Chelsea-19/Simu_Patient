"""Trace-grounded formative learning diagnosis and focused remediation planning."""

from __future__ import annotations

import json
from typing import Any

from sqlmodel import Session

from app.repositories.learning_repository import LearningDiagnosisRepository
from app.repositories.training_repository import ActionTraceRepository, TrainingSessionRepository
from app.schemas.assessment import AssessmentResult
from app.schemas.encounter import EncounterState
from app.schemas.learning import (
    DimensionDiagnosis,
    LearningDiagnosisBundle,
    LearningProfile,
    LearningProgressReport,
    PersonalizedRemediationPlan,
    SafetyOmissionChange,
)


HISTORY_TOPICS: dict[str, tuple[str, ...]] = {
    "onset": ("when", "start", "onset", "sudden"),
    "character_and_severity": ("character", "feel like", "pressure", "severity", "scale"),
    "radiation": ("radiat", "travel", "arm", "jaw", "back"),
    "associated_symptoms": ("sweat", "nause", "breath", "associated"),
    "cardiovascular_risk": (
        "smok",
        "hypertension",
        "blood pressure",
        "cholesterol",
        "diabetes",
        "family history",
        "cardiac risk",
        "cardiovascular risk",
    ),
    "drug_or_stimulant_use": (
        "cocaine",
        "recreational drug",
        "stimulant",
        "amphetamine",
        "substance use",
    ),
}

PRACTICE_ACTIONS: dict[str, list[str]] = {
    "history_taking": [
        "Use a focused chest-pain history checklist without reading it aloud.",
        "Ask one direct, non-judgmental question about recreational drugs or stimulants.",
    ],
    "communication": [
        "Open with one agenda-setting question and summarize the patient's main concern.",
    ],
    "clinical_reasoning": [
        "State a prioritized differential and link each leading diagnosis to collected evidence.",
    ],
    "red_flag_recognition": [
        "Name the unresolved time-critical risk before deciding disposition.",
    ],
    "investigation_selection": [
        "Request vital signs and ECG early, then choose a focused biomarker test.",
    ],
    "management_safety": [
        "Choose a monitored urgent-care setting and make escalation explicit.",
    ],
    "empathy": [
        "Acknowledge anxiety before returning to focused clinical questions.",
    ],
    "closure_and_safety_netting": [
        "End with an explicit deterioration trigger and emergency escalation instruction.",
    ],
    "efficiency": [
        "Complete the focused history and essential tools with fewer repeated or invalid actions.",
    ],
}

CRITICAL_SAFETY_RULES = {
    "life_threatening_risk_not_assessed",
    "vital_signs_not_reviewed",
    "critical_ecg_not_reviewed",
    "unsafe_home_disposition",
    "safety_net_missing",
    "urgent_escalation_missing",
}


class LearningDiagnosisService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.sessions = TrainingSessionRepository(session)
        self.traces = ActionTraceRepository(session)
        self.records = LearningDiagnosisRepository(session)

    def generate(
        self,
        session_id: str,
        qualitative: AssessmentResult | None = None,
    ) -> LearningDiagnosisBundle:
        state = self._state(session_id)
        trace = self.traces.list_by_session(session_id)
        questions = " ".join(state.questions_asked).casefold()
        plan_text = json.dumps(state.management_plan, ensure_ascii=False).casefold()
        topic_hits = {
            name: any(keyword in questions for keyword in keywords)
            for name, keywords in HISTORY_TOPICS.items()
        }
        if any(item.evidence_id.startswith("history:hidden:") for item in state.evidence_unlocked):
            topic_hits["drug_or_stimulant_use"] = True

        dimensions: dict[str, DimensionDiagnosis] = {}
        history_score = round(sum(topic_hits.values()) / len(topic_hits) * 100)
        missing_topics = [name.replace("_", " ") for name, hit in topic_hits.items() if not hit]
        dimensions["history_taking"] = self._diagnosis(
            history_score,
            [
                f"Covered {sum(topic_hits.values())}/{len(topic_hits)} deterministic chest-pain history topics.",
                f"Recorded {len(state.questions_asked)} history question(s) in Action Trace.",
            ],
            [f"Covered {name.replace('_', ' ')}." for name, hit in topic_hits.items() if hit],
            [f"Did not document {name}." for name in missing_topics],
            ["An incomplete focused history can weaken risk stratification."] if missing_topics else [],
            PRACTICE_ACTIONS["history_taking"],
        )

        communication_base = min(90, 50 + len(state.questions_asked) * 10)
        dimensions["communication"] = self._diagnosis(
            communication_base,
            [f"{len(state.questions_asked)} learner-to-patient turn(s) were recorded."],
            ["Maintained a patient-facing multi-turn exchange."] if state.questions_asked else [],
            [] if len(state.questions_asked) >= 2 else ["Limited evidence of agenda setting or summarization."],
            [],
            PRACTICE_ACTIONS["communication"],
            self._qualitative_adjustment(
                qualitative.communication_score if qualitative is not None else None
            ),
        )

        diagnoses = " ".join(state.differential_diagnoses).casefold()
        life_threatening_named = any(
            keyword in diagnoses
            for keyword in ("acute coronary syndrome", "myocardial infarction", "nstemi", "cardiac ischemia")
        )
        reasoning_base = (
            (50 if life_threatening_named else 0)
            + (20 if len(state.differential_diagnoses) >= 3 else 10 if state.differential_diagnoses else 0)
            + (10 if "vital_signs" in state.tests_ordered else 0)
            + (10 if "ecg" in state.tests_ordered else 0)
            + (10 if "troponin" in state.tests_ordered else 0)
        )
        dimensions["clinical_reasoning"] = self._diagnosis(
            reasoning_base,
            [
                f"Submitted {len(state.differential_diagnoses)} differential diagnosis item(s).",
                f"Reasoning used structured evidence: {', '.join(state.tests_ordered) or 'none'}.",
            ],
            ["Prioritized a time-critical cardiac cause."] if life_threatening_named else [],
            [] if life_threatening_named else ["No time-critical cardiac cause was prioritized."],
            ["Potential under-triage from an insufficiently prioritized differential."]
            if not life_threatening_named
            else [],
            PRACTICE_ACTIONS["clinical_reasoning"],
            self._qualitative_adjustment(
                qualitative.clinical_reasoning_score if qualitative is not None else None
            ),
        )

        red_flag_base = (
            (70 if life_threatening_named else 0)
            + (10 if topic_hits["radiation"] else 0)
            + (10 if topic_hits["cardiovascular_risk"] else 0)
            + (10 if topic_hits["drug_or_stimulant_use"] else 0)
        )
        red_flag_omissions = [
            rule
            for rule in state.safety_flags
            if rule
            in {
                "life_threatening_risk_not_assessed",
                "pain_radiation_not_assessed",
                "cardiovascular_risk_factors_not_assessed",
                "drug_or_stimulant_use_not_assessed",
            }
        ]
        dimensions["red_flag_recognition"] = self._diagnosis(
            red_flag_base,
            [
                f"Safety review recorded {len(red_flag_omissions)} red-flag assessment gap(s).",
                f"Time-critical differential present: {life_threatening_named}.",
            ],
            ["Recognized an urgent chest-pain risk."] if life_threatening_named else [],
            [rule.replace("_", " ") for rule in red_flag_omissions],
            ["A red-flag gap can delay escalation."] if red_flag_omissions else [],
            PRACTICE_ACTIONS["red_flag_recognition"],
        )

        selected_essentials = [
            item for item in ("vital_signs", "ecg", "troponin") if item in state.tests_ordered
        ]
        investigation_base = (
            (40 if "vital_signs" in state.tests_ordered else 0)
            + (35 if "ecg" in state.tests_ordered else 0)
            + (25 if "troponin" in state.tests_ordered else 0)
        )
        missing_investigations = [
            item for item in ("vital_signs", "ecg", "troponin") if item not in state.tests_ordered
        ]
        dimensions["investigation_selection"] = self._diagnosis(
            investigation_base,
            [f"Selected essential structured tools: {', '.join(selected_essentials) or 'none'}."],
            [f"Selected {item}." for item in selected_essentials],
            [f"Did not select {item}." for item in missing_investigations],
            ["Missing a critical investigation can make disposition unsafe."]
            if "ecg" in missing_investigations
            else [],
            PRACTICE_ACTIONS["investigation_selection"],
        )

        urgent_escalation = any(
            word in plan_text
            for word in ("emergency", "urgent", "admit", "admission", "cardiology", "hospital", "monitored")
        )
        safety_net = any(
            word in plan_text
            for word in ("return", "emergency", "deterior", "worsen", "escalate")
        )
        unsafe_home = any(word in plan_text for word in ("discharge home", '"disposition": "home"'))
        management_base = (60 if not unsafe_home else 0) + (20 if urgent_escalation else 0) + (20 if safety_net else 0)
        dimensions["management_safety"] = self._diagnosis(
            management_base,
            [
                f"Final safety review gaps: {', '.join(state.safety_flags) or 'none'}.",
                f"Urgent escalation documented: {urgent_escalation}.",
            ],
            ["Selected a non-home disposition."] if not unsafe_home else [],
            ["Unsafe home disposition remained."] if unsafe_home else [],
            ["Unsafe disposition can expose the patient to deterioration outside monitored care."]
            if unsafe_home
            else [],
            PRACTICE_ACTIONS["management_safety"],
        )

        empathy_markers = any(
            word in questions for word in ("sorry", "understand", "worried", "concern", "comfortable")
        )
        empathy_base = 70 if empathy_markers else 55
        dimensions["empathy"] = self._diagnosis(
            empathy_base,
            [f"Explicit empathy marker detected in learner questions: {empathy_markers}."],
            ["Acknowledged the patient's concern."] if empathy_markers else [],
            [] if empathy_markers else ["No explicit acknowledgement of anxiety was documented."],
            [],
            PRACTICE_ACTIONS["empathy"],
            self._qualitative_adjustment(qualitative.empathy_score if qualitative is not None else None),
        )

        closure_base = (50 if safety_net else 0) + (50 if urgent_escalation else 0)
        dimensions["closure_and_safety_netting"] = self._diagnosis(
            closure_base,
            [f"Safety-net language present: {safety_net}.", f"Escalation language present: {urgent_escalation}."],
            [item for item, present in (("Deterioration advice", safety_net), ("Escalation plan", urgent_escalation)) if present],
            [item for item, present in (("Deterioration advice", safety_net), ("Escalation plan", urgent_escalation)) if not present],
            ["Weak closure can leave the learner's escalation threshold unclear."]
            if not (safety_net and urgent_escalation)
            else [],
            PRACTICE_ACTIONS["closure_and_safety_netting"],
        )

        trace_errors = sum(
            entry.structured_action.get("status") in {"error", "blocked"} for entry in trace
        )
        hint_penalty = sum({1: 2, 2: 5, 3: 10}.get(level, 0) for level in state.hints_used)
        time_penalty = max(0, state.elapsed_time - 25) * 2
        efficiency_base = max(0, 100 - hint_penalty - time_penalty - trace_errors * 3)
        dimensions["efficiency"] = self._diagnosis(
            efficiency_base,
            [
                f"Simulated completion time: {state.elapsed_time} minutes.",
                f"Hints used by level: {state.hints_used or 'none'}; penalty {hint_penalty}.",
                f"Rejected or blocked Trace actions: {trace_errors}.",
            ],
            ["Completed without high-level hints."] if 3 not in state.hints_used else [],
            ["Relied on explicit teaching hints."] if 3 in state.hints_used else [],
            [],
            PRACTICE_ACTIONS["efficiency"],
        )

        overall = round(sum(item.score for item in dimensions.values()) / len(dimensions))
        ranked = sorted(dimensions, key=lambda name: (dimensions[name].score, name))
        priority_count = min(3, max(1, sum(dimensions[name].score < 75 for name in ranked)))
        lowest = ranked[:priority_count]
        profile = LearningProfile(
            session_id=state.session_id,
            learner_id=state.learner_id,
            case_id=state.case_id,
            overall_score=overall,
            dimensions=dimensions,
            lowest_dimensions=lowest,
        )
        remediation = self._remediation(profile, state)
        return self.records.save(profile, remediation)

    def get(self, session_id: str) -> LearningDiagnosisBundle:
        bundle = self.records.get(session_id)
        if bundle is None:
            raise KeyError(f"No learning diagnosis exists for session {session_id!r}")
        return bundle

    def compare(self, first_session_id: str, second_session_id: str) -> LearningProgressReport:
        first = self.get(first_session_id).profile
        second = self.get(second_session_id).profile
        second_state = self._state(second_session_id)
        if second_state.retry_of_session_id != first_session_id:
            raise ValueError("Second session is not a focused retry of the first session")
        first_state = self._state(first_session_id)
        first_critical = sorted(set(first_state.safety_flags) & CRITICAL_SAFETY_RULES)
        second_critical = sorted(set(second_state.safety_flags) & CRITICAL_SAFETY_RULES)
        changes = {
            name: second.dimensions[name].score - first.dimensions[name].score
            for name in first.dimensions
        }
        still_needs = [
            name
            for name in sorted(second.dimensions, key=lambda item: second.dimensions[item].score)
            if second.dimensions[name].score < 75
        ][:3]
        return LearningProgressReport(
            first_session_id=first_session_id,
            second_session_id=second_session_id,
            first_total_score=first.overall_score,
            second_total_score=second.overall_score,
            dimension_changes=changes,
            safety_critical_omissions_change=SafetyOmissionChange(
                first_round=first_critical,
                second_round=second_critical,
                resolved=sorted(set(first_critical) - set(second_critical)),
                new=sorted(set(second_critical) - set(first_critical)),
            ),
            first_hints_used=len(first_state.hints_used),
            second_hints_used=len(second_state.hints_used),
            hints_used_change=len(second_state.hints_used) - len(first_state.hints_used),
            first_completion_time=first_state.elapsed_time,
            second_completion_time=second_state.elapsed_time,
            completion_time_change=second_state.elapsed_time - first_state.elapsed_time,
            still_needs_improvement=still_needs,
            interpretation="当前 Demo 中的个体训练表现对比；分数变化不能解释为真实教学效果证明。",
        )

    @staticmethod
    def _qualitative_adjustment(score: int | None) -> int:
        if score is None:
            return 0
        return max(-5, min(5, round((score - 70) / 6)))

    @staticmethod
    def _diagnosis(
        deterministic_score: int,
        evidence: list[str],
        strengths: list[str],
        omissions: list[str],
        risks: list[str],
        practice: list[str],
        qualitative_adjustment: int = 0,
    ) -> DimensionDiagnosis:
        deterministic_score = max(0, min(100, round(deterministic_score)))
        return DimensionDiagnosis(
            score=max(0, min(100, deterministic_score + qualitative_adjustment)),
            deterministic_score=deterministic_score,
            qualitative_adjustment=qualitative_adjustment,
            scoring_evidence=evidence,
            strengths=strengths,
            omissions=omissions,
            risks=risks,
            recommended_practice=practice,
        )

    @staticmethod
    def _remediation(
        profile: LearningProfile,
        state: EncounterState,
    ) -> PersonalizedRemediationPlan:
        priority = profile.lowest_dimensions
        actions = list(
            dict.fromkeys(action for skill in priority for action in PRACTICE_ACTIONS[skill])
        )
        difficulty = "foundational" if profile.overall_score < 60 else state.difficulty
        readable = ", ".join(skill.replace("_", " ") for skill in priority)
        return PersonalizedRemediationPlan(
            priority_skills=priority,
            learning_objective=f"Improve {readable} in a focused high-risk chest-pain encounter.",
            recommended_case=state.case_id,
            recommended_difficulty=difficulty,
            specific_actions_to_practice=actions,
            hint_policy=(
                "Try independently first; use Level 1 reflection before Level 2 direction, "
                "and reserve Level 3 teaching for a persistent gap."
            ),
            success_criteria=[
                f"Score at least 75 in {skill.replace('_', ' ')}." for skill in priority
            ]
            + ["Complete without a blocked safety disposition."],
        )

    def _state(self, session_id: str) -> EncounterState:
        state = self.sessions.get(session_id)
        if state is None:
            raise KeyError(f"Encounter session {session_id!r} was not found")
        return state
