"""Deterministic stage transitions for clinical training encounters."""

from __future__ import annotations

from app.schemas.encounter import EncounterStage, EncounterState


FORWARD_TRANSITIONS: dict[EncounterStage, set[EncounterStage]] = {
    EncounterStage.CASE_INTRO: {EncounterStage.HISTORY_TAKING},
    EncounterStage.HISTORY_TAKING: {EncounterStage.EXAMINATION},
    EncounterStage.EXAMINATION: {EncounterStage.INVESTIGATION},
    EncounterStage.INVESTIGATION: {EncounterStage.CLINICAL_REASONING},
    EncounterStage.CLINICAL_REASONING: {EncounterStage.MANAGEMENT},
    EncounterStage.MANAGEMENT: {EncounterStage.SAFETY_REVIEW},
    EncounterStage.SAFETY_REVIEW: {EncounterStage.ASSESSMENT},
    EncounterStage.ASSESSMENT: {EncounterStage.REMEDIATION, EncounterStage.COMPLETED},
    EncounterStage.REMEDIATION: {EncounterStage.COMPLETED},
    EncounterStage.COMPLETED: set(),
}

PREVIOUS_STAGE: dict[EncounterStage, EncounterStage] = {
    EncounterStage.HISTORY_TAKING: EncounterStage.CASE_INTRO,
    EncounterStage.EXAMINATION: EncounterStage.HISTORY_TAKING,
    EncounterStage.INVESTIGATION: EncounterStage.EXAMINATION,
    EncounterStage.CLINICAL_REASONING: EncounterStage.INVESTIGATION,
    EncounterStage.MANAGEMENT: EncounterStage.CLINICAL_REASONING,
    EncounterStage.SAFETY_REVIEW: EncounterStage.MANAGEMENT,
    EncounterStage.ASSESSMENT: EncounterStage.SAFETY_REVIEW,
    EncounterStage.REMEDIATION: EncounterStage.ASSESSMENT,
    EncounterStage.COMPLETED: EncounterStage.REMEDIATION,
}


class EncounterStateMachine:
    """Apply explicit forward transitions and a one-stage learner revision."""

    @staticmethod
    def can_transition(current: EncounterStage, target: EncounterStage) -> bool:
        if current == target:
            return True
        if target in FORWARD_TRANSITIONS[current]:
            return True
        return PREVIOUS_STAGE.get(current) == target

    @classmethod
    def transition(cls, state: EncounterState, target: EncounterStage) -> EncounterState:
        if not cls.can_transition(state.current_stage, target):
            raise ValueError(
                f"Cannot transition from {state.current_stage.value} to {target.value}"
            )
        state.current_stage = target
        return state
