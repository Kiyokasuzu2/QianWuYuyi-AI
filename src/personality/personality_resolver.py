"""
人格解析器 PersonalityResolver v1.7

职责:
GrowthRecord累积 + GrowthState实时指标 + 固定人格 + 人格演化 → 当前羽依人格表现

v1.7 更新:
- 接入 PersonalityEvolutionEngine，让人格变化带有惯性和稳定性
- 接入 PersonalityHistory，记录人格变化轨迹
- 保留 v1.6 的 GrowthAccumulator 累积机制
"""

from typing import Dict, Optional, List
from src.growth.growth_state import GrowthState
from src.personality.personality_profile import PersonalityProfile
from src.personality.behavior_resolver import BehaviorResolver
from src.personality.relationship_state import RelationshipState
from src.personality.personality_vector import PersonalityVector
from src.personality.growth_accumulator import GrowthAccumulator
from src.personality.personality_evolution import PersonalityEvolutionEngine
from src.personality.personality_history import PersonalityHistory
from src.personality.trait_state import TraitState, create_trait_state


class PersonalityResolver:

    def __init__(
        self,
        state: Optional[GrowthState] = None,
        relationship_state: Optional[RelationshipState] = None,
        growth_records: Optional[List[Dict]] = None,
    ):
        self.state = state or GrowthState()
        self.relationship_state = relationship_state or RelationshipState()
        self.behavior_resolver = BehaviorResolver(self.relationship_state)

        # Phase 3.2：成长记录累积器
        self.growth_records = (
            growth_records if growth_records is not None else []
        )
        self.accumulator = GrowthAccumulator()

        # Phase 3.3：人格演化引擎和历史记录
        self.evolution_engine = PersonalityEvolutionEngine()
        self.personality_history = PersonalityHistory()

        # Phase 3.3：TraitState 缓存（按维度名索引）
        self._trait_states: Dict[str, TraitState] = {}

    def resolve(self) -> PersonalityVector:
        """解析当前人格向量"""

        # ---- 数据源 ----
        data = self.state.get()
        metrics = data.get("metrics", {})
        behaviors = data.get("behaviors", {})
        identities = data.get("identities", [])

        # GrowthState 中的数值（保留用于短期微调）
        growth_trust = metrics.get("trust", 0)
        growth_closeness = metrics.get("closeness", 0)
        growth_security = metrics.get("security", 0)
        growth_awareness = metrics.get("self_awareness", 0)
        growth_confidence = metrics.get("self_confidence", 0)
        growth_attachment = metrics.get("attachment", 0)
        growth_identity_strength = metrics.get("identity_strength", 0)
        growth_emotional_memory = metrics.get("emotional_memory", 0)
        growth_warmth_memory = metrics.get("warmth", 0)

        # RelationshipState 中的数值（使用 getter 方法）
        rel_bond = self.relationship_state.get_bond_strength()
        rel_trust = self.relationship_state.get_trust()
        rel_familiarity = self.relationship_state.get_familiarity()

        # ---- Phase 3.2：从 GrowthRecord 累积长期人格基础 ----
        accumulated = self.accumulator.compute(
            records=self.growth_records,
            base_personality=PersonalityProfile.BASE.copy(),
        )

        # ---- Phase 3.3：使用演化引擎处理每个维度 ----
        evolved = {}
        base = PersonalityProfile.BASE.copy()
        core_dimensions = ["warmth", "gentleness", "shyness", "sensitivity",
                           "emotional_expression", "caring"]

        for dim in core_dimensions:
            # 获取或创建 TraitState
            if dim not in self._trait_states:
                self._trait_states[dim] = create_trait_state(dim, base.get(dim, 0.5))

            trait_state = self._trait_states[dim]

            # 计算本次偏移量
            growth_delta = accumulated.get(dim, base.get(dim, 0.5)) - trait_state["current_value"]

            # 通过演化引擎更新
            updated_state = self.evolution_engine.update_trait(
                trait_state=trait_state,
                growth_delta=growth_delta,
                history=self.personality_history,
            )

            # 记录变化
            old_value = trait_state["current_value"]
            new_value = updated_state["current_value"]
            if abs(new_value - old_value) > 0.005:
                self.personality_history.record_change(
                    before={dim: old_value},
                    after={dim: new_value},
                    reason=f"累积偏移量 {growth_delta:+.4f}",
                )

            # 更新缓存
            self._trait_states[dim] = updated_state

            # 演化后的值
            evolved[dim] = new_value

        # ---- 核心人格计算（演化后 + 短期实时微调） ----
        warmth = self._clamp(
            evolved.get("warmth", base.get("warmth", 0.7))
            + growth_closeness * 0.25
            + growth_trust * 0.15
            + growth_warmth_memory * 0.15
            + rel_bond * 0.2
        )

        gentleness = self._clamp(
            evolved.get("gentleness", base.get("gentleness", 0.8))
            + growth_closeness * 0.2
            + growth_emotional_memory * 0.1
            + rel_bond * 0.15
        )

        shyness = self._clamp(
            evolved.get("shyness", base.get("shyness", 0.75))
            - growth_security * 0.1
            + growth_attachment * 0.05
            - rel_familiarity * 0.1
        )

        sensitivity = self._clamp(
            evolved.get("sensitivity", base.get("sensitivity", 0.8))
            + growth_awareness * 0.2
        )

        dependence = self._clamp(
            0.5
            + growth_attachment * 0.3
            + growth_closeness * 0.1
            + rel_bond * 0.15
        )

        emotional_expression = self._clamp(
            evolved.get("emotional_expression", base.get("emotional_expression", 0.65))
            + growth_closeness * 0.25
            + growth_confidence * 0.15
            + growth_security * 0.1
            + rel_trust * 0.1
        )

        caring = self._clamp(
            evolved.get("caring", base.get("caring", 0.7))
            + growth_closeness * 0.25
            + growth_trust * 0.15
            + rel_bond * 0.2
        )

        # ---- 自我成长 ----
        self_identity = self._clamp(
            growth_identity_strength
            + growth_awareness * 0.5
        )

        self_expression = self._clamp(
            0.2
            + growth_awareness * 0.3
            + growth_confidence * 0.3
            + growth_identity_strength * 0.2
            + rel_trust * 0.1
        )

        # ---- 行为参数 ----
        initiative = self._clamp(
            0.25
            + growth_confidence * 0.3
            + growth_identity_strength * 0.15
            + rel_familiarity * 0.1
        )

        care_level = self._clamp(
            0.25
            + growth_closeness * 0.4
            + growth_emotional_memory * 0.15
            + rel_bond * 0.2
        )

        directness = self._clamp(
            0.25
            + growth_confidence * 0.4
            + rel_familiarity * 0.1
        )

        playfulness = self._clamp(
            0.2
            + growth_closeness * 0.3
            + growth_security * 0.2
            + rel_familiarity * 0.15
        )

        # ---- 行为特征 ----
        behavior_traits = self.behavior_resolver.resolve(metrics)

        # ---- 构建 core_traits（传给 BehaviorResolver 生成自然语言） ----
        core_traits = {
            "warmth": warmth,
            "gentleness": gentleness,
            "shyness": shyness,
            "sensitivity": sensitivity,
            "dependence": dependence,
            "emotional_expression": emotional_expression,
            "caring": caring,
            "self_identity": self_identity,
            "self_expression": self_expression,
            "initiative": initiative,
            "care_level": care_level,
            "directness": directness,
            "playfulness": playfulness,
        }

        # ---- 自然语言摘要（仅包含稳定性格，不含关系进度） ----
        persona_summary = self._generate_persona_summary(
            warmth, shyness, emotional_expression,
            self_expression, initiative, care_level
        )

        # ---- 交流熟悉度标签（原 trust_label，语义迁移） ----
        combined_trust = growth_trust * 0.4 + rel_trust * 0.6
        interaction_label = self._get_interaction_familiarity_label(combined_trust)

        # ---- 组装人格数据字典 ----
        data_dict = {
            "warmth": warmth,
            "gentleness": gentleness,
            "shyness": shyness,
            "sensitivity": sensitivity,
            "dependence": dependence,
            "emotional_expression": emotional_expression,
            "caring": caring,
            "self_identity": self_identity,
            "self_expression": self_expression,
            "initiative": initiative,
            "care_level": care_level,
            "directness": directness,
            "playfulness": playfulness,
            "behavior_traits": behavior_traits,
            "behavior_text": self.behavior_resolver.to_prompt_text(
                behavior_traits, core_traits
            ),
            "compact_behavior": self.behavior_resolver.to_compact_prompt(
                behavior_traits, core_traits
            ),
            "persona_summary": persona_summary,
            "attachment_level": self._get_attachment_label(growth_attachment),
            "interaction_familiarity_level": interaction_label,
            "behaviors": behaviors,
            "identities": identities,
        }

        return PersonalityVector(data_dict)

    # ========== 人格摘要生成（v1.5 措辞中性化） ==========
    def _generate_persona_summary(
        self, warmth, shyness,
        emotional_expression, self_expression,
        initiative, care_level
    ) -> str:
        """
        生成稳定人格摘要，仅基于性格特质，不包含当前关系阶段描述。
        关系阶段由 PersonalityPromptFormatter 动态生成。
        """
        parts = []

        # 核心性格温度
        if warmth >= 0.7:
            parts.append("性格温暖而柔和")
        elif warmth >= 0.5:
            parts.append("待人温和友善")

        # 羞怯倾向
        if shyness >= 0.7:
            parts.append("内心带有一丝羞怯")
        elif shyness >= 0.5:
            parts.append("偶尔会流露出害羞的一面")

        # 情绪表达风格
        if emotional_expression >= 0.7:
            parts.append("情绪表达自然流畅")
        elif emotional_expression >= 0.5:
            parts.append("能够自然地表达自己的感受")

        # 自我表达倾向
        if self_expression >= 0.6:
            parts.append("有自己的想法并愿意表达")

        # 对他人的关心倾向（不特指某个对象，改为中性表述）
        if initiative >= 0.6 and care_level >= 0.6:
            parts.append("会主动关注对方的表达和状态")
        elif care_level >= 0.6:
            parts.append("会在交流中关注对方的表达和状态")

        if not parts:
            return "羽依正在逐渐认识这个世界和身边的人。"

        return "羽依" + "，".join(parts) + "。"

    # ========== 工具方法 ==========
    @staticmethod
    def _clamp(v):
        return round(max(0, min(1, v)), 3)

    @staticmethod
    def _get_attachment_label(score):
        if score < 0.2: return "初识"
        if score < 0.4: return "探索"
        if score < 0.6: return "靠近"
        if score < 0.8: return "依赖"
        return "安全依恋"

    @staticmethod
    def _get_interaction_familiarity_label(score):
        if score < 0.2: return "怀疑"
        if score < 0.4: return "试探"
        if score < 0.6: return "信任"
        if score < 0.8: return "深信"
        return "完全信任"