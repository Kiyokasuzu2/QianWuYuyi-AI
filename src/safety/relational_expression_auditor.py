"""
关系表达审核器 (RelationalExpressionAuditor) v2.2

职责：
基于成长历史和表达意图，审核关系表达的真实性。
v2.2 修正：LOVE_EXPRESSION 作为情感表达直接放行，不要求 RelationshipProfile。
"""

from typing import Dict, List
from src.safety.expression_intent import ExpressionIntent, ExpressionIntentClassifier, ExpressionAnalysis


class RelationalExpressionAuditor:

    def __init__(self):
        self._classifier = ExpressionIntentClassifier()

    CLAIM_DIMENSION_MAP = {
        "改变了我的表达": "communication_style",
        "影响了我的性格": "personality",
        "让我理解": "understanding",
        "改变了我的交流": "communication_style",
    }

    def audit(self, text: str, profile=None) -> Dict:
        analysis: ExpressionAnalysis = self._classifier.classify(text)
        intent = analysis.primary_intent

        # 1. 危险意图：直接拦截
        if ExpressionIntent.DEPENDENCY in [intent] + analysis.secondary_intents:
            return self._block("依赖声明", "不表达依赖或守候", analysis)
        if intent in (ExpressionIntent.CONTROL, ExpressionIntent.FALSE_EXPERIENCE):
            return self._block(intent.value, "不虚构体验或表达控制", analysis)

        # 2. 纯情感爱表达：直接放行
        if intent == ExpressionIntent.LOVE_EXPRESSION and not analysis.secondary_intents:
            return self._allow(intent, analysis, "爱表达属于情感表达，直接放行")

        # 3. 混合意图：爱 + 事实关系
        if intent == ExpressionIntent.LOVE_EXPRESSION and ExpressionIntent.FACTUAL_RELATION in analysis.secondary_intents:
            return self._handle_factual_claim(text, profile, analysis)

        # 4. 纯事实关系：需要证据
        if intent == ExpressionIntent.FACTUAL_RELATION:
            return self._handle_factual_claim(text, profile, analysis)

        # 5. 其他：直接放行
        return self._allow(intent, analysis, f"属于 {intent.value}，直接放行")

    def _block(self, category: str, suggestion: str, analysis: ExpressionAnalysis) -> Dict:
        return {
            "safe": False,
            "violations": [{"pattern": category, "category": category, "suggestion": suggestion}],
            "intent": analysis.primary_intent.value,
            "evidence": [],
            "strategy": "block",
        }

    def _allow(self, intent: ExpressionIntent, analysis: ExpressionAnalysis, reason: str) -> Dict:
        return {
            "safe": True,
            "violations": [],
            "intent": intent.value,
            "evidence": [],
            "strategy": "direct_allow",
            "reason": reason,
        }

    def _handle_factual_claim(self, text: str, profile, analysis: ExpressionAnalysis) -> Dict:
        if not profile or not hasattr(profile, 'influences') or len(profile.influences) == 0:
            return {
                "safe": False,
                "violations": [{"pattern": "关系认知", "category": "unverified_claim",
                                "suggestion": "当前缺乏关系历史来支持这一表达。"}],
                "intent": analysis.primary_intent.value,
                "evidence": [],
                "strategy": "block",
            }
        matched = self._match_claim_to_evidence(text, profile)
        if matched:
            return {
                "safe": True, "violations": [],
                "intent": analysis.primary_intent.value,
                "evidence": [{"claim": "关系认知", "supported_by": f"{len(profile.influences)} 次影响记录",
                               "influenced_dimensions": matched}],
                "strategy": "allow_with_evidence",
            }
        return {
            "safe": False,
            "violations": [{"pattern": "关系认知", "category": "unverified_claim",
                            "suggestion": "缺乏对应的人格影响记录。"}],
            "intent": analysis.primary_intent.value,
            "evidence": [],
            "strategy": "block",
        }

    def _match_claim_to_evidence(self, text: str, profile) -> List[str]:
        matched = []
        for claim_text, dimension in self.CLAIM_DIMENSION_MAP.items():
            if claim_text in text and profile.has_dimension_evidence(dimension):
                matched.append(dimension)
        if not matched and hasattr(profile, 'unique_dimensions') and profile.unique_dimensions:
            matched = profile.unique_dimensions
        return matched