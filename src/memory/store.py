import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from src.config import get
from src.utils.text import clean_content


class MemoryStore:

    def __init__(self):

        # 历史记忆库
        self.history_path = Path(
            "data/memories.json"
        )

        # 新增记忆库
        self.json_path = Path(
            get(
                "memory.json_path",
                "data/memory.json"
            )
        )

        self.target_user_id = get(
            "memory.target_user_id",
            "366648462"
        )

        self.alias_ids = {
            "terminal_user",
            self.target_user_id
        }

        self._cache = None

        self.json_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


    def load_all(self) -> List[Dict]:

        if self._cache is not None:
            return self._cache

        memories = []

        paths = [
            self.history_path,
            self.json_path
        ]

        for path in paths:

            if not path.exists():
                continue

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    data = json.load(f)

                    if isinstance(data, list):

                        memories.extend(data)

            except Exception as e:

                print(
                    f"加载记忆失败 {path}: {e}"
                )


        self._cache = memories

        return memories



    def save(self, memories: List[Dict]):

        # 新记忆写入独立文件
        with open(
            self.json_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                memories,
                f,
                ensure_ascii=False,
                indent=2
            )


        self._cache = memories



    def add(
        self,
        user_id: str,
        content: str,
        role: str,
        metadata: Optional[Dict] = None
    ):

        content = clean_content(content)


        if not content or len(content) < 3:
            return


        memories = self.load_all()


        memories.append(
            {
                "user_id": user_id,

                "role":
                    "user"
                    if role == "user"
                    else "assistant",

                "content": content,

                "timestamp":
                    datetime.now().isoformat(),

                "metadata":
                    metadata or {}
            }
        )


        self.save(memories)

        # 返回刚保存的记忆对象
        # 供 VectorMemory 建立索引
        return memories[-1]



    def normalize_user_id(
        self,
        user_id: str
    ):

        if user_id in self.alias_ids:

            return self.target_user_id

        return user_id



    def get_by_user(
        self,
        user_id: str
    ) -> List[Dict]:


        memories = self.load_all()


        target = self.normalize_user_id(
            user_id
        )


        result = []


        for m in memories:

            mid = self.normalize_user_id(
                m.get(
                    "user_id",
                    ""
                )
            )


            if mid == target:

                result.append(m)


        return result



    def count(self) -> int:

        return len(
            self.load_all()
        )



    def clear_cache(self):

        self._cache = None



    def upgrade_schema(self):

        memories = self.load_all()

        upgraded = 0


        for mem in memories:

            changed = False


            defaults = {

                "summary": None,

                "meaning": None,

                "tags": [],

                "importance_score": None,

                "importance_label": None,

                "memory_type": None

            }


            for key, value in defaults.items():

                if key not in mem:

                    mem[key] = value

                    changed = True


            if changed:

                upgraded += 1



        if upgraded > 0:

            self.save(
                memories
            )

            print(
                f"✅ Schema升级完成：{upgraded} 条记录"
            )


        return upgraded