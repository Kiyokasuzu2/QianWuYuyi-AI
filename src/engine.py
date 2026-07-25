# src/engine.py
class ResponseEngine:
    """响应引擎（占位实现）"""
    
    def generate(
        self,
        user_message: str,
        history: list,
        chat_memories: list,
        life_events: list,
        personality_context: str,
        resolved_behavior: dict,
        self_model_context: dict,
        emotion_context: dict,
        relationship_context: dict,
        context_prompt_blocks: list = None,
    ) -> str:
        """
        生成回复（简单占位）
        实际项目中可替换为调用 LLM 的逻辑
        """
        # 简单拼接一个回复（演示用）
        prompt_parts = []
        if personality_context:
            prompt_parts.append(f"人格：{personality_context}")
        if context_prompt_blocks:
            prompt_parts.append(f"系统提示：{context_prompt_blocks}")
        if emotion_context:
            prompt_parts.append(f"情绪：{emotion_context.get('dominant')}")
        if relationship_context:
            prompt_parts.append(f"关系：{relationship_context.get('trust')}")

        reply = f"（模拟回复）收到你的消息：{user_message}。上下文：{', '.join(prompt_parts) if prompt_parts else '无额外信息'}"
        return reply