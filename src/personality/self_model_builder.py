"""
自我模型构建器 (SelfModelBuilder) v1.0

职责：
分析人格成长历史(PersonalityGrowthHistory)与当前特质状态(TraitState)，
构建出一个动态的、去重合并的 SelfModel。
"""

from typing import Dict, List
from datetime import datetime

from src.personality.personality_growth_record import PersonalityGrowthHistory
from src.personality.trait_state import TraitState
from src.personality.self_model import SelfModel


class SelfModelBuilder:
    """基于成长记录与特质状态构建自我模型"""

    def build(
        self,
        history: PersonalityGrowthHistory,
        trait_states: Dict[str, TraitState],
        base_identity: str,
        capability_limitations: List[str],
    ) -> SelfModel:
        """
        核心构建方法。

        Args:
            history: 人格成长历史记录。
            trait_states: 当前所有维度的 TraitState 字典。
            base_identity: 基础身份描述（来自 PersonalityProfile 或系统常量）。
            capability_limitations: 能力边界列表（来自 CapabilityBoundary）。

        Returns:
            一个全新的、反映当前状态的 SelfModel。
        """
        # 1. 提取高置信度记录
        high_conf_records = history.get_high_confidence(0.7)

        # 2. 分析稳定特质与发展中特质
        stable_traits = self._extract_stable_traits(high_conf_records)
        developing_traits = self._extract_developing_traits(high_conf_records, trait_states)

        # 3. 去重合并成长理解
        growth_understanding = self._merge_growth_understanding(high_conf_records)

        # 4. 生成身份摘要
        identity_summary = self._generate_identity_summary(
            base_identity, stable_traits
        )

        # 5. 组装模型
        model: SelfModel = {
            "model_version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "identity_summary": identity_summary,
            "stable_traits": stable_traits,
            "developing_traits": developing_traits,
            "growth_understanding": growth_understanding,
            "known_limitations": capability_limitations,
        }
        return model

    def _extract_stable_traits(self, records: List) -> List[str]:
        """
        提取稳定特质：growth_level 为 "trait"，且 validation_count >= 3。
        """
        stable_meanings = []
        for r in records:
            if r.get("growth_level") == "trait" and r.get("validation_count", 0) >= 3:
                meaning = r.get("meaning")
                if meaning and meaning not in stable_meanings:
                    stable_meanings.append(meaning)
        return stable_meanings

    def _extract_developing_traits(
        self, records: List, trait_states: Dict[str, TraitState]
    ) -> List[str]:
        """
        提取发展中特质：growth_level 为 "preference"，
        且关联的 TraitState 具有较高动量（momentum > 0.5）。
        """
        developing_descriptions = []
        for r in records:
            if r.get("growth_level") != "preference":
                continue

            has_high_momentum = False
            for dim in r.get("affected_dimensions", []):
                state = trait_states.get(dim)
                if state and state.get("momentum", 0.0) > 0.5:
                    has_high_momentum = True
                    break

            if has_high_momentum:
                meaning = r.get("meaning", "")
                if meaning and meaning not in developing_descriptions:
                    developing_descriptions.append(f"正在形成：{meaning}")

        return developing_descriptions

    def _merge_growth_understanding(self, records: List) -> List[str]:
        """
        合并成长理解：提取 narrative 字段，去重并保留最稳定的表述。
        """
        narratives = []
        for r in records:
            narrative = r.get("narrative")
            if narrative and narrative not in narratives:
                narratives.append(narrative)
        return narratives

    def _generate_identity_summary(
        self, base: str, stable_traits: List[str]
    ) -> str:
        """
        生成身份摘要：基于身份与稳定特质进行总结。
        """
        if not stable_traits:
            return f"我是一个{base}。"
        
        summary_traits = "、".join(stable_traits[:3])
        return f"我是一个{base}，我的特质包括：{summary_traits}。"