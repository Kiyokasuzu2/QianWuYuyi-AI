"""
MemoryStore v1.1 —— 羽依长期记忆存储层
只拒绝 truth <= 0 的记忆，用途判断交给上层
"""

import json
import os
from typing import List, Dict


class MemoryStore:
    def __init__(self, path="data/memory.json"):
        self.path = path
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        if not os.path.exists(path):
            self._save([])

    def add(self, memory: Dict):
        """保存单条记忆，自动丢弃零信任记忆"""
        if memory.get("truth", 0) <= 0:
            return

        memories = self.load()
        if any(m.get("id") == memory.get("id") for m in memories):
            return
        memories.append(memory)
        self._save(memories)

    def add_many(self, memories: List[Dict]):
        for mem in memories:
            self.add(mem)

    def load(self) -> List[Dict]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def delete(self, memory_id: str):
        memories = [m for m in self.load() if m.get("id") != memory_id]
        self._save(memories)

    def clear(self):
        self._save([])

    def _save(self, data):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MemoryStore] save failed: {e}")