"""
Repository for Rubric.
"""

from __future__ import annotations
from sqlmodel import Session, select
from app.models.rubric import Rubric

class RubricRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: dict) -> Rubric:
        rubric = Rubric(**data)
        self.session.add(rubric)
        self.session.commit()
        self.session.refresh(rubric)
        return rubric

    def get_by_id(self, rubric_id: int) -> Rubric | None:
        return self.session.get(Rubric, rubric_id)

    def get_default(self) -> Rubric:
        """Fetch the first rubric or create a default 'Standard OSCE' rubric."""
        statement = select(Rubric).limit(1)
        rubric = self.session.exec(statement).first()
        if not rubric:
            return self.create({"name": "Standard OSCE", "version": "1.0"})
        return rubric
