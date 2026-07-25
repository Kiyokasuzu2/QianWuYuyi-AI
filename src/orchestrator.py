from src.response.engine import ResponseEngine
from src.memory import MemoryStore, VectorMemory, EventMemory
from src.config import get_memory_config
from src.personality.personality_controller import PersonalityController  # Deprecated
from src.personality.relationship_state import RelationshipState
from src.growth.pipeline import GrowthPipeline
from src.memory.memory_gate import MemoryGate
from src.personality.personality_prompt import PersonalityPromptFormatter
from datetime import datetime

# Phase 7.1：关系系统
from src.relationship.relationship_profile import RelationshipProfile
from src.relationship.relationship_repository import RelationshipRepository

# Phase 7.1：安全系统
from src.safety.expression_verifier import ExpressionVerifier

# Phase 6：人格决策组件
from src.personality.value_system import ValueSystem
from src.personality.identity_resolver import IdentityResolver
from src.personality.behavior_engine import BehaviorEngine
from src.personality.conflict_resolver import ConflictResolver
from src.personality.self_model_builder import SelfModelBuilder


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
        self.event_memory = EventMemory()

        # Deprecated
        self.personality_controller = PersonalityController()

        # 关系状态
        self.relationship_state = RelationshipState()

        # 成长流水线
        self.growth_pipeline = GrowthPipeline(
            event_memory=self.event_memory,
            memory_store=self.store,
            user_id=self.target_user_id,
            relationship_state=self.relationship_state
        )

        # 人格解析与格式化
        self.personality_resolver = self.growth_pipeline.resolver
        self.personality_formatter = PersonalityPromptFormatter()
        self.current_personality = None

        # Phase 7.1：关系画像持久化
        self.relationship_repository = RelationshipRepository()
        loaded_profile = self.relationship_repository.load(self.target_user_id)
        if loaded_profile:
            self.relationship_profile = loaded_profile
        else:
            self.relationship_profile = RelationshipProfile(
                user_id=self.target_user_id,
                relationship_start=datetime.now().isoformat()
            )

        # Phase 7.1：安全审核器
        self.expression_verifier = ExpressionVerifier()

        # Phase 6：人格决策组件
        self.value_system = ValueSystem()
        self.identity_resolver = IdentityResolver(self.value_system)
        self.behavior_engine = BehaviorEngine()
        self.conflict_resolver = ConflictResolver()
        self.self_model_builder = SelfModelBuilder()

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
        if personality is None:
            personality = self.personality_resolver.resolve()
        personality._data["familiarity"] = self.relationship_state.get_familiarity()
        personality._data["bond_strength"] = self.relationship_state.get_bond_strength()
        personality_text = self.personality_formatter.format(personality)
        return {
            "personality_text": personality_text,
            "personality": personality.get_all(),
            "style_instruction": personality.get("behavior_text", ""),
            "compact_style": personality.get("compact_behavior", ""),
            "warmth": personality.get("warmth"),
            "shyness": personality.get("shyness"),
            "attachment_level": personality.get("attachment_level"),
            "interaction_familiarity_level": personality.get("interaction_familiarity_level"),
            "behaviors": personality.get("behaviors", {}),
        }

    def get_personality_vector(self):
        return self.personality_resolver.resolve()

    def get_personality_state(self) -> dict:
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
        # Step 1: 保存用户消息
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
                metadata={**mem, "memory_type": "long_term"}
            )
            if structured:
                self.vector.add_memory(structured)

        # Step 2: 成长分析
        growth_result = self.growth_pipeline.incremental_update(user_message)
        self.relationship_state.update_activity(0.02)

        # Step 3: 获取当前人格
        personality = self.personality_resolver.resolve()
        self.current_personality = personality
        personality_context = self._get_personality_context(personality)

        # Phase 7.1：同步关系影响记录并持久化
        for influence in self.growth_pipeline.collect_new_influences():
            self.relationship_profile.add_influence(influence)
        self.relationship_repository.save(self.relationship_profile)

        # Step 3.6：构建自我模型
        trait_states = self.personality_resolver.get_trait_states()
        self_model = self.self_model_builder.build(
            history=self.growth_pipeline.growth_records,
            trait_states=trait_states
        )

        # Step 3.7：人格决策链
        snapshot = self.identity_resolver.resolve(
            self_model=self_model,
            trait_states=trait_states
        )
        behavior_profile = self.behavior_engine.analyze(snapshot)
        resolved_behavior = self.conflict_resolver.resolve(behavior_profile)
        resolved_behavior_data = (
            resolved_behavior.to_dict()
            if hasattr(resolved_behavior, "to_dict")
            else resolved_behavior
        )

        life_events = self._get_life_events(user_message)
        chat_memories = self._retrieve_chat_memories(user_message)
        if life_events:
            print(f"🧠 人生事件召回: {len(life_events)} 条")
            for ctx in life_events:
                print(f"   - {ctx.title}: {ctx.summary[:40]}...")

        # Step 4：生成回复
        reply = self.engine.generate(
            user_message=user_message,
            history=self.history,
            chat_memories=chat_memories,
            life_events=life_events,
            personality_context=personality_context,
            resolved_behavior=resolved_behavior_data
        )

        # Step 4.5：表达真实性审核
        audit_result = self.expression_verifier.verify(reply, self.relationship_profile)
        if not audit_result["safe"]:
            print(f"⚠️ 回复未通过表达审核: {audit_result['violations']}")

        # Step 5: 保存助手回复
        self.store.add(
            self.target_user_id, reply, "assistant",
            metadata={"memory_type": "assistant_response", "ignore_growth": True}
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