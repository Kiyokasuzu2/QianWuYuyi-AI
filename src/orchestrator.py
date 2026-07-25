"""
Orchestrator（总调度中心）Phase 11.6 覆盖版
整合记忆、成长、人格、自我模型、情绪、安全、关系等所有子系统。
Phase 11.6 新增：UserContext + UserResolver，多用户记忆分区。
"""
from datetime import datetime
from typing import List, Dict, Optional

from src.response.engine import ResponseEngine
from src.memory import MemoryStore, VectorMemory, EventMemory
from src.config import get_memory_config
from src.personality.personality_controller import PersonalityController  # Deprecated
from src.personality.relationship_state import RelationshipState
from src.growth.pipeline import GrowthPipeline
from src.memory.memory_gate import MemoryGate
from src.personality.personality_prompt import PersonalityPromptFormatter

# Phase 7.1：关系系统
from src.relationship.relationship_influence_profile import RelationshipInfluenceProfile
from src.relationship.relationship_repository import RelationshipRepository

# Phase 7.1：安全系统
from src.safety.expression_verifier import ExpressionVerifier

# Phase 6：人格决策组件
from src.personality.value_system import ValueSystem
from src.personality.identity_resolver import IdentityResolver
from src.personality.behavior_engine import BehaviorEngine
from src.personality.conflict_resolver import ConflictResolver
from src.personality.self_model_builder import SelfModelBuilder

# Phase 7.4：关系表达约束
from src.safety.constraint_resolver import ConstraintResolver
from src.safety.relationship_expression_policy import RelationshipExpressionPolicy
from src.safety.claim_strength_evaluator import ClaimStrength

# Phase 8.4：自我模型上下文
from src.personality.self_model_store import SelfModelStore
from src.personality.self_model_context_provider import SelfModelContextProvider

# Phase 9.7：情绪系统完整集成
from src.emotion.emotion_manager import EmotionManager
from src.emotion.emotion_repository import EmotionRepository
from src.emotion.emotion_trace_repository import EmotionTraceRepository
from src.emotion.emotion_event_detector import EmotionEventDetector
from src.emotion.emotion_growth_service import EmotionGrowthService

# Phase 10.7：关系上下文
from src.relationship.relationship_context_provider import RelationshipContextProvider

# Phase 11.6：用户上下文与记忆分区
from src.identity.user_context import UserContext
from src.identity.user_resolver import UserResolver


