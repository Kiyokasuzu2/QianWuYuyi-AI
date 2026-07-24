"""
人格演化引擎 (PersonalityEvolutionEngine) v1.0

职责：
接收 GrowthAccumulator 输出的成长偏移量，结合 TraitState 和 PersonalityHistory，
计算人格维度的动态演化（值、动量、稳定性、置信度）。

设计原则：
- 高稳定性时对外界变化产生“免疫”，不轻易改变
- 连续同方向变化增强动量，形成趋势
- 反向变化重置动量，防止人格漂移
- 无变化时动量缓慢衰减
- 每次验证提高稳定性，长期不验证缓慢降低
- 置信度基于验证次数和一致性

v1.0 范围：
- update_trait() 核心方法
- 不包含 TRAIT_RELATIONS 联动
- 不包含 PERSONALITY_TENSIONS 矛盾处理
"""

from typing import Optional
from src.personality.trait_state import TraitState, create_trait_state
from src.personality.personality_history import PersonalityHistory


class PersonalityEvolutionEngine:
    """
    人格演化引擎

    输入：当前 TraitState、成长偏移量、人格历史
    输出：更新后的 TraitState
    """

    def update_trait(
        self,
        trait_state: TraitState,
        growth_delta: float,
        history: Optional[PersonalityHistory] = None,
    ) -> TraitState:
        """
        综合更新单一人格维度。

        Args:
            trait_state: 当前特质状态
            growth_delta: 来自 GrowthAccumulator 的偏移量（可正可负）
            history: 人格历史记录（用于稳定性计算）

        Returns:
            更新后的 TraitState
        """
        if history is None:
            history = PersonalityHistory()

        # 1. 确定本次变化方向
        direction = self._determine_direction(growth_delta)

        # 2. 更新当前值
        new_value = self._apply_growth(trait_state, growth_delta)

        # 3. 更新动量
        new_momentum = self._update_momentum(trait_state, direction)

        # 4. 更新稳定性
        new_stability = self._update_stability(trait_state, history)

        # 5. 更新置信度
        new_confidence = self._update_confidence(trait_state, direction, history)

        # 6. 组装更新后的状态
        updated: TraitState = {
            "trait": trait_state["trait"],
            "current_value": round(new_value, 4),
            "momentum": round(new_momentum, 4),
            "direction": direction,
            "stability": round(new_stability, 4),
            "confidence": round(new_confidence, 4),
            "last_growth_direction": direction,
            "last_updated": trait_state.get("last_updated", ""),  # 由调用者设置
            "consecutive_same_direction": self._update_consecutive(
                trait_state, direction
            ),
        }
        return updated

    def _apply_growth(self, trait_state: TraitState, growth_delta: float) -> float:
        """
        计算本次值变化。
        有效变化 = 偏移量 × 动量 × (1 - 稳定性 × 0.5)
        稳定性越高，对外界影响的“免疫”越强。
        """
        stability = trait_state.get("stability", 0.3)
        momentum = trait_state.get("momentum", 0.1)
        effective = growth_delta * momentum * (1 - stability * 0.5)
        new_value = trait_state.get("current_value", 0.5) + effective
        return self._clamp(new_value)

    def _update_momentum(self, trait_state: TraitState, direction: str) -> float:
        """
        更新动量：
        - 连续同方向：动量 +0.1（上限1.0）
        - 方向变化（反向）：重置为 0.1
        - 稳定（无变化）：动量 -0.05（下限0.0）
        """
        last_direction = trait_state.get("last_growth_direction", "stable")
        current_momentum = trait_state.get("momentum", 0.1)

        if direction == "stable":
            return max(0.0, current_momentum - 0.05)
        elif direction == last_direction:
            return min(1.0, current_momentum + 0.1)
        else:
            return 0.1  # 反向重置

    def _update_stability(
        self,
        trait_state: TraitState,
        history: PersonalityHistory,
    ) -> float:
        """
        更新稳定性：
        基于该维度的历史变化次数。
        每次验证 +0.05，上限 0.95，起始 0.3。
        如果长期没有变化记录，稳定性不降低（保持当前值）。
        """
        trait_name = trait_state.get("trait", "")
        changes = history.get_changes_for_dimension(trait_name)
        verified_count = len(changes)
        return min(0.95, 0.3 + verified_count * 0.05)

    def _update_confidence(
        self,
        trait_state: TraitState,
        direction: str,
        history: PersonalityHistory,
    ) -> float:
        """
        更新置信度：
        - 连续同方向变化：置信度 +0.05
        - 稳定（无变化）：保持不变
        - 方向变化（反向）：置信度 -0.1
        范围：0.1 ~ 1.0
        """
        last_direction = trait_state.get("last_growth_direction", "stable")
        current_confidence = trait_state.get("confidence", 0.1)

        if direction == "stable":
            return current_confidence
        elif direction == last_direction:
            return min(1.0, current_confidence + 0.05)
        else:
            return max(0.1, current_confidence - 0.1)

    def _determine_direction(self, growth_delta: float) -> str:
        """根据偏移量判断方向"""
        if growth_delta > 0.001:
            return "increase"
        elif growth_delta < -0.001:
            return "decrease"
        else:
            return "stable"

    def _update_consecutive(
        self,
        trait_state: TraitState,
        direction: str,
    ) -> int:
        """更新连续同方向次数"""
        last_direction = trait_state.get("last_growth_direction", "stable")
        if direction == last_direction and direction != "stable":
            return trait_state.get("consecutive_same_direction", 0) + 1
        else:
            return 1 if direction != "stable" else 0

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
        return max(low, min(high, value))