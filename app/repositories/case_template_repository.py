"""
Repository class for CaseTemplate operations.
"""

from __future__ import annotations

from sqlmodel import Session, select

from app.models.case_template import CaseTemplate


class CaseTemplateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: dict) -> CaseTemplate:
        case = CaseTemplate(**data)
        self.session.add(case)
        self.session.commit()
        self.session.refresh(case)
        return case

    def get_by_id(self, case_id: int) -> CaseTemplate | None:
        return self.session.get(CaseTemplate, case_id)

    def list_all(self, skip: int = 0, limit: int = 20) -> list[CaseTemplate]:
        statement = select(CaseTemplate).offset(skip).limit(limit)
        return self.session.exec(statement).all()

    def count_all(self) -> int:
        from sqlmodel import func
        statement = select(func.count(CaseTemplate.id))
        return self.session.exec(statement).one()