class Orchestrator:
    def __init__(self):
        self.engine = ResponseEngine()
        self.history = []
        self.history_limit = 20

        # Phase 11.6：创建用户上下文
        self.user_resolver = UserResolver()
        self.user_context = self.user_resolver.resolve()
        self.target_user_id = self.user_context.user_id

        # 记忆系统（使用 UserContext 分区，通过新版 MemoryStore 支持）
        self.store = MemoryStore(self.user_context)
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
        self.relationship_repository = RelationshipRepository(
            data_dir="data",
            user_id=self.target_user_id
        )
        loaded_profile = self.relationship_repository.load()
        if loaded_profile:
            self.relationship_profile = loaded_profile
        else:
            self.relationship_profile = RelationshipInfluenceProfile(
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

        # Phase 8.4：自我模型上下文
        self.self_model_store = SelfModelStore()
        self.self_model_context_provider = SelfModelContextProvider(self.self_model_store)

        # Phase 9.7：情绪系统完整集成
        self.emotion_detector = EmotionEventDetector()
        self.emotion_manager = EmotionManager(
            EmotionRepository("data/emotion_state.json"),
            EmotionTraceRepository("data/emotional_traces.json"),
            counter_file="data/emotion_analysis_counter.json"
        )
        self.emotion_growth_service = EmotionGrowthService(
            manager=self.emotion_manager,
            self_model_store=self.self_model_store,
            analysis_interval=10
        )

        # Phase 10.7：关系上下文提供器
        self.relationship_context_provider = RelationshipContextProvider()

        self._init_memory_index()

    def _init_memory_index(self):
        memories = self.store.load()
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
        memory_entry = {
            "content": user_message,
            "role": "user",
            "user_id": self.target_user_id,
            "metadata": {"memory_type": "short_term"},
        }
        self.store.add(memory_entry)

        # Step 1.5: 长期记忆审核与向量化
        verified = []
        if len(user_message.strip()) >= 5:
            verified = self.memory_gate.process(user_message)
        for mem in verified:
            structured_mem = {
                "content": mem["content"],
                "role": "user",
                "user_id": self.target_user_id,
                "metadata": {**mem, "memory_type": "long_term"},
            }
            self.store.add(structured_mem)
            if structured_mem:
                self.vector.add_memory(structured_mem)

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

        # ========== Phase 9.7 情绪系统完整接入 ==========
        self.emotion_manager.update()
        emotion_event = self.emotion_detector.detect(user_message)
        if emotion_event:
            self.emotion_manager.process_event(emotion_event)
        emotion_ctx = self.emotion_manager.get_context(influence=0.3)

        # Phase 8.4：自我模型上下文
        self_model_ctx = self.self_model_context_provider.get_context()

        # ========== Phase 10.7 关系上下文 ==========
        relationship_state_v10 = self.relationship_repository.load_state()
        cognitive_profile = self.relationship_repository.load_cognitive_profile()
        relationship_ctx = self.relationship_context_provider.get_context(
            state=relationship_state_v10,
            profile=cognitive_profile,
        )

        # Step 4：生成回复
        reply = self.engine.generate(
            user_message=user_message,
            history=self.history,
            chat_memories=chat_memories,
            life_events=life_events,
            personality_context=personality_context,
            resolved_behavior=resolved_behavior_data,
            self_model_context=self_model_ctx,
            emotion_context=emotion_ctx,
            relationship_context=relationship_ctx,
        )

        # Step 4.5：表达真实性审核
        audit_result = self.expression_verifier.verify(reply, self.relationship_profile)

        expression_constraint_text = ""
        if audit_result:
            match_result = audit_result.get("match_result")
            claim_strength_str = audit_result.get("claim_strength")
            if match_result is not None and claim_strength_str is not None:
                try:
                    claim_strength = ClaimStrength(claim_strength_str)
                except ValueError:
                    claim_strength = ClaimStrength.UNSUPPORTED
                constraint = ConstraintResolver.resolve(match_result, claim_strength)
                expression_constraint_text = RelationshipExpressionPolicy.to_prompt(constraint)
            elif not audit_result.get("safe", True):
                hint = audit_result.get("violations", [{}])[0].get("suggestion", "")
                if hint:
                    expression_constraint_text = f"【表达注意】{hint}"

        if expression_constraint_text:
            reply = self.engine.generate(
                user_message=user_message,
                history=self.history,
                chat_memories=chat_memories,
                life_events=life_events,
                personality_context=personality_context,
                resolved_behavior=resolved_behavior_data,
                self_model_context=self_model_ctx,
                emotion_context=emotion_ctx,
                relationship_context=relationship_ctx,
                expression_constraint_text=expression_constraint_text,
            )

        # Step 5: 保存助手回复
        assistant_memory = {
            "content": reply,
            "role": "assistant",
            "user_id": self.target_user_id,
            "metadata": {"memory_type": "assistant_response", "ignore_growth": True},
        }
        self.store.add(assistant_memory)

        # Step 6: 更新工作记忆
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": reply})
        if len(self.history) > self.history_limit * 2:
            self.history = self.history[-self.history_limit * 2:]

        # ========== Phase 9.7 情绪成长（后台） ==========
        self.emotion_manager.increment_analysis_counter()
        if self.emotion_growth_service.should_analyze():
            self.emotion_growth_service.analyze_and_merge()

        return reply

    def clear_history(self):
        self.history = []

    def get_history(self) -> list:
        return self.history

    def get_memory_stats(self) -> dict:
        return {
            "total_memories": len(self.store.load()),
            "vector_indexed": self.vector.count(),
            "working_memory": len(self.history),
            "life_events": len(self.event_memory.get_all())
        }