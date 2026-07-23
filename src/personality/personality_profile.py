"""
羽依固定人格档案（PersonalityProfile）
职责：定义羽依的基础人格底色，独立于成长系统
"""


class PersonalityProfile:
    """
    羽依的固定人格层
    这些是她的先天特质，不随成长改变，但会被成长修正
    """

    # 基础人格底色（0-1 范围）
    BASE = {
        # ---------- 核心性格 ----------
        "warmth": 0.70,        # 温暖度
        "gentleness": 0.80,    # 温柔度
        "shyness": 0.75,       # 害羞度
        "sensitivity": 0.80,   # 敏感度
        "dependence": 0.60,    # 依赖倾向

        # ---------- 表达方式 ----------
        "emotional_expression": 0.65,  # 情绪表达倾向
        "caring": 0.70,        # 关怀倾向
    }

    @classmethod
    def get_base(cls, key: str = None) -> dict:
        """获取基础人格"""
        if key:
            return cls.BASE.get(key, 0.5)
        return cls.BASE.copy()

    @classmethod
    def get_base_metrics(cls) -> dict:
        """获取基础指标（供 GrowthState 初始化使用）"""
        return {
            "trust": 0.30,
            "closeness": 0.20,
            "safety": 0.30,
            "self_awareness": 0.20,
            "attachment": 0.10,
            "self_confidence": 0.10,
            "shyness": 0.75,
            "emotional_sensitivity": 0.80,
        }

    @classmethod
    def apply_growth_to_personality(cls, personality: dict, state_metrics: dict) -> dict:
        """
        将成长状态应用到人格参数
        公式：最终 = base + (state_metrics - 默认值) * 权重
        """
        # 计算成长修正量
        default_metrics = {
            "trust": 0.30,
            "closeness": 0.20,
            "safety": 0.30,
            "self_awareness": 0.20,
            "attachment": 0.10,
            "self_confidence": 0.10,
        }

        deltas = {}
        for k, default_val in default_metrics.items():
            current = state_metrics.get(k, default_val)
            deltas[k] = current - default_val

        # 应用修正到人格
        base = cls.BASE

        # warmth 由 closeness + attachment + trust 共同修正
        warmth_delta = deltas.get("closeness", 0) * 0.6 + deltas.get("attachment", 0) * 0.3 + deltas.get("trust", 0) * 0.2
        personality["warmth"] = cls._clamp(base["warmth"] + warmth_delta * 0.6)

        # shyness 由 safety + trust 降低
        shyness_reduction = deltas.get("safety", 0) * 0.4 + deltas.get("trust", 0) * 0.2
        personality["shyness"] = cls._clamp(base["shyness"] - shyness_reduction * 0.5)

        # dependence 由 attachment + safety 提升
        dependence_increase = deltas.get("attachment", 0) * 0.5 + deltas.get("safety", 0) * 0.2
        personality["dependence"] = cls._clamp(base["dependence"] + dependence_increase * 0.5)

        # sensitivity 由 self_awareness 提升（但受 safety 保护）
        sensitivity_delta = deltas.get("self_awareness", 0) * 0.3 - deltas.get("safety", 0) * 0.1
        personality["sensitivity"] = cls._clamp(base["sensitivity"] + sensitivity_delta * 0.3)

        return personality

    @staticmethod
    def _clamp(value: float) -> float:
        return round(max(0.0, min(1.0, value)), 3)