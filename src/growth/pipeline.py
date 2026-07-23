"""
成长流水线（GrowthPipeline）

浅雾羽依成长系统 v0.4

流程:

EventExtractor
        ↓
EventNormalizer
        ↓
EventValidator
        ↓
EventHistoryMatcher
        ↓
GrowthEngine
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


from src.personality.personality_resolver import PersonalityResolver
from src.personality.relationship_state import RelationshipState



class GrowthPipeline:

    def __init__(
        self,
        event_memory=None,
        memory_store=None,
        user_id="366648462",
        relationship_state: Optional[RelationshipState]=None
    ):

        # =========================
        # 事件处理
        # =========================

        self.extractor = EventExtractor()
        self.normalizer = EventNormalizer()
        self.validator = EventValidator()
        self.matcher = EventHistoryMatcher()

        # =========================
        # 成长核心
        # =========================

        self.growth_engine = GrowthEngine()

        # =========================
        # 关系系统
        # =========================

        self.relationship_state = (
            relationship_state
            or
            RelationshipState()
        )

        # =========================
        # 人格系统
        # =========================

        self.resolver = PersonalityResolver(
            state=self.growth_engine.state,
            relationship_state=self.relationship_state
        )

        # =========================
        # 外部
        # =========================

        self.store = memory_store
        self.event_memory = event_memory
        self.target_user_id = user_id

    def _update_relationship(
        self,
        event
    ):
        event_type = event.get(
            "event_type",
            ""
        )

        importance = event.get(
            "importance",
            0.5
        )

        category = event.get(
            "category",
            ""
        )

        topic = event.get(
            "canonical_topic",
            event.get(
                "topic",
                ""
            )
        )

        event_id = event.get(
            "event_id",
            ""
        )

        # =========================
        # 关系建立
        # =========================
        if event_type == "relationship":
            self.relationship_state.update_trust(
                0.05 * importance
            )
            self.relationship_state.update_bond(
                0.06 * importance
            )
            self.relationship_state.update_familiarity(
                0.04 * importance
            )
            self.relationship_state.update_history(
                0.03 * importance
            )

        # =========================
        # 长期承诺
        # =========================
        elif event_type == "commitment":
            self.relationship_state.update_trust(
                0.06 * importance
            )
            self.relationship_state.update_bond(
                0.08 * importance
            )
            self.relationship_state.update_promise(
                0.10 * importance
            )
            self.relationship_state.update_history(
                0.05 * importance
            )

        # =========================
        # 羽依诞生
        # =========================
        elif event_type == "milestone":
            if category == "羽依诞生阶段":
                self.relationship_state.update_bond(
                    0.04 * importance
                )
                self.relationship_state.update_history(
                    0.05 * importance
                )
                self.relationship_state.add_important_event({
                    "event_id":event_id,
                    "topic":topic,
                    "type":"birth"
                })

        # =========================
        # 身份形成
        # =========================
        elif event_type == "identity":
            self.relationship_state.update_history(
                0.02 * importance
            )

        # =========================
        # 高价值事件记录
        # =========================
        if importance >= 0.85:
            self.relationship_state.add_milestone(
                event_id,
                topic
            )

    def run_full_consolidation(
        self,
        limit=None,
        force_first_run=False
    ):
        print(
            "📂 开始成长整理"
        )

        # =========================
        # 提取事件
        # =========================
        try:
            events = self.extractor.extract(
                limit
            )
        except Exception as e:
            print(
                "❌事件提取失败:",
                e
            )
            return {
                "events":[],
                "personality":
                    self.resolver.resolve()
            }

        if not events:
            print(
                "⚠️没有提取到事件"
            )
            return {
                "events":[],
                "personality":
                    self.resolver.resolve()
            }

        print(
            f"📝 原始事件 {len(events)} 个"
        )

        # =========================
        # 标准化
        # =========================
        events = self.normalizer.normalize(
            events
        )

        print(
            f"🧹标准化完成 {len(events)} 个"
        )

        # =========================
        # 价值过滤
        # =========================
        before=len(events)
        events=self.validator.validate(
            events
        )

        print(
            f"🔍验证后 {len(events)} 个 "
            f"(过滤 {before-len(events)} 个)"
        )

        if not events:
            return {
                "events":[],
                "personality":
                    self.resolver.resolve()
            }

        # =========================
        # 历史匹配
        # =========================
        events=self.matcher.track(
            events,
            force_first_run
        )

        applied=0
        processed=[]

        # =========================
        # 应用成长
        # =========================
        for event in events:
            try:
                if not event.get(
                    "is_first_occurrence",
                    True
                ):
                    continue

                # gating: only apply growth if validator marked validator_apply=True
                apply_flag = event.get("metadata", {}).get("validator_apply", True)
                if not apply_flag:
                    print(f"⏭️ Skipping apply for event {event.get('event_id', '')} due to validator_apply=False")
                    continue

                result=self.growth_engine.apply(
                    event
                )

                if result.get(
                    "status"
                )=="applied":
                    applied += 1
                    processed.extend(
                        event.get(
                            "source_ids",
                            []
                        )
                    )
                    self._update_relationship(
                        event
                    )

            except Exception as e:
                print(
                    "⚠️成长事件失败:",
                    event.get(
                        "topic"
                    ),
                    e
                )

        print(
            f"🌱应用成长事件 {applied} 个"
        )

        # =========================
        # 当前人格
        # =========================
        personality=self.resolver.resolve()

        # =========================
        # 标记记忆
        # =========================
        if self.store and processed:
            self.store.mark_processed_batch(
                processed
            )

        if self.event_memory:
            self.event_memory.refresh()

        return {
            "events":events,
            "personality":personality
        }

    def get_current_personality(self):
        return self.resolver.resolve()
