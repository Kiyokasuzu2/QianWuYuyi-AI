"""
成长流水线（GrowthPipeline）v0.6

浅雾羽依成长系统 v0.6

流程:

EventExtractor
        ↓
EventNormalizer
        ↓
EventValidator
        ↓
EventHistoryMatcher
        ↓
GrowthEvaluator  ← 新增
        ↓
GrowthEngine
        ↓
GrowthRecord  ← 新增
        ↓
RelationshipState
        ↓
PersonalityResolver

职责:
让羽依根据人生经历产生长期成长。
"""

from typing import Optional

from src.growth.event_extractor import EventExtractor
from src.growth.event_normalizer import EventNormalizer
from src.growth.event_validator import EventValidator
from src.growth.event_history_matcher import EventHistoryMatcher
from src.growth.growth_engine import GrowthEngine
from src.growth.event_identity_resolver import resolve_event_identity
from src.growth.growth_evaluator import GrowthEvaluator

from src.personality.personality_resolver import PersonalityResolver
from src.personality.relationship_state import RelationshipState


class GrowthPipeline:

    def __init__(
        self,
        event_memory=None,
        memory_store=None,
        user_id="366648462",
        relationship_state: Optional[RelationshipState] = None
    ):
        # 事件处理
        self.extractor = EventExtractor()
        self.normalizer = EventNormalizer()
        self.validator = EventValidator()
        self.matcher = EventHistoryMatcher()

        # 成长核心
        self.growth_engine = GrowthEngine()

        # 成长评估器（Phase 3.1 新增）
        self.evaluator = GrowthEvaluator()

        # 成长记录存储（Phase 3.1 新增）
        self.growth_records = []

        # 关系系统
        self.relationship_state = (
            relationship_state or RelationshipState()
        )

        # 人格系统
        self.resolver = PersonalityResolver(
            state=self.growth_engine.state,
            relationship_state=self.relationship_state
        )

        # 外部依赖
        self.store = memory_store
        self.event_memory = event_memory
        self.target_user_id = user_id

        # ===== 将 GrowthState 注入 Matcher，使其能从持久化历史中识别重复经历 =====
        self.matcher.set_growth_state(self.growth_engine.state)

    # =================================================
    # 增量成长更新（实时聊天入口）
    # =================================================
    def incremental_update(self, user_message: str):
        """
        单次聊天后的快速成长入口

        用于 Orchestrator.process()
        """
        try:
            events = self.extractor.extract_from_text(user_message)

            if not events:
                return {
                    "events": [],
                    "personality": self.resolver.resolve(),
                    "growth_records": [],
                }

            events = self.normalizer.normalize(events)
            events = self.validator.validate(events)

            if not events:
                return {
                    "events": [],
                    "personality": self.resolver.resolve(),
                    "growth_records": [],
                }

            for e in events:
                resolve_event_identity(e)

            events = self.matcher.track(events, False)

            applied = []
            new_records = []

            for event in events:
                apply_flag = event.get("metadata", {}).get("validator_apply", True)
                if not apply_flag:
                    continue

                # ---- Phase 3.1：成长资格评估 ----
                canonical_topic = event.get("canonical_topic", event.get("topic", ""))
                event_type = event.get("event_type", "")
                history_events = self.matcher.get_history(canonical_topic, event_type)

                evaluated = self.evaluator.evaluate(event, history_events)

                if evaluated.get("growth_allowed", False):
                    record = self.growth_engine.apply_evaluated(evaluated)
                    if record:
                        self.growth_records.append(record)
                        new_records.append(record)

                # 原有 GrowthState 更新逻辑保留
                result = self.growth_engine.apply(event)

                if result.get("status") == "applied":
                    if result.get("mode") == "first":
                        self._update_relationship(event)

                    applied.append({
                        **event,
                        "growth_mode": result.get("mode")
                    })

                if self.store and event.get("source_ids"):
                    try:
                        self.store.mark_processed_batch(event["source_ids"])
                    except AttributeError:
                        pass

            return {
                "events": applied,
                "personality": self.resolver.resolve(),
                "growth_records": new_records,
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"⚠️ 增量成长失败: {e}")
            return {
                "events": [],
                "personality": self.resolver.resolve(),
                "growth_records": [],
            }

    # =================================================
    # 关系更新（内部方法）
    # =================================================
    def _update_relationship(self, event):
        event_type = event.get("event_type", "")

        raw_importance = event.get("importance", 0.5)
        if isinstance(raw_importance, (list, tuple)):
            importance = float(raw_importance[0]) if len(raw_importance) > 0 else 0.5
        elif isinstance(raw_importance, (int, float)):
            importance = float(raw_importance)
        else:
            importance = 0.5

        category = event.get("category", "")
        topic = event.get("canonical_topic", event.get("topic", ""))
        event_id = event.get("event_id", "")

        if event_type == "relationship":
            self.relationship_state.update_trust(0.05 * importance)
            self.relationship_state.update_bond(0.06 * importance)
            self.relationship_state.update_familiarity(0.04 * importance)
            self.relationship_state.update_history(0.03 * importance)

        elif event_type == "commitment":
            self.relationship_state.update_trust(0.06 * importance)
            self.relationship_state.update_bond(0.08 * importance)
            self.relationship_state.update_promise(0.10 * importance)
            self.relationship_state.update_history(0.05 * importance)

        elif event_type == "milestone":
            if category == "羽依诞生阶段":
                self.relationship_state.update_bond(0.04 * importance)
                self.relationship_state.update_history(0.05 * importance)
                self.relationship_state.add_important_event({
                    "event_id": event_id,
                    "topic": topic,
                    "type": "birth"
                })

        elif event_type == "identity":
            self.relationship_state.update_history(0.02 * importance)

        if importance >= 0.85:
            self.relationship_state.add_milestone(event_id, topic)

    # =================================================
    # 完整整合（批量处理）
    # =================================================
    def run_full_consolidation(self, limit=None, force_first_run=False):
        print("📂 开始成长整理")

        try:
            events = self.extractor.extract(limit)
        except Exception as e:
            print(f"❌ 事件提取失败: {e}")
            return {
                "events": [],
                "personality": self.resolver.resolve(),
                "growth_records": [],
            }

        if not events:
            print("⚠️ 没有提取到事件")
            return {
                "events": [],
                "personality": self.resolver.resolve(),
                "growth_records": [],
            }

        print(f"📝 原始事件 {len(events)} 个")
        events = self.normalizer.normalize(events)
        print(f"🧹 标准化完成 {len(events)} 个")

        before = len(events)
        events = self.validator.validate(events)
        print(f"🔍 验证后 {len(events)} 个 (过滤 {before - len(events)} 个)")

        if not events:
            return {
                "events": [],
                "personality": self.resolver.resolve(),
                "growth_records": [],
            }

        for e in events:
            resolve_event_identity(e)

        events = self.matcher.track(events, force_first_run)

        applied = 0
        processed = []
        new_records = []

        for event in events:
            try:
                if not event.get("is_first_occurrence", True):
                    continue

                apply_flag = event.get("metadata", {}).get("validator_apply", True)
                if not apply_flag:
                    print(f"⏭️ 跳过 event {event.get('event_id', '')} (validator_apply=False)")
                    continue

                # ---- Phase 3.1：成长评估 ----
                canonical_topic = event.get("canonical_topic", event.get("topic", ""))
                event_type = event.get("event_type", "")
                history_events = self.matcher.get_history(canonical_topic, event_type)

                evaluated = self.evaluator.evaluate(event, history_events)
                if evaluated.get("growth_allowed", False):
                    record = self.growth_engine.apply_evaluated(evaluated)
                    if record:
                        self.growth_records.append(record)
                        new_records.append(record)

                result = self.growth_engine.apply(event)

                if result.get("status") == "applied":
                    applied += 1
                    processed.extend(event.get("source_ids", []))
                    self._update_relationship(event)

            except Exception as e:
                print(f"⚠️ 成长事件失败: {event.get('topic')}, {e}")

        print(f"🌱 应用成长事件 {applied} 个")
        personality = self.resolver.resolve()

        if self.store and processed:
            self.store.mark_processed_batch(processed)

        if self.event_memory:
            self.event_memory.refresh()

        return {
            "events": events,
            "personality": personality,
            "growth_records": new_records,
        }

    def get_current_personality(self):
        return self.resolver.resolve()

    @property
    def state(self):
        return self.growth_engine.state