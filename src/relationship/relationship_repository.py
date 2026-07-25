"""
关系数据仓库 (RelationshipRepository) v1.0

职责：
负责 RelationshipProfile 的持久化存储与加载。
"""

import json
import os
from typing import Optional
from datetime import datetime
from src.relationship.relationship_profile import RelationshipProfile
from src.personality.personality_influence import PersonalityInfluence, InfluenceType


class RelationshipRepository:
    """管理关系画像的持久化存储"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def _get_filepath(self, user_id: str) -> str:
        return os.path.join(self.data_dir, f"relationship_{user_id}.json")

    def load(self, user_id: str) -> Optional[RelationshipProfile]:
        """从文件加载关系画像"""
        filepath = self._get_filepath(user_id)
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            profile = RelationshipProfile(
                user_id=data.get("user_id", user_id),
                relationship_start=data.get("relationship_start", datetime.now().isoformat()),
            )

            for inf_data in data.get("influences", []):
                raw_type = inf_data.get("influence_type", "positive_growth")
                try:
                    influence_type = InfluenceType(raw_type)
                except ValueError:
                    influence_type = InfluenceType.POSITIVE_GROWTH

                influence = PersonalityInfluence(
                    influence_id=inf_data.get("influence_id", ""),
                    timestamp=inf_data.get("timestamp", ""),
                    source_event_id=inf_data.get("source_event_id", ""),
                    source_event_description=inf_data.get("source_event_description", ""),
                    affected_dimension=inf_data.get("affected_dimension", ""),
                    before_value=inf_data.get("before_value", 0.0),
                    after_value=inf_data.get("after_value", 0.0),
                    delta=inf_data.get("delta", 0.0),
                    influence_type=influence_type,
                    impact_weight=inf_data.get("impact_weight", 0.0),
                    confidence=inf_data.get("confidence", 0.5),
                    evidence=inf_data.get("evidence", []),
                )
                profile.add_influence(influence)

            return profile
        except Exception as e:
            print(f"⚠️ 加载关系画像失败: {e}")
            return None

    def save(self, profile: RelationshipProfile):
        """保存关系画像到文件"""
        filepath = self._get_filepath(profile.user_id)
        try:
            data = profile.to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存关系画像失败: {e}")