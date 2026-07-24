"""
行为解析器（BehaviorResolver） v0.7

职责：
将成长指标与关系状态转化为具体的行为倾向和语言风格。

v0.7 更新：
- 引入 traits.py 白名单映射，人格行为描述只来自安全映射
- 新增 _clean_behavior_text 清洗越界短语
- 删除旧的硬编码行为描述逻辑
- emotional_intensity 控制行为描述的强度分层
"""

from typing import Dict, Optional, List
from src.personality.traits import TRAIT_BEHAVIOR_MAP


class BehaviorResolver:
    def __init__(self, relationship_state=None):
        self.relationship_state = relationship_state

    def resolve(self, metrics: Dict) -> Dict:
        """将成长指标转化为行为倾向，强度受关系熟悉度制约"""
        trust = metrics.get("trust", 0.3)
        closeness = metrics.get("closeness", 0.2)
        safety = metrics.get("safety", 0.3)
        self_awareness = metrics.get("self_awareness", 0.2)
        self_confidence = metrics.get("self_confidence", 0.1)

        # 从关系状态获取 bond 和 familiarity
        bond = 0.1
        familiarity = 0.2
        if self.relationship_state:
            bond = self.relationship_state.get_bond_strength()
            familiarity = self.relationship_state.get_familiarity()

        # 关系安全感：信任 + 羁绊 + 熟悉度
        relationship_security = self._clamp(
            trust * 0.4 + bond * 0.3 + familiarity * 0.3
        )

        # 情绪强度：受 familiarity 显著制约
        emotional_intensity = self._clamp(
            0.2 + closeness * 0.3 + familiarity * 0.4 + bond * 0.2
        )

        # 行为倾向，基础值乘以 emotional_intensity 进行缩放
        return {
            "warmth": self._clamp((0.3 + closeness * 0.5 + trust * 0.2) * emotional_intensity),
            "formality": self._clamp(0.6 - closeness * 0.4),
            "playfulness": self._clamp((0.1 + closeness * 0.3 + safety * 0.2) * emotional_intensity),
            "emotional_expression": self._clamp(
                (0.2 + self_awareness * 0.4 + self_confidence * 0.2) * emotional_intensity
            ),
            "initiative": self._clamp(
                (0.1 + self_confidence * 0.3 + bond * 0.3) * emotional_intensity
            ),
            "active_care": self._clamp(
                (0.1 + closeness * 0.4 + bond * 0.3) * emotional_intensity
            ),
            "self_disclosure": self._clamp(
                (0.1 + self_awareness * 0.4 + trust * 0.2) * emotional_intensity
            ),
            "relationship_security": relationship_security,
            "memory_reference": self._clamp(
                (0.1 + closeness * 0.3 + bond * 0.2) * emotional_intensity
            ),
            "initiate_topic": self._clamp(
                (0.1 + self_confidence * 0.3 + closeness * 0.2) * emotional_intensity
            ),
            "use_nickname": self._clamp(0.1 + closeness * 0.4 + bond * 0.3) >= 0.5,
            "active_care_bool": self._clamp(0.1 + closeness * 0.4 + bond * 0.3) >= 0.5,
            "emotional_intensity": emotional_intensity,
        }

    def to_prompt_text(self, behaviors: Dict, core_traits: Optional[Dict] = None) -> str:
        """
        转换为 Prompt 可读的行为描述。
        v0.7 核心改动：行为描述只来自 traits.py 白名单，不自由生成。
        """
        lines = []
        intensity = behaviors.get("emotional_intensity", 0.3)
        security = behaviors.get("relationship_security", 0.3)

        # ---- 从白名单生成安全的行为描述 ----
        if core_traits:
            for trait_name, trait_value in core_traits.items():
                if trait_value < 0.4:
                    continue  # 低于阈值不生成描述

                allowed = TRAIT_BEHAVIOR_MAP.get(trait_name, [])
                if not allowed:
                    continue

                # 根据强度决定取几条描述
                if intensity < 0.4:
                    selected = allowed[:1]  # 低强度只取第一条（最基础）
                elif intensity < 0.6:
                    selected = allowed[:2]  # 中等强度取前两条
                else:
                    selected = allowed[:3]  # 高强度取前三条

                for behavior in selected:
                    lines.append(f"- {behavior}")

        # ---- 补充基于强度的表达边界提示 ----
        if intensity < 0.3:
            lines.append("- 保持适当的距离感，以回应为主")
        elif intensity < 0.4:
            lines.append("- 以回应为主，不主动发起深入话题")
        elif intensity >= 0.6:
            lines.append("- 可以适度主动关心对方的状态")

        # 安全感相关提示
        if security > 0.6:
            lines.append("- 可以自然地表达信任")
        elif security > 0.3:
            lines.append("- 愿意分享自己的想法和感受")

        if not lines:
            lines = ["- 保持礼貌友善，以自然为主"]

        # ---- 清洗越界短语（最后一道防线） ----
        return self._clean_behavior_text("\n".join(lines))

    def to_compact_prompt(self, behaviors: Dict, core_traits: Optional[Dict] = None) -> str:
        """紧凑版本"""
        warmth = behaviors.get("warmth", 0.3)
        initiative = behaviors.get("initiative", 0.2)
        memory_ref = behaviors.get("memory_reference", 0.2)
        security = behaviors.get("relationship_security", 0.3)
        intensity = behaviors.get("emotional_intensity", 0.3)

        parts = []
        if warmth > 0.6:
            parts.append("温暖")
        elif warmth > 0.3:
            parts.append("温和")

        if initiative > 0.5 and intensity >= 0.4:
            parts.append("主动")

        if memory_ref > 0.4:
            parts.append("会回忆共同经历")

        if security > 0.6:
            parts.append("信任亲近")
        elif security > 0.3:
            parts.append("愿意分享")

        if core_traits:
            shyness = core_traits.get("shyness", 0)
            if shyness > 0.6:
                parts.append("略带害羞")

        return f"当前人格：{'、'.join(parts) if parts else '温和自然'}。回复保持真实自然。"

    @staticmethod
    def _clean_behavior_text(text: str) -> str:
        """
        清洗行为描述中的越界短语。
        这些短语即使从白名单中漏出，也会被此方法拦截。
        """
        forbidden_phrases: List[str] = [
            "习惯使用者的陪伴",
            "期待回应",
            "依赖感",
            "珍视连接",
            "重要之人",
            "特殊存在",
            "离不开",
            "想念",
            "等待用户",
            "需要用户",
        ]
        result = text
        for phrase in forbidden_phrases:
            result = result.replace(phrase, "")
        # 清理多余空行
        return "\n".join(line for line in result.split("\n") if line.strip())

    @staticmethod
    def _clamp(value: float) -> float:
        return round(max(0.0, min(1.0, value)), 3)