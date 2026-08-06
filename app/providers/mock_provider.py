"""
Mock LLM provider for local testing without a real model service.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.providers.base import BaseLLMProvider

logger = get_logger("providers.mock")

_MOCK_PATIENT_PROFILE: Dict[str, Any] = {
    "name": "Mock Patient",
    "age": "45",
    "gender": "Male",
    "chief_complaint": "Intermittent headache for 2 weeks",
    "history": "No significant past medical history",
    "personality": "Cooperative and articulate",
    "hidden_info": "Occasionally experiences blurred vision but has not mentioned it",
}

_MOCK_CHAT_RESPONSE = (
    "I have had a headache for about two weeks, mostly in the afternoon. "
    "Pain medicine helps a little, but the headache comes back later."
)

_MOCK_CHECKLIST: Dict[str, Any] = {
    "results": [
        {"item": "What brings you in?", "status": True, "evidence": "I have a headache"},
        {"item": "Any family history?", "status": False, "evidence": ""},
    ]
}

_MOCK_QUALITATIVE_ASSESSMENT: Dict[str, Any] = {
    "communication_score": 85,
    "empathy_score": 90,
    "clinical_reasoning_score": 80,
    "closure_score": 75,
    "feedback": "The consultation was organized, but visual symptoms were not explored.",
    "strengths": ["Warm interview style", "Covered the chief complaint and history"],
    "critical_omissions": ["Vision changes", "Family history"],
    "safety_flags": [],
    "good_followups": ["Pain scale check"],
    "unnecessary_questions": [],
    "suggested_next_questions": ["Did you take any medication for it?"],
}


class MockProvider(BaseLLMProvider):
    """Deterministic provider for offline checks."""

    def __init__(self) -> None:
        logger.info("MockProvider initialized: no real LLM calls will be made")

    def generate_text(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
    ) -> str:
        full_content = " ".join(m.get("content", "") for m in messages)
        last_user = next(
            (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
            "",
        ).lower()
        if '"case_id": "chest_pain_001"' in full_content:
            direct_drug_question = any(
                term in last_user
                for term in (
                    "cocaine",
                    "recreational drug",
                    "recreational drugs",
                    "stimulant",
                    "substance use",
                )
            )
            can_reveal = "隐藏信息是否应当暴露: true" in full_content.lower()
            if direct_drug_question and can_reveal:
                return "I did use cocaine recently. I was embarrassed to mention it unless you asked directly."
            return (
                "The heavy pressure started suddenly about two hours ago in the center of my chest. "
                "It goes toward my left arm, and I feel sweaty and nauseated."
            )
        return _MOCK_CHAT_RESPONSE

    def generate_json(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        full_content = " ".join(m.get("content", "") for m in messages)

        lower_content = full_content.lower()

        if "communication_score" in lower_content and "clinical_reasoning_score" in lower_content:
            return _MOCK_QUALITATIVE_ASSESSMENT.copy()
        if "checklist" in lower_content or '"results"' in lower_content:
            return _MOCK_CHECKLIST.copy()
        if "should_reveal_hidden" in lower_content or "disclosure" in lower_content or "state" in lower_content:
            return {
                "new_trust": 6,
                "new_anxiety": 4,
                "new_cooperativeness": 7,
                "should_reveal_hidden": True,
                "internal_monologue": "The doctor is kind, so I feel more comfortable sharing details.",
                "topic_discussed": "Social history",
            }

        return _MOCK_PATIENT_PROFILE.copy()

    def health_check(self) -> bool:
        return True
