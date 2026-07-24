from src.response.engine import ResponseEngine
from src.memory import MemoryStore, VectorMemory, EventMemory
from src.config import get_memory_config
from src.personality.personality_controller import PersonalityController  # Deprecated compatibility
from src.personality.relationship_state import RelationshipState
from src.growth.pipeline import GrowthPipeline
from src.memory.memory_gate import MemoryGate
from src.personality.personality_prompt import PersonalityPromptFormatter


class Orchestrator:
    def __init__(self):
        self.engine = ResponseEngine()
        self.history = []
        self.history_limit = 20

        self.target_user_id = get_memory_config()["target_user_id"]

        # 记忆系统
        self.store = MemoryStore()
        self.vector = VectorMemory()
        self.memory_gate = MemoryGate()

        # 人生事件记忆
        self.event_memory = EventMemory()

        # Deprecated: 旧人格控制器，仅保留实例供可能存在的旧模块调用，不参与人格计算
        self.personality_controller = PersonalityController()

        # 关系状态
        self.relationship_state = RelationshipState()

        # 成长流水线（传入依赖）
        self.growth_pipeline = GrowthPipeline(
            event_memory=self.event_memory,
            memory_store=self.store,
            user_id=self.target_user_id,
            relationship_state=self.relationship_state
        )

        # 统一人格解析器（复用流水线内部实例，避免重复创建）
        self.personality_resolver = self.growth_pipeline.resolver

        # 人格文本格式化器
        self.personality_formatter = PersonalityPromptFormatter()

        # 当前人格缓存（调试与测试用）
        self.current_personality = None

        self._init_memory_index()

    def _init_memory_index(self):
        memories = self.store.get_by_user(self.target_user_id)
        if memories:
            print(f"Loading {len(memories)} historical memories...")
            self.vector.index_memories(memories, self.target_user_id)
            self.vector.mark_index_complete()

    def _retrieve_chat_memories(self, user_message: str) -> list:
        return self.vector.search(user_message, top_k=5)

    def _get_life_events(self, user_message: str) -> list:
        return self.event_memory.search(user_message, limit=3)

    def _get_personality_context(self, personality=None) -> dict:
        """
        返回人格上下文。
        - 生成格式化的人格文本（personality_text）
        - 同时保留关键数值字段供调试（不会进入 Prompt 链）
        """
        if personality is None:
            personality = self.personality_resolver.resolve()

        # 注入关系数据，供 PersonalityPromptFormatter 动态调整表达边界
        personality._data["familiarity"] = self.relationship_state.get_familiarity()
        personality._data["bond_strength"] = self.relationship_state.get_bond_strength()

        # 生成自然语言人格描述
        personality_text = self.personality_formatter.format(personality)

        return {
            "personality_text": personality_text,  # PromptBuilder 唯一使用的字段
            # 以下字段仅供内部调试/日志，不再注入 System Prompt
            "personality": personality.get_all(),
            "style_instruction": personality.get("behavior_text", ""),
            "compact_style": personality.get("compact_behavior", ""),
            "warmth": personality.get("warmth"),
            "shyness": personality.get("shyness"),
            "attachment_level": personality.get("attachment_level"),
            "interaction_familiarity_level": personality.get("interaction_familiarity_level"),
            "behaviors": personality.get("behaviors", {})
        }

    def get_personality_vector(self):
        return self.personality_resolver.resolve()

    def get_personality_state(self) -> dict:
        """统一人格状态接口（替代旧 Controller）"""
        return self._get_personality_context()

    def print_personality(self):
        p = self.current_personality or self.get_personality_vector()
        print("\n🧠 羽依人格")
        print("-" * 30)
        print(f"温暖: {p.get('warmth')}")
        print(f"害羞: {p.get('shyness')}")
        print(f"依恋: {p.get('attachment_level')}")
        print(f"交流熟悉度: {p.get('interaction_familiarity_level')}")
        print(f"行为摘要: {p.get('behavior_text', '')[:60]}...")

    def process(self, user_message: str) -> str:
        # Step 1: 保存原始用户消息（不向量化）
        self.store.add(self.target_user_id, user_message, "user")

        # Step 1.5: 长期记忆审核与向量化
        verified = []
        if len(user_message.strip()) >= 5:
            verified = self.memory_gate.process(user_message)

        for mem in verified:
            structured = self.store.add(
                self.target_user_id,
                mem["content"],
                "user",
                metadata={
                    **mem,
                    "memory_type": "long_term"
                }
            )
            if structured:
                self.vector.add_memory(structured)

        # Step 2: 成长分析（事件提取、成长引擎应用、关系更新）
        growth_result = self.growth_pipeline.incremental_update(user_message)

        # Step 2.5: 关系活动更新（每次互动）
        self.relationship_state.update_activity(0.02)

        # Step 3: 获取当前人格（必须在所有状态更新后重新计算，确保本次关系变化生效）
        personality = self.personality_resolver.resolve()
        self.current_personality = personality

        personality_context = self._get_personality_context(personality)
        life_events = self._get_life_events(user_message)
        chat_memories = self._retrieve_chat_memories(user_message)

        if life_events:
            print(f"🧠 人生事件召回: {len(life_events)} 条")
            for ctx in life_events:
                print(f"   - {ctx.title}: {ctx.summary[:40]}...")

        # Step 4: 生成回复
        reply = self.engine.generate(
            user_message=user_message,
            history=self.history,
            chat_memories=chat_memories,
            life_events=life_events,
            personality_context=personality_context
        )

        # Step 5: 保存助手回复（标记防止成长污染）
        self.store.add(
            self.target_user_id,
            reply,
            "assistant",
            metadata={
                "memory_type": "assistant_response",
                "ignore_growth": True
            }
        )

        # Step 6: 更新工作记忆
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": reply})

        if len(self.history) > self.history_limit * 2:
            self.history = self.history[-self.history_limit * 2:]

        return reply

    def clear_history(self):
        self.history = []

    def get_history(self) -> list:
        return self.history

    def get_memory_stats(self) -> dict:
        return {
            "total_memories": self.store.count(),
            "vector_indexed": self.vector.count(),
            "working_memory": len(self.history),
            "life_events": len(self.event_memory.get_all())
        }