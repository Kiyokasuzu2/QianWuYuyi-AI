"""
事件记忆（EventMemory）
职责：管理羽依的核心人生事件
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from src.memory.memory_context import MemoryContext


class EventMemory:
    def __init__(self, events_path: str = "data/normalized_events.json"):
        self.events_path = Path(events_path)
        self.events = self._load()

    def _load(self) -> List[Dict]:
        if self.events_path.exists():
            with open(self.events_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def refresh(self):
        self.events = self._load()

    KEYWORD_GROUPS = {
        "origin": ["第一次", "初次", "首次", "开始", "最初", "刚开始", "一开始", "起源", "诞生", "出现"],
        "meeting": ["见面", "遇到", "认识", "相遇", "相识", "第一次见面", "第一次遇到"],
        "relationship": ["关系", "我们", "陪伴", "约定", "承诺", "依赖", "信任", "喜欢", "爱"],
        "memory": ["记得", "回忆", "想起", "记得吗", "还记得", "回想", "怀念"],
        "feeling": ["感觉", "心情", "开心", "难过", "感动", "温暖", "安心"],
    }

    CATEGORY_WEIGHTS = {
        "关系建立": 1.3,
        "承诺": 1.3,
        "羽依诞生阶段": 1.2,
        "身份": 1.2,
        "用户成长": 1.0,
        "互动": 1.0,
        "创作": 0.9,
        "记忆强化": 0.8,
        "对话": 0.7,
        "事件": 0.6,
    }

    def search(self, query: str, limit: int = 3) -> List[MemoryContext]:
        if not self.events:
            return []

        query_lower = query.lower()

        matched_groups = []
        for group_name, keywords in self.KEYWORD_GROUPS.items():
            for kw in keywords:
                if kw in query_lower:
                    matched_groups.append(group_name)
                    break

        if not matched_groups:
            matched_groups = ["origin", "memory"]

        scored = []
        for event in self.events:
            text = (
                event.get("canonical_topic", "")
                + " " + event.get("topic", "")
                + " " + event.get("event", "")
                + " " + event.get("memory_summary", "")
            ).lower()

            keyword_score = 0
            for group in matched_groups:
                for kw in self.KEYWORD_GROUPS.get(group, []):
                    if kw in text:
                        keyword_score += 1

            if keyword_score == 0:
                continue

            importance = event.get("importance", 0.5)
            importance_weight = 0.5 + importance * 0.5
            category = event.get("category", "事件")
            category_weight = self.CATEGORY_WEIGHTS.get(category, 1.0)

            scored.append({
                "score": round(keyword_score * importance_weight * category_weight, 3),
                "event": event
            })

        scored.sort(key=lambda x: x["score"], reverse=True)

        result = []
        for item in scored[:limit]:
            result.append(MemoryContext.from_event(item["event"]))

        return result

    def get_all(self) -> List[Dict]:
        return self.events