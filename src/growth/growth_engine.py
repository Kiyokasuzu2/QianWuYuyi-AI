"""
羽依成长引擎（GrowthEngine）v1.6.4

职责:
人生事件 → 成长意义识别 → 人格参数变化 → GrowthState保存

v1.6.4 修改:
- _history_key 改用 event_identity_resolver，基于稳定身份生成 key
- _record_history 优先使用事件已有的 event_identity，并保留 fallback 解析
- apply 入口增加兜底：如果上游未注入身份，Engine 自动解析
- apply 内调整执行顺序：先解析身份，再用身份推导含义
- 添加 DEBUG BEFORE RECORD 输出，便于验证身份传递
"""

from typing import Dict
from datetime import datetime
from src.growth.growth_state import GrowthState
from src.growth.meaning_resolver import resolve_meaning
from src.growth.event_identity_resolver import resolve_event_identity


class GrowthEngine:

    def __init__(self):
        self.state = GrowthState()

    GROWTH_MAP = {
        "birth": {
            "metrics": {"self_awareness": 0.18, "identity_strength": 0.15, "curiosity": 0.10},
            "milestone": True
        },
        "identity_creation": {
            "metrics": {"identity_strength": 0.20, "self_awareness": 0.15, "self_confidence": 0.10},
            "milestone": True
        },
        "relationship_start": {
            "metrics": {"trust": 0.08, "warmth": 0.08, "closeness": 0.12, "emotional_memory": 0.10}
        },
        "emotional_expression": {
            "metrics": {"trust": 0.10, "attachment": 0.12, "security": 0.08, "emotional_memory": 0.15}
        },
        "promise": {
            "metrics": {"attachment": 0.15, "trust": 0.10, "security": 0.12}
        },
        "creation": {
            "metrics": {"self_confidence": 0.08, "self_expression": 0.10, "initiative": 0.06, "creativity": 0.08}
        },
        "growth_support": {
            "metrics": {"trust": 0.08, "self_confidence": 0.10, "closeness": 0.08}
        },
        "companionship": {
            "metrics": {"closeness": 0.02, "warmth": 0.01}
        }
    }

    REPEAT_BONUS = {
        "promise": {"trust": 0.02, "security": 0.02},
        "relationship_start": {"closeness": 0.02, "warmth": 0.01},
        "emotional_expression": {"emotional_memory": 0.02},
        "creation": {"self_expression": 0.02, "creativity": 0.02},
        "companionship": {"warmth": 0.01, "closeness": 0.01}
    }

    def _history_key(self, event):
        return resolve_event_identity(event)

    def _already_grown(self, event):
        if event.get("is_first_occurrence") is False:
            return True
        if event.get("is_first_occurrence") is True:
            return False

        history = self.state.get().setdefault("growth_history", [])
        key = self._history_key(event)

        for item in history:
            if item.get("history_key") == key:
                return True
        return False

    def _calc_growth(self, value, importance, current):
        return round(value * importance * (1 - current), 4)

    def _apply_metrics(self, metrics, importance):
        before = {}
        delta = {}
        for key, value in metrics.items():
            current = self.state.get_metric(key)
            before[key] = current
            amount = self._calc_growth(value, importance, current)
            if amount > 0.0001:
                delta[key] = amount
        if delta:
            self.state.update_metrics(delta)
        return before, delta

    def _record_history(self, event, mode, before, delta):
        history = self.state.get().setdefault("growth_history", [])

        if mode == "repeat":
            key = self._history_key(event)
            for item in history:
                if item.get("history_key") == key:
                    item["reinforcement_count"] = item.get("reinforcement_count", 0) + 1
                    item["last_reinforced_at"] = datetime.now().isoformat()
                    return

        history.append({
            "meaning": event.get("meaning", ""),
            "topic": event.get("canonical_topic", event.get("topic", "")),
            "event_identity": (
                event.get("event_identity")
                or resolve_event_identity(event)
            ),
            "history_key": self._history_key(event),
            "mode": mode,
            "reinforcement_count": 0,
            "last_reinforced_at": None,
            "before": before,
            "delta": delta,
            "time": datetime.now().isoformat()
        })

    def apply(self, event: Dict):
        if event.get("event_scope") == "system":
            return {"status": "ignored", "reason": "system_event"}

        # 1. 确保事件身份存在（兜底）
        if not event.get("event_identity"):
            resolve_event_identity(event)

        # 2. 使用身份解析含义
        meaning = resolve_meaning(event)
        event["meaning"] = meaning
        
        # 如果还是没有含义，尝试最后的手段
        if not meaning:
            meaning = event.get("meaning") or event.get("event_type", "unknown")
            event["meaning"] = meaning
            if not meaning or meaning == "unknown":
                return {"status": "skipped", "reason": "unknown_meaning"}

        rule = self.GROWTH_MAP.get(meaning)
        if not rule:
            return {"status": "skipped", "reason": "no_rule"}

        importance = event.get("importance", 0.5)
        existed = self._already_grown(event)

        if existed:
            metrics = self.REPEAT_BONUS.get(meaning, {})
            mode = "repeat"
        else:
            metrics = rule.get("metrics", {})
            mode = "first"

        before, delta = self._apply_metrics(metrics, importance)

        if not existed and rule.get("milestone", False):
            self.state.add_milestone(event.get("event_id"), event.get("topic", ""))

        # 调试输出（冻结后可移除）
        print(
            "DEBUG BEFORE RECORD:",
            event.get("event_identity"),
            event.get("_identity_source"),
            event.get("evidence")
        )

        self._record_history(event, mode, before, delta)
        self.state.save()

        return {
            "status": "applied",
            "mode": mode,
            "meaning": meaning,
            "topic": event.get("topic"),
            "delta": delta
        }

    def apply_batch(self, events: list):
        return [self.apply(e) for e in events]

    def get_state(self):
        return self.state.get()

    def reset(self):
        self.state.reset()
        print("🔄 GrowthState 已重置")