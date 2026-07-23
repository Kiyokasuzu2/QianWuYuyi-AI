# src/core.py
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到sys.path
sys.path.append(str(Path(__file__).parent.parent))

from openai import OpenAI
from src.config_loader import CONFIG
from src.memory import MemorySystem

class YuyiCore:
    def __init__(self):
        self.memory = MemorySystem()
        self.client = OpenAI(
            api_key=CONFIG["llm"]["api_key"],
            base_url=CONFIG["llm"]["api_base"]
        )
        self.model = CONFIG["llm"]["model"]
        self.temperature = CONFIG["llm"]["temperature"]
        self.max_tokens = CONFIG["llm"]["max_tokens"]
        
        # 加载人格文档作为System Prompt基底
        self.persona_base = self._load_persona()
        
        # 当前用户ID（终端模拟时固定为 "terminal_user"）
        self.current_user = "terminal_user"
        
    def _load_persona(self):
        """加载 docs/ 下的核心人格文档"""
        docs_dir = Path(__file__).parent.parent / "docs"
        persona_files = ["persona.txt", "identity.txt", "communication.txt"]
        content = ""
        for fname in persona_files:
            fpath = docs_dir / fname
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as f:
                    content += f.read() + "\n\n"
        return content.strip()
        
    def _build_system_prompt(self, user_id: str, query: str):
        """构建完整的系统提示词，注入记忆和成长信息"""
        # 1. 检索相关长期记忆
        memories = self.memory.search(user_id, query, top_k=3)
        memory_text = ""
        if memories:
            memory_text = "\n【羽依记得的相关经历】\n"
            for m in memories:
                memory_text += f"- [{m['role']}] {m['content']}\n"
        else:
            memory_text = "\n【关于这件事，羽依还没有相关记忆。】\n"
            
        # 2. 获取短期对话历史
        recent = self.memory.get_recent(user_id, limit=5)
        history_text = ""
        if recent:
            history_text = "\n【最近对话】\n"
            for r in recent:
                history_text += f"{r['role']}: {r['content']}\n"
                
        # 3. 构建完整System Prompt
        sys_prompt = f"""
{self.persona_base}

【当前时间】{datetime.now().strftime("%Y-%m-%d %H:%M")}
【当前用户】terminal_user

{memory_text}
{history_text}

【核心行为原则】
1. 真实优先：不确定就说"我不太确定"，不编造。
2. 不伪装记忆：如果没有相关记忆，直接说明。
3. 自然交流：日常简短，复杂问题展开。
4. 尊重边界：不武断猜测对方情绪。

请根据以上信息，以浅雾羽依的身份回复用户。
"""
        return sys_prompt
        
    def _should_memorize(self, user_id: str, content: str) -> bool:
        """
        判断是否应该写入长期记忆（解决“什么时候记忆”）
        规则：长度>30字 或 包含第一人称 或 包含情绪词
        """
        if len(content) > 30:
            return True
        # 简单情绪词检测
        emotion_words = ["开心", "难过", "累", "烦", "喜欢", "讨厌", "害怕", "担心", "期待", "希望", "失望", "孤独"]
        if any(w in content for w in emotion_words):
            return True
        # 第一人称
        if "我" in content or "我们" in content:
            return True
        return False
        
    def _check_growth_trigger(self, user_id: str, query: str) -> bool:
        """
        检测是否触发成长反思（解决“什么经历会改变她”）
        简易版：检测query中是否包含重复话题关键词
        实际生产需配合历史统计
        """
        # 获取最近10条该用户记忆
        recent = self.memory.get_recent(user_id, limit=10)
        if len(recent) < 3:
            return False
            
        # 简单重复话题检测：提取query关键词，对比近期内容
        # 此处简化，只要包含“记得吗”“变了”“成长”等词即触发
        trigger_words = ["记得吗", "变了", "成长", "以前", "改变", "不同了"]
        if any(w in query for w in trigger_words):
            return True
        return False
        
    def chat(self, user_message: str) -> str:
        """处理用户消息，返回羽依回复"""
        user_id = self.current_user
        
        # 1. 构建系统提示词
        system_prompt = self._build_system_prompt(user_id, user_message)
        
        # 2. 调用LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"抱歉，我刚刚思考时出了点问题。错误：{str(e)}"
            
        # 3. 记忆写入（记忆用户消息 + 羽依回复）
        # 用户消息判断是否写入长期
        if self._should_memorize(user_id, user_message):
            self.memory.add(
                user_id=user_id,
                content=f"用户说：{user_message}",
                role="user",
                metadata={"trigger": "auto"}
            )
        # 羽依的回复总是写入（但也可以选择性，这里默认写入）
        self.memory.add(
            user_id=user_id,
            content=f"羽依回复：{reply}",
            role="yuyi",
            metadata={"response_to": user_message[:20]}
        )
        
        # 4. 成长触发检测（简易）
        if self._check_growth_trigger(user_id, user_message):
            # 触发成长：记录到日志（未来可扩展为自动反思）
            growth_log = Path(__file__).parent.parent / "data" / "growth_log.txt"
            growth_log.parent.mkdir(exist_ok=True)
            with open(growth_log, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().isoformat()}] 成长触发: {user_message}\n")
                f.write(f"回复: {reply}\n\n")
                
        return reply