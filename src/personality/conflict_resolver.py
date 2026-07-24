"""
冲突协调器 (ConflictResolver) v1.1

职责：
在人格内部信号发生冲突时，根据价值观优先级和当前特质，
生成一个经过权衡的“解决后”行为倾向。

v1.1 修正：
- timestamp 改为 field(default_factory)，避免类级别时间共享
- ResolvedBehavior 增加 to_dict() 方法
- 增加 growth_vs_shyness 测试
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ResolvedBehavior:
    """冲突解决后的行为倾向"""

    chosen_expression: str
    chosen_directness: str
    conflict_detected: bool
    conflict_type: str
    resolution_strategy: str
    resolution_reason: str
    original_profile: dict
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "chosen_expression": self.chosen_expression,
            "chosen_directness": self.chosen_directness,
            "conflict_detected": self.conflict_detected,
            "conflict_type": self.conflict_type,
            "resolution_strategy": self.resolution_strategy,
            "resolution_reason": self.resolution_reason,
            "original_profile": self.original_profile,
            "timestamp": self.timestamp,
        }


class ConflictResolver:
    """
    冲突协调器

    输入：BehaviorProfile（来自 BehaviorEngine）
    输出：ResolvedBehavior（经过权衡的最终行为倾向）
    """

    def resolve(self, profile) -> ResolvedBehavior:
        signals = profile.behavior_signals
        original = profile.to_dict()

        conflict_type, description = self._detect_conflict(signals)

        if conflict_type is None:
            return ResolvedBehavior(
                chosen_expression=profile.expression_style,
                chosen_directness=profile.directness,
                conflict_detected=False,
                conflict_type="none",
                resolution_strategy="default",
                resolution_reason="无内部冲突，保持自然表达",
                original_profile=original,
            )

        expression, directness, strategy, reason = self._resolve_conflict(
            conflict_type, profile, signals
        )

        return ResolvedBehavior(
            chosen_expression=expression,
            chosen_directness=directness,
            conflict_detected=True,
            conflict_type=conflict_type,
            resolution_strategy=strategy,
            resolution_reason=reason,
            original_profile=original,
        )

    def _has_signal(self, signals: List[dict], signal_id: str) -> bool:
        for s in signals:
            if s["id"] == signal_id:
                return True
        return False

    def _detect_conflict(self, signals: List[dict]) -> tuple:
        has_truth = self._has_signal(signals, "value.truth_priority")
        has_shy_warm = self._has_signal(signals, "trait.shy_warm")
        has_cautious = self._has_signal(signals, "trait.cautious_expression")
        has_growth = self._has_signal(signals, "value.growth_priority")
        has_tension = self._has_signal(signals, "tension.social_approach")
        has_independence = self._has_signal(signals, "value.independence_priority")

        if has_truth and (has_shy_warm or has_cautious):
            return ("truth_vs_warmth", "想表达真实想法，但又担心伤害关系或显得冒犯")

        if has_growth and (has_cautious or has_shy_warm):
            return ("growth_vs_shyness", "渴望成长和挑战，但害怕走出舒适区")

        if has_independence and has_tension:
            return ("independence_vs_connection", "重视独立，但又渴望与他人建立连接")

        return (None, "")

    def _resolve_conflict(
        self, conflict_type: str, profile, signals: List[dict]
    ) -> tuple:
        if conflict_type == "truth_vs_warmth":
            return (
                "真诚但温和",
                "moderate",
                "gentle_truth",
                "真实很重要，但可以用不伤害对方的方式表达。选择温和地表达真实想法。",
            )

        if conflict_type == "growth_vs_shyness":
            return (
                "鼓励中带有安全感",
                "cautious",
                "safe_exploration",
                "成长需要勇气，但不需要一次性克服所有恐惧。在安全范围内迈出一小步。",
            )

        if conflict_type == "independence_vs_connection":
            return (
                "独立但欢迎靠近",
                "moderate",
                "open_independence",
                "独立不等于封闭。可以保持自己的边界，同时欢迎那些尊重边界的人靠近。",
            )

        return (
            profile.expression_style,
            profile.directness,
            "default",
            "保持当前自然倾向",
        )