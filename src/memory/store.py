import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from src.config import get
from src.utils.text import clean_content


class MemoryStore:
    def __init__(self):
        self.json_path = Path(get("memory.json_path", "data/memories.json"))
        self.target_user_id = get("memory.target_user_id", "366648462")
        self._cache = None
        self.json_path.parent.mkdir(parents=True, exist_ok=True)

    def load_all(self) -> List[Dict]:
        if self._cache is not None:
            return self._cache
        if self.json_path.exists():
            with open(self.json_path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
            return self._cache
        return []

    def save(self, memories: List[Dict]):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)
        self._cache = memories

    def add(self, user_id: str, content: str, role: str, metadata: Optional[Dict] = None):
        content = clean_content(content)
        if not content or len(content) < 3:
            return
        memories = self.load_all()
        memories.append({
            "user_id": user_id,
            "role": "user" if role == "user" else "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        self.save(memories)

    def get_by_user(self, user_id: str) -> List[Dict]:
        memories = self.load_all()
        return [m for m in memories if m.get("user_id") == user_id]

    def count(self) -> int:
        return len(self.load_all())

    def clear_cache(self):
        self._cache = None

    def upgrade_schema(self):
        """升级现有记忆的 schema，为每条记录增加新字段（如果不存在）"""
        memories = self.load_all()
        upgraded = 0
        
        for mem in memories:
            changed = False
            
            if "summary" not in mem:
                mem["summary"] = None
                changed = True
            if "meaning" not in mem:
                mem["meaning"] = None
                changed = True
            if "tags" not in mem:
                mem["tags"] = []
                changed = True
            if "importance_score" not in mem:
                mem["importance_score"] = None
                changed = True
            if "importance_label" not in mem:
                mem["importance_label"] = None
                changed = True
            if "memory_type" not in mem:
                mem["memory_type"] = None
                changed = True
            
            if changed:
                upgraded += 1
        
        if upgraded > 0:
            self.save(memories)
            print(f"✅ Schema 升级完成：{upgraded} 条记录已更新")
        
        return upgraded