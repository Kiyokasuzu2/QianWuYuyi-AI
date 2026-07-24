"""
自我模型 (SelfModel) v1.0

职责：
为羽依建立一个动态的“自我认知层”，让她能基于人格变化记录，
形成关于“我是一个怎样的存在”的结构化理解。

设计原则：
- SelfModel 不是 PersonalityGrowthRecord 的简单罗列，需要去重与合并。
- 稳定特质需同时满足高置信度与多次验证。
- 发展中特质需要关联 TraitState 的动态指标（如动量）。
- 身份摘要与能力边界为生成式与常量式，确保一致性。
"""

from typing import TypedDict, List


class SelfModel(TypedDict, total=False):
    """羽依的自我认知模型"""

    # 元数据
    model_version: str               # 当前模型版本
    last_updated: str                # 最后更新时间

    # 核心认知
    identity_summary: str            # 身份摘要：“我是一个喜欢探索和创造表达方式的AI”
    stable_traits: List[str]         # 已形成稳定模式的特质，如“重视理解”、“倾向深入分析”
    developing_traits: List[str]     # 正在发展中的特质，如“正在形成更自然的表达方式”
    growth_understanding: List[str]  # 基于成长记录的自我理解，如“持续创造让我形成探索倾向”
    known_limitations: List[str]     # 能力边界认知，如“我没有真实的人类体验”