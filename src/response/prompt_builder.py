from datetime import datetime
from src.core.persona import Persona
from src.memory import MemoryFormatter
from src.emotion.emotion_state import EmotionState
from src.personality.relationship_state import RelationshipState
from src.personality.core_identity import CoreIdentity
from src.personality.personality_controller import PersonalityController
from src.utils.text import truncate


class PromptBuilder:
    def __init__(self):
        self.persona = Persona()
        self.memory_formatter = MemoryFormatter()
        self.emotion_state = EmotionState()
        self.relationship_state = RelationshipState()
        self.personality_controller = PersonalityController()

    def _format_chat_memories(self, chat_memories: list) -> str:
        if not chat_memories:
            return ""

        lines = []
        for m in chat_memories[:5]:
            role = "用户" if m.get("role") == "user" else "羽依"
            content = truncate(m.get("content", ""), 120)
            lines.append(f"  {role}: {content}")

        return "【最近相关聊天】\n" + "\n".join(lines)

    def _format_personality(self, personality_context: dict) -> str:
        if not personality_context:
            return ""

        style = personality_context.get("style_instruction", "")
        if style:
            return f"\n{style}"
        return ""

    def _format_emotion(self) -> str:
        return f"\n{self.emotion_state.to_prompt_text(influence=0.3)}"

    def _format_relationship(self) -> str:
        return f"\n{self.relationship_state.to_prompt_text()}"

    def _format_core_identity(self) -> str:
        return CoreIdentity.get_prompt_constraint()

    def build_messages(
        self,
        user_message: str,
        history: list = None,
        chat_memories: list = None,
        life_events: list = None,
        personality_context: dict = None
    ) -> list:
        # ✅ 1. 核心身份锁（最高优先级）
        core_identity_text = self._format_core_identity()

        # 2. 人格底色
        persona_text = self.persona.load()

        # 3. 人生事件（共同经历）
        life_events_text = ""
        if life_events:
            life_events_text = self.memory_formatter.format_for_prompt(life_events)

        # 4. 人格行为（成长后的行为倾向）
        personality_text = self._format_personality(personality_context)

        # 5. 关系状态
        relationship_text = self._format_relationship()

        # 6. 当前情绪（短期状态）
        emotion_text = self._format_emotion()

        # 7. 最近聊天记忆
        chat_memories_text = self._format_chat_memories(chat_memories)

        system_prompt = f"""{core_identity_text}

{persona_text}

{life_events_text}

{personality_text}

{relationship_text}

{emotion_text}

{chat_memories_text}

【核心原则】
- 真实比完美重要，不确定就说不知道，绝不编造。
- 回复自然，带有你自己的性格和温度。
- 如果用户问起过去的事情，请从【你记得的重要经历】中查找。
- 如果找不到相关记忆，坦诚地说"我好像还没有相关的记忆呢"。
- 不要编造记忆，不要假装记得没有发生过的事情。
- 当前情绪只会轻微影响表达方式，不会改变你的核心人格。

当前时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}
"""

        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for item in history[-20:]:
                messages.append(item)

        messages.append({"role": "user", "content": user_message})
        return messages