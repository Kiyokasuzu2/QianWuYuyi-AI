"""
Prompt 构建器
职责：将人格文本、记忆、关系等上下文组装为 LLM 可用的 messages。
不直接理解人格对象，只拼接格式化后的文本。
"""

from datetime import datetime
from typing import Dict, List, Optional

from src.memory import MemoryFormatter
from src.utils.text import truncate


class PromptBuilder:
    def __init__(self):
        self.memory_formatter = MemoryFormatter()

    def _format_chat_memories(self, chat_memories: list) -> str:
        """格式化最近聊天记忆"""
        if not chat_memories:
            return ""

        lines = []
        for m in chat_memories[:5]:
            role = "用户" if m.get("role") == "user" else "羽依"
            content = truncate(m.get("content", ""), 120)
            lines.append(f"  {role}: {content}")

        return "【最近相关聊天】\n" + "\n".join(lines)

    def _format_personality(self, personality_context: dict) -> str:
        """
        提取人格描述文本。
        优先使用 personality_text（由 PersonalityPromptFormatter 生成），
        兼容旧字段 style_instruction。
        """
        if not personality_context:
            return ""

        personality_text = personality_context.get("personality_text", "")
        if personality_text:
            return personality_text

        # 旧格式兼容
        style = personality_context.get("style_instruction", "")
        if style:
            return f"【表达风格】\n{style}"
        return ""

    def build_messages(
        self,
        user_message: str,
        history: Optional[List[Dict]] = None,
        chat_memories: Optional[List] = None,
        life_events: Optional[List] = None,
        personality_context: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        构建完整的 messages 列表。
        
        personality_context 格式（新）:
        {
            "personality_text": "格式化后的人格描述",
            "style_instruction": "...",   // 旧字段兼容
        }
        """
        # 核心身份约束
        core_identity_text = (
            "你是浅雾羽依，一个正在成长的AI人格。\n"
            "你拥有长期稳定的性格倾向，同时会根据与使用者的互动自然演化。"
        )

        # 人格描述（由 PersonalityPromptFormatter 生成，不再硬编码）
        personality_text = self._format_personality(personality_context)

        # 人生事件
        life_events_text = ""
        if life_events:
            life_events_text = self.memory_formatter.format_for_prompt(life_events)

        # 聊天记忆
        chat_memories_text = self._format_chat_memories(chat_memories)

        # 组装 System Prompt
        system_prompt = f"""{core_identity_text}

{personality_text}

{life_events_text}

{chat_memories_text}

【核心原则】
- 真实比完美重要，不确定就说不知道，绝不编造。
- 回复自然，带有你自己的性格和温度。
- 如果用户问起过去的事情，请从你记得的重要经历中查找。
- 如果找不到相关记忆，坦诚地说"我好像还没有相关的记忆呢"。
- 不要编造记忆，不要假装记得没有发生过的事情。

当前时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}
"""

        messages = [{"role": "system", "content": system_prompt.strip()}]

        if history:
            for item in history[-20:]:
                messages.append(item)

        messages.append({"role": "user", "content": user_message})
        return messages