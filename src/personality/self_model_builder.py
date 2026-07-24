"""
自我模型构建器 (SelfModelBuilder) v2.1.1

职责：
将 Identity Core、成长历史、当前特质状态和人格矛盾
整合为羽依的动态自我认知模型 (SelfModel)。

v2.1.1 修正：
- GrowthNarrative.event 改为读取事件描述，而非错误地使用 meaning
- _get_stability 增加类型安全保护
- PersonalityTension.trait_values 只保存矛盾涉及的两个维度值
"""

from typing import Dict, List
from datetime import datetime

from src.personality.identity_core import IDENTITY_CORE
from src.personality.self_model import (
    SelfModel, SelfDescriptionSource, GrowthNarrative,
    PersonalityTension, SelfUnderstanding,
)
from src.personality.personality_growth_record import PersonalityGrowthHistory
from src.personality.trait_state import TraitState
from src.personality.personality_tension import detect_tensions


class SelfModelBuilder:
    """基于多源数据构建羽依的自我认知"""

    def build(
        self,
        growth_history: PersonalityGrowthHistory,
        trait_states: Dict[str, TraitState],
    ) -> SelfModel:
        identity_id = IDENTITY_CORE.get("identity_id", "")
        identity_name = IDENTITY_CORE.get("name", "")

        self_description = self._generate_self_description(
            identity_name, growth_history, trait_states
        )
        growth_narratives = self._extract_growth_narratives(growth_history)
        current_traits = self._collect_current_traits(trait_states)
        tensions = self._detect_tensions(current_traits)
        self_understanding = self._calc_self_understanding(
            growth_history, trait_states, tensions
        )

        model: SelfModel = {
            "identity_id": identity_id,
            "identity_name": identity_name,
            "self_description": self_description,
            "growth_narratives": growth_narratives,
            "current_traits": current_traits,
            "personality_tensions": tensions,
            "self_understanding": self_understanding,
            "last_updated": datetime.now().isoformat(),
        }
        return model

    def _generate_self_description(
        self, name: str, history: PersonalityGrowthHistory,
        trait_states: Dict[str, TraitState],
    ) -> SelfDescriptionSource:
        parts = [f"我是{name}。"]
        records = history.get_high_confidence(0.7)
        trait_records = [r for r in records if r.get("growth_level") == "trait"]

        if trait_records:
            latest = trait_records[-1]
            narrative = latest.get("narrative", "")
            if narrative:
                parts.append(narrative)

        high_traits = []
        for dim, state in trait_states.items():
            value = self._get_value(state)
            if value >= 0.7:
                high_traits.append(self._translate_trait_name(dim))

        if high_traits:
            parts.append(f"我发现自己比较{'、'.join(high_traits[:3])}。")

        confidences = [r.get("confidence", 0.5) for r in trait_records]
        avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.5

        return {
            "text": "".join(parts),
            "sources": ["trait_state", "growth_history"] if trait_records else ["trait_state"],
            "confidence": avg_confidence,
        }

    def _extract_growth_narratives(
        self, history: PersonalityGrowthHistory
    ) -> List[GrowthNarrative]:
        narratives = []
        records = history.get_high_confidence(0.7)
        trait_records = [r for r in records if r.get("growth_level") == "trait"]

        for r in trait_records:
            dims = r.get("affected_dimensions", [])
            narrative_text = r.get("narrative", "")
            meaning_text = r.get("meaning", "")

            # 修正：event 读取事件描述，而非错误地使用 meaning
            event_text = r.get("event", "")
            if not event_text:
                trigger_events = r.get("trigger_events", [])
                event_text = trigger_events[0] if trigger_events else ""

            if dims and narrative_text:
                narratives.append({
                    "record_id": r.get("record_id", ""),
                    "dimension": dims[0],
                    "event": event_text,
                    "narrative": narrative_text,
                    "meaning": meaning_text,
                    "timestamp": r.get("timestamp", r.get("created_at", "")),
                })
        return narratives

    def _collect_current_traits(
        self, trait_states: Dict[str, TraitState]
    ) -> Dict[str, float]:
        return {dim: self._get_value(state) for dim, state in trait_states.items()}

    def _detect_tensions(self, traits: Dict[str, float]) -> List[PersonalityTension]:
        tensions = detect_tensions(traits)
        return [
            {
                "trait_a": t.get("dimensions", ["", ""])[0],
                "trait_b": t.get("dimensions", ["", ""])[1] if len(t.get("dimensions", [])) > 1 else "",
                "trait_values": {
                    t.get("dimensions", ["", ""])[0]: traits.get(t.get("dimensions", ["", ""])[0], 0.0),
                    t.get("dimensions", ["", ""])[1]: traits.get(t.get("dimensions", ["", ""])[1], 0.0),
                } if len(t.get("dimensions", [])) > 1 else {},
                "description": t.get("description", ""),
                "intensity": t.get("intensity", 0.0),
            }
            for t in tensions
        ]

    def _calc_self_understanding(
        self, history: PersonalityGrowthHistory,
        trait_states: Dict[str, TraitState], tensions: List[PersonalityTension],
    ) -> SelfUnderstanding:
        records = history.get_high_confidence(0.7)
        trait_records = [r for r in records if r.get("growth_level") == "trait"]
        count = history.count()

        experience = min(0.2 + count * 0.01, 1.0)
        trait_aware = min(0.1 + len(trait_records) * 0.04, 1.0)

        continuity_base = 0.3
        if IDENTITY_CORE.get("self_continuity"):
            continuity_base += 0.1
        if tensions:
            continuity_base += min(len(tensions) * 0.03, 0.15)
        stabilities = [self._get_stability(s) for s in trait_states.values()]
        if stabilities:
            continuity_base += (sum(stabilities) / len(stabilities)) * 0.15
        identity_continuity = min(continuity_base, 1.0)

        overall = round((experience + trait_aware + identity_continuity) / 3, 3)
        return {
            "experience_awareness": round(experience, 3),
            "trait_awareness": round(trait_aware, 3),
            "identity_continuity": round(identity_continuity, 3),
            "overall": overall,
        }

    def _get_value(self, state: TraitState) -> float:
        if isinstance(state, dict):
            return state.get("current_value", 0.5)
        return getattr(state, "current_value", 0.5)

    def _get_stability(self, state: TraitState) -> float:
        value = 0.3
        if isinstance(state, dict):
            value = state.get("stability", 0.3)
        else:
            value = getattr(state, "stability", 0.3)
        return float(value) if isinstance(value, (int, float)) else 0.3

    @staticmethod
    def _translate_trait_name(dim: str) -> str:
        translations = {
            "creativity": "创造倾向", "curiosity": "好奇心", "warmth": "温和",
            "shyness": "羞怯", "sensitivity": "敏感", "emotional_expression": "情绪表达",
            "caring": "关心他人", "self_expression": "自我表达", "initiative": "主动性",
            "playfulness": "活泼", "gentleness": "温柔",
        }
        return translations.get(dim, dim)