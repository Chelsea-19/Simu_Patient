"""Persistence for learning profiles and personalized remediation plans."""

from __future__ import annotations

from sqlmodel import Session, select

from app.models.learning import LearningDiagnosisRecord
from app.schemas.learning import LearningDiagnosisBundle, LearningProfile, PersonalizedRemediationPlan


class LearningDiagnosisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(
        self,
        profile: LearningProfile,
        remediation_plan: PersonalizedRemediationPlan,
    ) -> LearningDiagnosisBundle:
        record = self.session.get(LearningDiagnosisRecord, profile.session_id)
        if record is None:
            record = LearningDiagnosisRecord(
                session_id=profile.session_id,
                learner_id=profile.learner_id,
                case_id=profile.case_id,
                overall_score=profile.overall_score,
                profile_json=profile.model_dump_json(),
                remediation_json=remediation_plan.model_dump_json(),
                generated_at=profile.generated_at,
            )
        else:
            record.overall_score = profile.overall_score
            record.profile_json = profile.model_dump_json()
            record.remediation_json = remediation_plan.model_dump_json()
            record.generated_at = profile.generated_at
        self.session.add(record)
        self.session.commit()
        return LearningDiagnosisBundle(profile=profile, remediation_plan=remediation_plan)

    def get(self, session_id: str) -> LearningDiagnosisBundle | None:
        record = self.session.get(LearningDiagnosisRecord, session_id)
        if record is None:
            return None
        return LearningDiagnosisBundle(
            profile=LearningProfile.model_validate_json(record.profile_json),
            remediation_plan=PersonalizedRemediationPlan.model_validate_json(
                record.remediation_json
            ),
        )

    def list_by_learner(self, learner_id: str) -> list[LearningDiagnosisBundle]:
        statement = (
            select(LearningDiagnosisRecord)
            .where(LearningDiagnosisRecord.learner_id == learner_id)
            .order_by(LearningDiagnosisRecord.generated_at)
        )
        return [
            LearningDiagnosisBundle(
                profile=LearningProfile.model_validate_json(record.profile_json),
                remediation_plan=PersonalizedRemediationPlan.model_validate_json(
                    record.remediation_json
                ),
            )
            for record in self.session.exec(statement).all()
        ]
