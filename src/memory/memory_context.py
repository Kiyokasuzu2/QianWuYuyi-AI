"""
MemoryContext - 记忆上下文数据类
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class MemoryContext:
    title: str
    summary: str
    emotion: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_prompt_text(self, index: int = -1) -> str:
        prefix = f"{index + 1}. " if index >= 0 else ""

        time_text = ""
        if self.timestamp:
            try:
                date = self.timestamp[:10]
                time_text = f"\n   时间：{date}"
            except:
                pass

        emotion_text = ""
        if self.emotion:
            emotion_text = f"\n   这段经历带来的感受：{', '.join(self.emotion)}"

        return f"{prefix}[{self.title}]\n   {self.summary}{time_text}{emotion_text}".strip()

    @classmethod
    def from_event(cls, event: dict) -> "MemoryContext":
        title = event.get("canonical_topic", "") or event.get("topic", "")
        summary = event.get("memory_summary", "")
        if not summary:
            event_text = event.get("event", "")
            summary = event_text[:80] + "..." if len(event_text) > 80 else event_text
        emotion = event.get("emotion_tag", [])
        timestamp = (
            event.get("occurred_at")
            or event.get("timestamp")
            or event.get("created_at")
            or ""
        )
        return cls(title=title, summary=summary, emotion=emotion, timestamp=timestamp)