"""
人格向量（PersonalityVector）
职责：封装人格数据，提供统一访问接口
"""

from typing import Dict, Optional, List


class PersonalityVector:
    """
    人格向量
    封装人格参数，支持统一访问和描述生成
    """

    def __init__(self, data: Dict):
        self._data = data

    def get(self, key: str, default: float = 0.0) -> float:
        """获取数值型参数"""
        return self._data.get(key, default)

    def get_label(self, key: str, default: str = "未知") -> str:
        """获取标签型参数"""
        return self._data.get(key, default)

    def get_behaviors(self) -> Dict:
        """获取行为倾向"""
        return self._data.get("behaviors", {})

    def get_identities(self) -> List[str]:
        """获取自我认知列表"""
        return self._data.get("identities", [])

    def get_all(self) -> Dict:
        """获取全部数据"""
        return self._data

    def summary(self) -> Dict:
        """返回关键参数摘要"""
        return {
            "warmth": self.get("warmth"),
            "gentleness": self.get("gentleness"),
            "shyness": self.get("shyness"),
            "sensitivity": self.get("sensitivity"),
            "dependence": self.get("dependence"),
            "attachment_level": self.get_label("attachment_level", "未知"),
            "trust_level": self.get_label("trust_level", "未知"),
        }

    def __str__(self) -> str:
        summary = self.summary()
        return f"温暖:{summary['warmth']:.2f}, 害羞:{summary['shyness']:.2f}, 依恋:{summary['attachment_level']}, 信任:{summary['trust_level']}"