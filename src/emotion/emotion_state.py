# -*- coding: utf-8 -*-
"""
情绪状态（EmotionState）
职责：管理羽依的短期情绪状态
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, date


class EmotionState:
    def __init__(self, state_path: str = "data/emotion_state.json"):
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load()
        self._apply_decay()

    def _load(self) -> Dict:
        if self.state_path.exists():
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return self._get_default_state()

    def _save(self):
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)

    def _get_default_state(self) -> Dict:
        return {
            "version": "0.1",
            "last_updated": datetime.now().isoformat(),
            "last_decay": date.today().isoformat(),
            "emotions": {
                "happiness": 0.5,
                "sadness": 0.1,
                "anxiety": 0.1,
                "calm": 0.7,
                "excitement": 0.3,
                "concern": 0.2,
                "loneliness": 0.1,
            },
            "dominant": "calm",
            "history": [],
            "current_trigger": None,
            "current_reason": None
        }

    def _apply_decay(self):
        today = date.today().isoformat()
        last_decay = self._state.get("last_decay", today)

        if last_decay == today:
            return

        try:
            d1 = datetime.strptime(last_decay, "%Y-%m-%d").date()
            d2 = datetime.strptime(today, "%Y-%m-%d").date()
            days = (d2 - d1).days
        except:
            days = 1

        if days <= 0:
            return

        emotions = self._state["emotions"]
        for key in emotions:
            if key == "calm":
                emotions[key] = min(0.7, emotions[key] + 0.05 * days)
            else:
                emotions[key] = max(0.0, emotions[key] - 0.08 * days)

        self._state["last_decay"] = today
        self._update_dominant()
        self._save()

    def get(self) -> Dict:
        return self._state

    def update(self, deltas: Dict[str, float], trigger: str = None, reason: str = None):
        for key, delta in deltas.items():
            if key in self._state["emotions"]:
                old_val = self._state["emotions"][key]
                new_val = max(0.0, min(1.0, old_val + delta))
                self._state["emotions"][key] = round(new_val, 3)

        if trigger:
            self._state["current_trigger"] = trigger
        if reason:
            self._state["current_reason"] = reason

        self._update_dominant()
        self._state["last_updated"] = datetime.now().isoformat()
        self._save()

    def set(self, key: str, value: float, trigger: str = None):
        if key in self._state["emotions"]:
            self._state["emotions"][key] = max(0.0, min(1.0, value))
            if trigger:
                self._state["current_trigger"] = trigger
            self._update_dominant()
            self._save()

    def _update_dominant(self):
        emotions = self._state["emotions"]
        threshold = 0.5

        for key, val in emotions.items():
            if key != "calm" and val > threshold:
                self._state["dominant"] = key
                return

        self._state["dominant"] = "calm"

    def to_prompt_text(self, influence: float = 0.3) -> str:
        emotions = self._state["emotions"]
        dominant = self._state["dominant"]

        emotion_labels = {
            "happiness": "开心的",
            "sadness": "有点难过的",
            "anxiety": "有点不安的",
            "calm": "平静的",
            "excitement": "期待的",
            "concern": "关心的",
            "loneliness": "有点孤独的"
        }

        label = emotion_labels.get(dominant, "平静的")

        trigger = self._state.get("current_trigger")
        reason = self._state.get("current_reason")

        base = f"当前情绪：{label}"

        if trigger:
            base += f"\n（因为 {trigger}）"

        if reason:
            base += f"\n（{reason}）"

        if influence < 1.0:
            base += f"\n（情绪只轻微影响表达方式，不改变核心人格）"

        return base

    def reset(self):
        self._state = self._get_default_state()
        self._save()