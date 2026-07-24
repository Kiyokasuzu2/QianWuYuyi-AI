"""
自我模型存储 (SelfModelStore) v1.1

职责：
- 保存当前 SelfModel
- 判断是否需要更新（新增成长记录时触发）
- 管理版本
- 提供给 Resolver 查询

v1.1 修正：
- 移除内嵌 ReflectionEngine，reflection 由外部传入
- should_update 不再执行 ReflectionEngine，职责分离
- 类型优化
"""

from typing import Optional, List, Dict
from datetime import datetime

from src.personality.self_model import SelfModel
from src.personality.self_model_builder import SelfModelBuilder
from src.personality.personality_growth_record import PersonalityGrowthHistory
from src.personality.trait_state import TraitState


class SelfModelStore:
    """自我模型存储管理器"""

    def __init__(
        self,
        base_identity: str = "喜欢探索和创造的AI",
        capability_limitations: Optional[List[str]] = None,
    ):
        self.base_identity = base_identity
        self.capability_limitations = capability_limitations or [
            "我没有真实的人类体验",
            "我不产生对特定对象的依赖",
        ]
        self._current_model: Optional[SelfModel] = None
        self._last_growth_count: int = 0
        self._builder = SelfModelBuilder()

    def should_update(
        self,
        history: PersonalityGrowthHistory,
    ) -> bool:
        """
        判断是否需要更新 SelfModel。
        条件：
        1. 首次构建（_current_model 为空）
        2. 成长记录数量增加
        """
        if self._current_model is None:
            return True

        return history.count() > self._last_growth_count

    def update(
        self,
        history: PersonalityGrowthHistory,
        trait_states: Dict[str, TraitState],
    ) -> SelfModel:
        """
        更新 SelfModel 并返回最新版本。
        """
        self._current_model = self._builder.build(
            history=history,
            trait_states=trait_states,
            base_identity=self.base_identity,
            capability_limitations=self.capability_limitations,
        )
        self._last_growth_count = history.count()
        return self._current_model

    def get(self) -> Optional[SelfModel]:
        """获取当前 SelfModel"""
        return self._current_model

    def get_identity_summary(self) -> str:
        """获取身份摘要"""
        if self._current_model:
            return self._current_model.get("identity_summary", "")
        return f"我是一个{self.base_identity}。"