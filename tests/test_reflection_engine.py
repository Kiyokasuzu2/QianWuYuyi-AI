"""
反思引擎测试 v1.1
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personality.personality_growth_record import (
    create_personality_growth_record,
    PersonalityGrowthHistory,
)
from src.personality.reflection_engine import ReflectionEngine


def test_pattern_discovery():
    """同一维度出现多次应被识别为模式"""
    history = PersonalityGrowthHistory()
    for _ in range(3):
        history.add(create_personality_growth_record(
            trigger_events=["evt_001"],
            changes={"creativity": {"before": 0.5, "after": 0.6, "delta": 0.1}},
            affected_dimensions=["creativity"],
            meaning="创造倾向增强",
            confidence=0.8,
            validation_count=2,
            growth_level="preference",
        ))
    engine = ReflectionEngine()
    result = engine.reflect(history)
    assert len(result["discovered_patterns"]) > 0
    assert any("creativity" in p for p in result["discovered_patterns"])


def test_trait_upgrade_detected():
    """满足条件的 preference 应被识别为候选"""
    history = PersonalityGrowthHistory()
    for _ in range(3):
        history.add(create_personality_growth_record(
            trigger_events=["evt_001"],
            changes={"creativity": {"before": 0.5, "after": 0.6, "delta": 0.1}},
            affected_dimensions=["creativity"],
            meaning="创造倾向增强",
            confidence=0.85,
            validation_count=2,
            growth_level="preference",
        ))
    engine = ReflectionEngine()
    result = engine.reflect(history)
    assert "creativity" in result["trait_candidates"]


def test_no_upgrade_for_low_confidence():
    """低置信度不应触发升级"""
    history = PersonalityGrowthHistory()
    for _ in range(3):
        history.add(create_personality_growth_record(
            trigger_events=["evt_001"],
            changes={"creativity": {"before": 0.5, "after": 0.6, "delta": 0.1}},
            affected_dimensions=["creativity"],
            meaning="创造倾向增强",
            confidence=0.6,
            validation_count=2,
            growth_level="preference",
        ))
    engine = ReflectionEngine()
    result = engine.reflect(history)
    assert len(result["trait_candidates"]) == 0


def test_summary_generated():
    """即使没有升级，也应生成总结"""
    history = PersonalityGrowthHistory()
    engine = ReflectionEngine()
    result = engine.reflect(history)
    assert "平稳" in result["self_summary"]


def test_conflicting_growth_not_upgrade():
    """正负变化混杂，不应升级"""
    history = PersonalityGrowthHistory()
    history.add(create_personality_growth_record(
        trigger_events=["evt_001"],
        changes={"creativity": {"before": 0.5, "after": 0.6, "delta": 0.1}},
        affected_dimensions=["creativity"],
        meaning="创造倾向增强",
        confidence=0.85,
        validation_count=2,
        growth_level="preference",
    ))
    history.add(create_personality_growth_record(
        trigger_events=["evt_002"],
        changes={"creativity": {"before": 0.6, "after": 0.5, "delta": -0.1}},
        affected_dimensions=["creativity"],
        meaning="创造倾向减弱",
        confidence=0.85,
        validation_count=2,
        growth_level="preference",
    ))
    history.add(create_personality_growth_record(
        trigger_events=["evt_003"],
        changes={"creativity": {"before": 0.5, "after": 0.52, "delta": 0.02}},
        affected_dimensions=["creativity"],
        meaning="创造倾向微弱回升",
        confidence=0.85,
        validation_count=2,
        growth_level="preference",
    ))
    engine = ReflectionEngine()
    result = engine.reflect(history)
    assert len(result["trait_candidates"]) == 0


if __name__ == "__main__":
    test_pattern_discovery()
    print("✅ 测试1通过：成长模式被发现")
    test_trait_upgrade_detected()
    print("✅ 测试2通过：特质候选被识别")
    test_no_upgrade_for_low_confidence()
    print("✅ 测试3通过：低置信度不触发")
    test_summary_generated()
    print("✅ 测试4通过：总结正常生成")
    test_conflicting_growth_not_upgrade()
    print("✅ 测试5通过：冲突变化不升级")
    print("\n🎉 全部通过")