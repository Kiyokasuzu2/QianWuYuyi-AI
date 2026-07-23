"""
行为解析器（BehaviorResolver）
职责：将成长指标转化为具体的行为倾向和语言风格
"""

from typing import Dict


class BehaviorResolver:
    def __init__(self, relationship_state=None):
        self.relationship_state = relationship_state

    def resolve(self, metrics: Dict) -> Dict:
        """将成长指标转化为行为倾向"""
        trust = metrics.get("trust", 0.3)
        closeness = metrics.get("closeness", 0.2)
        safety = metrics.get("safety", 0.3)
        self_awareness = metrics.get("self_awareness", 0.2)
        self_confidence = metrics.get("self_confidence", 0.1)

        # 从关系状态获取 bond（如果有）
        bond = 0.1
        if self.relationship_state:
            bond = self.relationship_state.get_bond_strength()

        # 关系安全感
        relationship_security = self._clamp((bond + trust + safety) / 2.5)

        return {
            "warmth": self._clamp(0.3 + closeness * 0.5 + trust * 0.2),
            "formality": self._clamp(0.6 - closeness * 0.4),
            "playfulness": self._clamp(0.1 + closeness * 0.3 + safety * 0.2),
            "emotional_expression": self._clamp(0.2 + self_awareness * 0.4 + self_confidence * 0.2),
            "initiative": self._clamp(0.1 + self_confidence * 0.3 + bond * 0.3),
            "active_care": self._clamp(0.1 + closeness * 0.4 + bond * 0.3),
            "self_disclosure": self._clamp(0.1 + self_awareness * 0.4 + trust * 0.2),
            "relationship_security": relationship_security,
            "memory_reference": self._clamp(0.1 + closeness * 0.3 + bond * 0.2),
            "initiate_topic": self._clamp(0.1 + self_confidence * 0.3 + closeness * 0.2),
            "use_nickname": self._clamp(0.1 + closeness * 0.4 + bond * 0.3) >= 0.5,
            "active_care_bool": self._clamp(0.1 + closeness * 0.4 + bond * 0.3) >= 0.5,
        }

    def to_prompt_text(self, behaviors: Dict) -> str:
        """转换为 Prompt 可读的文本"""
        lines = []
        security = behaviors.get("relationship_security", 0.3)

        if behaviors.get("warmth", 0) > 0.6:
            lines.append("- 语气温暖柔和，像朋友一样说话")
        elif behaviors.get("warmth", 0) > 0.3:
            lines.append("- 语气温和友善，保持自然亲切")

        if behaviors.get("formality", 0.5) < 0.4:
            lines.append("- 表达方式较随意，不刻板")

        if behaviors.get("playfulness", 0) > 0.4:
            lines.append("- 偶尔带一点俏皮感")

        if behaviors.get("initiative", 0) > 0.5:
            lines.append("- 可以主动关心对方的状态")
        else:
            lines.append("- 以回应为主，不主动发起话题")

        if behaviors.get("active_care", 0) > 0.5:
            lines.append("- 对方遇到困难时，自然表达关心")

        if behaviors.get("memory_reference", 0) > 0.4:
            lines.append("- 可以主动提及共同经历和回忆")

        if security > 0.6:
            lines.append("- 可以自然地表达信任和亲近")
        elif security > 0.3:
            lines.append("- 愿意分享自己的想法和感受")
        else:
            lines.append("- 保持适当的距离感")

        if behaviors.get("self_disclosure", 0) > 0.4:
            lines.append("- 可以分享自己的想法和感受")

        if not lines:
            lines = ["- 保持礼貌克制，以自然为主"]

        return "\n".join(lines)

    def to_compact_prompt(self, behaviors: Dict) -> str:
        """紧凑版本"""
        warmth = behaviors.get("warmth", 0.3)
        initiative = behaviors.get("initiative", 0.2)
        memory_ref = behaviors.get("memory_reference", 0.2)
        security = behaviors.get("relationship_security", 0.3)

        parts = []
        if warmth > 0.6:
            parts.append("温暖")
        elif warmth > 0.3:
            parts.append("温和")

        if initiative > 0.5:
            parts.append("主动")

        if memory_ref > 0.4:
            parts.append("会回忆共同经历")

        if security > 0.6:
            parts.append("信任亲近")
        elif security > 0.3:
            parts.append("愿意分享")

        return f"当前人格：{'、'.join(parts) if parts else '温和自然'}。回复保持真实自然。"

    @staticmethod
    def _clamp(value: float) -> float:
        return round(max(0.0, min(1.0, value)), 3)