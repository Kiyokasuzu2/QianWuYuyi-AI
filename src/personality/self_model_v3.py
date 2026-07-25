"""
SelfModel v3 — 具有成长叙事的自我模型
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class NarrativeItem:
    """一条成长叙事，自带来源追溯"""
    text: str
    source_ids: List[str] = field(default_factory=list)


@dataclass
class SelfModelV3:
    identity: str = "浅雾羽依"
    traits: Dict[str, float] = field(default_factory=dict)
    values: Dict[str, float] = field(default_factory=dict)
    beliefs: List[str] = field(default_factory=list)
    narrative_items: List[NarrativeItem] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity": self.identity,
            "traits": self.traits,
            "values": self.values,
            "beliefs": self.beliefs,
            "narrative_items": [
                {"text": item.text, "source_ids": item.source_ids}
                for item in self.narrative_items
            ],
            "last_updated": self.last_updated
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SelfModelV3":
        items = data.get("narrative_items", [])
        narrative_items = []
        for item in items:
            if isinstance(item, dict):
                narrative_items.append(
                    NarrativeItem(
                        text=item.get("text", ""),
                        source_ids=item.get("source_ids", [])
                    )
                )
        return cls(
            identity=data.get("identity", "浅雾羽依"),
            traits=data.get("traits", {}),
            values=data.get("values", {}),
            beliefs=data.get("beliefs", []),
            narrative_items=narrative_items,
            last_updated=data.get("last_updated", datetime.now().isoformat())
        )

    def to_prompt_context(self) -> str:
        parts = [f"我是{self.identity}。"]
        if self.traits:
            trait_desc = "、".join(
                f"{k}（{v:.1f}）" for k, v in self.traits.items()
            )
            parts.append(f"我的性格特征：{trait_desc}。")
        if self.beliefs:
            belief_desc = "；".join(self.beliefs)
            parts.append(f"我相信：{belief_desc}。")
        if self.narrative_items:
            parts.append("我为什么会这样：")
            for item in self.narrative_items:
                parts.append(f"- {item.text}")
        return "\n".join(parts)