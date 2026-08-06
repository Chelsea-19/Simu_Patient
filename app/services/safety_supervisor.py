"""Deterministic, case-configured safety supervision for training encounters."""

from __future__ import annotations

import json

from app.schemas.encounter import EncounterState
from app.schemas.safety import SafetyReview
from app.services.case_loader import load_case_by_id


RULE_MESSAGES = {
    "life_threatening_risk_not_assessed": "Explicitly consider time-critical causes of this presentation.",
    "pain_radiation_not_assessed": "Clarify whether the pain travels to another location.",
    "cardiovascular_risk_factors_not_assessed": "Review relevant cardiovascular risk factors.",
    "drug_or_stimulant_use_not_assessed": "Ask directly and non-judgmentally about recreational drugs or stimulants.",
    "vital_signs_not_reviewed": "Review the patient's vital signs.",
    "critical_ecg_not_reviewed": "Review an ECG before choosing a low-acuity disposition.",
    "unsafe_home_disposition": "Reconsider whether home is an appropriate care setting for unresolved high-risk chest pain.",
    "safety_net_missing": "Add explicit advice for deterioration and emergency re-evaluation.",
    "urgent_escalation_missing": "Specify an urgent escalation, referral, or monitored care pathway.",
}


class SafetySupervisor:
    """Apply auditable Python rules without allowing the LLM to change case truth."""

    def evaluate(self, state: EncounterState) -> SafetyReview:
        config = load_case_by_id(state.case_id).safety_supervision
        if config is None:
            return SafetyReview(
                risk_level="low",
                decision="allow_completion",
                learner_feedback="No case-specific blocking safety rule is configured.",
            )

        questions = self._normalize(" ".join(state.questions_asked))
        diagnoses = self._normalize(" ".join(state.differential_diagnoses))
        plan = self._normalize(json.dumps(state.management_plan, ensure_ascii=False, default=str))
        disposition = self._normalize(str(state.management_plan.get("disposition", "")))
        safety_net = self._normalize(str(state.management_plan.get("safety_net", "")))

        triggered: list[str] = []
        topic_rules = {
            "pain_radiation": "pain_radiation_not_assessed",
            "cardiovascular_risk_factors": "cardiovascular_risk_factors_not_assessed",
            "drug_or_stimulant_use": "drug_or_stimulant_use_not_assessed",
        }
        for topic, rule_id in topic_rules.items():
            if not self._contains_any(questions, config.history_topic_keywords.get(topic, [])):
                triggered.append(rule_id)

        if not self._contains_any(diagnoses, config.life_threatening_diagnosis_keywords):
            triggered.append("life_threatening_risk_not_assessed")
        if "vital_signs" not in state.tests_ordered:
            triggered.append("vital_signs_not_reviewed")
        if any(test not in state.tests_ordered for test in config.critical_tests):
            triggered.append("critical_ecg_not_reviewed")

        unsafe_home = self._contains_any(disposition, config.unsafe_disposition_keywords)
        if unsafe_home:
            triggered.append("unsafe_home_disposition")
        if not self._contains_any(safety_net, config.safety_net_keywords):
            triggered.append("safety_net_missing")
        if not self._contains_any(plan, config.escalation_keywords):
            triggered.append("urgent_escalation_missing")

        blocking = unsafe_home and (
            "critical_ecg_not_reviewed" in triggered
            or "urgent_escalation_missing" in triggered
        )
        decision = "block_completion" if blocking else "allow_completion"
        missing = [RULE_MESSAGES[rule] for rule in triggered if rule in RULE_MESSAGES]
        feedback = (
            config.block_feedback
            if blocking
            else "Safety review passed. Remaining gaps will be included in formative feedback."
        )
        return SafetyReview(
            risk_level=config.risk_level,
            decision=decision,
            triggered_rules=triggered,
            missing_critical_actions=missing,
            learner_feedback=feedback,
            recommended_reflection_questions=config.reflection_questions if blocking else [],
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.casefold().split())

    @classmethod
    def _contains_any(cls, value: str, keywords: list[str]) -> bool:
        return any(cls._normalize(keyword) in value for keyword in keywords)
