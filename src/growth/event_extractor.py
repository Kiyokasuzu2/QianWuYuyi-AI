import json
import hashlib

from src.config import get
from src.memory.store import MemoryStore
from src.response.llm import LLMClient
from src.utils.text import clean_content


class EventExtractor:
    """
    羽依成长系统
    事件提取器 v5.0

    聊天记录
        ↓
    原始事件

    只负责发现：
    发生了什么
    """

    def __init__(self):

        self.store = MemoryStore()

        self.llm = LLMClient()

        self.batch_size = get(
            "growth.consolidation_batch_size",
            50
        )

        self.target_user_id = get(
            "memory.target_user_id",
            "366648462"
        )


    def get_unprocessed_memories(
        self,
        limit=None
    ):

        memories = self.store.get_by_user(
            self.target_user_id
        )

        limit = limit or self.batch_size

        result=[]

        for mem in memories:

            if not mem.get("summary"):

                result.append(mem)

                if len(result)>=limit:
                    break

        return result



    def _format_memories(
        self,
        memories
    ):

        lines=[]

        for idx,mem in enumerate(memories):

            role = (
                "用户"
                if mem.get("role")=="user"
                else
                "羽依"
            )

            content = clean_content(
                mem.get(
                    "content",
                    ""
                )
            )

            if len(content)>800:

                content = (
                    content[:400]
                    +
                    "\n...[省略]...\n"
                    +
                    content[-400:]
                )


            lines.append(
                f"[{idx}] {role}: {content}"
            )


        return "\n".join(lines)



    def build_prompt(
        self,
        memories
    ):


        chat=self._format_memories(
            memories
        )


        return f"""

你是浅雾羽依成长系统的事件提取器。

任务：

从聊天记录中提取真实发生的成长事件。


不要总结。
不要评价。
不要编造。


只有以下事件可以提取：

- 羽依第一次启动/唤醒
- 配置完成
- 用户表达重要情感
- 长期陪伴约定
- 用户创造相关内容
- 明确偏好形成


普通聊天不要提取。


event_type只能：

relationship
milestone
creation
identity
preference
conversation



必须严格输出：

{{
"events":[
{{
"event":"事件名称",
"topic":"事件主题",
"event_type":"类型",
"evidence":[
{{
"text":"原文",
"role":"user 或 assistant",
"source_index":数字
}}
]
}}
]
}}



聊天：

{chat}


只输出JSON。

"""




    def _extract_json(
        self,
        text
    ):

        start=text.find("{")
        end=text.rfind("}")

        if start==-1 or end==-1:
            return None

        return text[start:end+1]



    def parse_result(
        self,
        result,
        memories
    ):


        try:

            json_text=self._extract_json(
                result
            )

            data=json.loads(
                json_text
            )

        except Exception as e:

            print(
                "⚠️JSON解析失败:",
                e
            )

            return []


        output=[]


        for event in data.get(
            "events",
            []
        ):


            # =========================
            # 兼容旧模型输出
            # =========================

            if not event.get(
                "event"
            ):

                event["event"] = event.get(
                    "description",
                    "未知事件"
                )


            if not event.get(
                "topic"
            ):

                event["topic"] = event.get(
                    "description",
                    event["event"]
                )



            source_ids=[]

            evidence=[]


            for ev in event.get(
                "evidence",
                []
            ):


                idx=ev.get(
                    "source_index"
                )


                if idx is None:
                    continue


                if idx>=len(memories):
                    continue



                mem=memories[idx]


                mem_id=mem.get(
                    "id"
                )


                if not mem_id:

                    raw=(
                        mem.get(
                            "content",
                            ""
                        )
                    )


                    mem_id=(
                        "mem_"
                        +
                        hashlib.md5(
                            raw.encode(
                                "utf-8"
                            )
                        )
                        .hexdigest()[:12]
                    )



                evidence.append(
                    {
                        "text":
                            mem.get(
                                "content",
                                ""
                            ),

                        "role":
                            mem.get(
                                "role",
                                "assistant"
                            ),

                        "source_index":
                            idx,

                        "memory_id":
                            mem_id
                    }
                )


                source_ids.append(
                    mem_id
                )



            if not source_ids:
                continue



            event["evidence"]=evidence

            event["source_ids"]=list(
                set(source_ids)
            )


            output.append(
                event
            )


        return output




    def extract(
        self,
        limit=None
    ):


        memories=self.get_unprocessed_memories(
            limit
        )


        if not memories:

            return []


        print(
            f"📂正在处理 {len(memories)} 条未整理记忆..."
        )


        prompt=self.build_prompt(
            memories
        )


        print(
            f"📝 Prompt长度:{len(prompt)}"
        )


        result=self.llm.generate_raw(
            prompt
        )


        print(
            "\n📝 LLM原始响应:\n",
            result
        )


        events=self.parse_result(
            result,
            memories
        )


        print(
            f"✅提取到 {len(events)} 个事件"
        )


        for e in events:

            print(
                f" - [{e.get('event_type')}] {e.get('topic')}"
            )


        return events