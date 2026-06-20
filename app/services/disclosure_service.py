"""
Disclosure Controller and Patient State logic.
"""

import json
from typing import Dict, Any

from app.core.logging import get_logger
from app.providers.base import BaseLLMProvider
from app.models.session_state import SessionState

logger = get_logger("services.disclosure_service")

STATE_UPDATE_PROMPT = """
你是一个内部的【状态更新与披露控制引擎】。
你的任务是根据医生当前的提问（User Input）和病人的当前状态（Current State），来客观更新病人的情绪，并判断病人是否应该透露特定信息。

【病人初始设定】:
{profile_json}

【当前病人内部状态】:
Trust Level (1-10): {trust}
Anxiety Level (1-10): {anxiety}
Cooperativeness (1-10): {cooperativeness}
已透露话题: {revealed_topics}
是否已透露隐藏信息: {hidden_info_revealed}

【医生的最新提问】:
{user_input}

【任务要求】:
1. 更新 trust, anxiety, 和 cooperativeness。如果医生展现了极强的共情，trust 上升，anxiety 下降；反之如果有指责或过度逼问，trust 下降，anxiety 飙升。
2. 判断医生目前是否触及了病人的【隐藏信息】（Hidden Info）。如果医生问得非常直接且相关，且 Trust > 4，则 should_reveal_hidden = true。如果已经 revealed，则保持 true。
3. 返回 JSON 格式，必须包含以下字段：
{{
    "new_trust": int (1-10),
    "new_anxiety": int (1-10),
    "new_cooperativeness": int (1-10),
    "should_reveal_hidden": bool,
    "internal_monologue": "病人现在心里的真实想法（比如：医生好像很懂我，我决定告诉他那个秘密... 或：他太随便了，我不想搭理他）",
    "topic_discussed": "当前这句话属于什么医疗话题，如：现病史、既往史、家族史、个人史等"
}}
"""

class DisclosureService:
    def __init__(self, provider: BaseLLMProvider):
        self._provider = provider

    def analyze_next_state(
        self,
        profile_json: str,
        current_state: SessionState,
        user_input: str,
    ) -> Dict[str, Any]:
        """
        Uses an LLM call to perform State Tracking & Disclosure Decision.
        """
        prompt = STATE_UPDATE_PROMPT.format(
            profile_json=profile_json,
            trust=current_state.trust_level,
            anxiety=current_state.anxiety_level,
            cooperativeness=current_state.cooperativeness,
            revealed_topics=current_state.revealed_topics_json,
            hidden_info_revealed=str(current_state.hidden_info_revealed).lower(),
            user_input=user_input
        )
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            logger.info("Evaluating state transition & disclosure...")
            result = self._provider.generate_json(messages)
            return result
        except Exception as e:
            logger.error("State eval failed: %s", e)
            # Safe fallback: State remains constant, nothing new is revealed.
            return {
                "new_trust": current_state.trust_level,
                "new_anxiety": current_state.anxiety_level,
                "new_cooperativeness": current_state.cooperativeness,
                "should_reveal_hidden": current_state.hidden_info_revealed,
                "internal_monologue": "Fallback: evaluation failed.",
                "topic_discussed": "Unknown"
            }
