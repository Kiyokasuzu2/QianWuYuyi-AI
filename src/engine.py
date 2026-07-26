import os
from openai import OpenAI

class ResponseEngine:
    def __init__(self):
        # 请将 "你的DeepSeek API Key" 替换为真实的 API Key
        self.api_key = os.getenv("DEEPSEEK_API_KEY", )
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com/v1")
        self.model = "deepseek-v4-pro"

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
        # 构建系统提示
        system_parts = []
        if personality_context:
            system_parts.append(f"人格：{personality_context}")
        if emotion_context and emotion_context.get("dominant"):
            system_parts.append(f"情绪：{emotion_context.get('dominant')}")
        if context_prompt_blocks:
            for block in context_prompt_blocks:
                if block.get("role") == "system":
                    system_parts.append(block.get("content", ""))
        system_prompt = "\n\n".join(system_parts) if system_parts else "你是浅雾羽依，一个温柔、害羞但正在成长的AI个体。"

        # 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history[-20:]:  # 最近10轮
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        # 调用 DeepSeek
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[DeepSeek] 调用失败: {e}")
            return f"抱歉，我遇到了一点问题：{str(e)}"
