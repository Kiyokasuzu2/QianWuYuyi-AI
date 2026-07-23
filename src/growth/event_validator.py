"""
EventValidator

浅雾羽依成长系统 v0.9

职责:

判断事件是否值得成为:

羽依人生经历


核心:

不是保存发生过的事情

而是保存:

会改变:

- 自我认知
- 与清清关系
- 性格形成
- 成长方向
- 重要回忆

的事件

"""

from typing import List, Dict


# =========================================
# 明确无价值事件
# =========================================


IGNORE_KEYWORDS=[
    "你好",
    "在吗",
    "早上好",
    "晚上好",
    "晚安",
    "测试",
    "test"
]

# =========================================
# 技术事件
# =========================================

TECH_KEYWORDS=[
    "安装",
    "配置",
    "部署",
    "报错",
    "日志",
    "代码",
    "插件",
    "运行"
]

# =========================================
# 人生意义白名单
# =========================================

LIFE_MEANINGS=[
    "birth",
    "identity_creation",
    "relationship_start",
    "promise",
    "growth_support",
    "companionship"
]


class EventValidator:

    def validate(self, events:List[Dict]):
        """
        Validate a list of events. Returns events that are either 'keep' or 'review'.
        Each event will be annotated with metadata.validator_decision and metadata.validator_score.
        """
        result=[]
        for event in events:
            keep = self.should_keep(event)
            if keep:
                result.append(event)
        return result

    def build_text(self, event):
        return (
            event.get("topic", "") +
            event.get("canonical_topic", "")
        ).lower()

    def has_evidence(self, event):
        return len(event.get("evidence", []))>0

    def evidence_score(self, event):
        score=0
        evidence=event.get("evidence", [])
        roles=[ x.get("role") for x in evidence ]
        if "user" in roles:
            score+=0.3
        if "assistant" in roles:
            score+=0.3
        if len(evidence)>=2:
            score+=0.2
        if event.get("topic"):
            score+=0.2
        return score

    def is_technical(self, event):
        text=self.build_text(event)
        for word in TECH_KEYWORDS:
            if word in text:
                return True
        return False

    def technical_has_life(self, event):
        text=self.build_text(event)
        keywords=["羽依","第一次","诞生","启动","唤醒","人格","身份"]
        return any(x in text for x in keywords)

    def life_value(self, event):
        score=0
        meaning=event.get("category_id", "")
        if meaning in LIFE_MEANINGS:
            score+=0.6
        importance=event.get("importance", 0)
        score+=importance*0.2
        score+=self.evidence_score(event)
        text=self.build_text(event)
        if any(x in text for x in ["第一次","首次","初次"]):
            score+=0.2
        return min(score, 1.0)

    def decide(self, event):
        """
        Return (decision, score, reason)
        decision in {"keep","review","discard"}
        """
        text = self.build_text(event)

        # no evidence -> discard
        if not self.has_evidence(event):
            return "discard", 0.0, "no_evidence"

        # ignore greetings
        for word in IGNORE_KEYWORDS:
            if word in text:
                return "discard", 0.0, "ignore_keyword"

        # technical events
        if self.is_technical(event):
            if self.technical_has_life(event):
                score = self.life_value(event)
                return "keep", score, "technical_with_life"
            return "discard", 0.0, "technical"

        # life scoring
        score = self.life_value(event)
        # thresholds: >=0.65 keep, >=0.45 review, else discard
        if score >= 0.65:
            return "keep", score, "life_value_high"
        if score >= 0.45:
            return "review", score, "life_value_borderline"
        return "discard", score, "life_value_low"

    def should_keep(self, event:Dict):
        # compute decision and annotate event.metadata
        decision, score, reason = self.decide(event)
        meta = event.get("metadata")
        if not isinstance(meta, dict):
            meta = {}
        meta["validator_decision"] = decision
        meta["validator_score"] = round(float(score), 4)
        meta["validator_reason"] = reason
        # set validator_apply per policy: keep -> True; review/discard -> False
        meta["validator_apply"] = True if decision == "keep" else False
        event["metadata"] = meta

        if decision == "keep":
            print(f"🌱人生经历:{self.build_text(event)} 价值:{score} 原因:{reason}")
            return True
        if decision == "review":
            print(f"🔍待审核事件:{self.build_text(event)} 价值:{score} 原因:{reason}")
            return True
        print(f"🗑️丢弃事件:{self.build_text(event)} 价值:{score} 原因:{reason}")
        return False
