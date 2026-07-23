from src.response.engine import ResponseEngine
from src.memory import MemoryStore, VectorMemory, EventMemory
from src.config import get_memory_config
from src.personality.personality_controller import PersonalityController
from src.personality.relationship_state import RelationshipState
from src.growth.pipeline import GrowthPipeline


class Orchestrator:
    def __init__(self):
        self.engine = ResponseEngine()
        self.history = []
        self.history_limit = 20

        self.target_user_id = get_memory_config()["target_user_id"]

        # 记忆系统
        self.store = MemoryStore()
        self.vector = VectorMemory()

        # 人生事件记忆
        self.event_memory = EventMemory()

        # 人格控制
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

        self._init_memory_index()

    def _init_memory_index(self):
        memories = self.store.get_by_user(self.target_user_id)
        if memories:
            print(f"Loading {len(memories)} historical memories...")
            self.vector.index_memories(memories, self.target_user_id)
            # ✅ 标记索引完成
            self.vector.mark_index_complete()

    def _retrieve_chat_memories(self, user_message: str) -> list:
        return self.vector.search(user_message, top_k=5)

    def _get_life_events(self, user_message: str) -> list:
        return self.event_memory.search(user_message, limit=3)

    def _get_personality_context(self) -> dict:
        return self.personality_controller.get_personality_context()

    def process(self, user_message: str) -> str:
        # ==========================================
        # Step 1: 保存用户消息
        # ==========================================
        user_mem = self.store.add(self.target_user_id, user_message, "user")
        if user_mem:
            self.vector.add_memory(user_mem)

        # ==========================================
        # Step 2: 成长分析（用户消息 → 事件 → 人格变化）
        # ==========================================
        growth_result = self.growth_pipeline.incremental_update(user_message)

        # ==========================================
        # Step 3: 获取最新状态（已包含成长变化）
        # ==========================================
        personality_context = self._get_personality_context()
        life_events = self._get_life_events(user_message)
        chat_memories = self._retrieve_chat_memories(user_message)

        if life_events:
            print(f"🧠 人生事件召回: {len(life_events)} 条")
            for ctx in life_events:
                print(f"   - {ctx.title}: {ctx.summary[:40]}...")

        # ==========================================
        # Step 4: 生成回复
        # ==========================================
        reply = self.engine.generate(
            user_message=user_message,
            history=self.history,
            chat_memories=chat_memories,
            life_events=life_events,
            personality_context=personality_context
        )

        # ==========================================
        # Step 5: 保存羽依回复（不进入向量库）
        # ==========================================
        self.store.add(self.target_user_id, reply, "assistant")

        # ==========================================
        # Step 6: 更新关系状态（每次互动增加活动）
        # ==========================================
        self.relationship_state.update_activity(0.02)

        # ==========================================
        # Step 7: 更新工作记忆
        # ==========================================
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

    def get_personality_state(self) -> dict:
        return self.personality_controller.get_personality_context()