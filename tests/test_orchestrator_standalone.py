# test_orchestrator_standalone.py
"""
单项测试：验证 Orchestrator 核心功能
运行方式：python test_orchestrator_standalone.py
"""

import sys
import os
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_orchestrator_basic():
    """基本测试：创建 Orchestrator 实例并测试核心方法"""
    print("=" * 50)
    print("开始单项测试：Orchestrator 核心功能")
    print("=" * 50)

    try:
        # 1. 导入 Orchestrator
        print("1. 导入 Orchestrator...")
        from src.orchestrator import Orchestrator
        print("   ✅ 导入成功")

        # 2. 创建实例
        print("2. 创建 Orchestrator 实例...")
        o = Orchestrator()
        print(f"   ✅ 实例创建成功: {o}")

        # 3. 检查必需属性是否存在
        print("3. 检查必需属性...")
        required_attrs = [
            "memory_store",
            "vector_memory",
            "personality_resolver",
            "self_model_context_provider",
            "user_resolver",
            "engine",
            "runtime_context",
            "relationship_profile",
            "relationship_state",
        ]
        for attr in required_attrs:
            assert hasattr(o, attr), f"缺少属性: {attr}"
            print(f"   ✅ {attr}")

        # 4. 检查 relationship_state 方法
        print("4. 检查 relationship_state 方法...")
        assert hasattr(o.relationship_state, "recalibrate_for_testing"), "缺少 recalibrate_for_testing 方法"
        o.relationship_state.recalibrate_for_testing()
        print("   ✅ recalibrate_for_testing() 调用成功")

        assert hasattr(o.relationship_state, "get"), "缺少 get 方法"
        state = o.relationship_state.get()
        print(f"   ✅ get() 返回: {state}")

        # 5. 测试 process 方法（模拟一条消息）
        print("5. 测试 process 方法...")
        test_message = "你好，羽依！"
        print(f"   输入消息: {test_message}")
        reply = o.process(test_message)
        print(f"   回复: {reply}")
        print("   ✅ process 方法执行完成")

        # 6. 检查是否生成历史记录
        print("6. 检查历史记录...")
        assert len(o.history) > 0, "历史记录为空"
        print(f"   ✅ 历史记录条数: {len(o.history)}")
        print(f"   ✅ 最新记录: {o.history[-1] if o.history else '无'}")

        print("=" * 50)
        print("🎉 所有测试通过！Orchestrator 运行正常。")
        print("=" * 50)
        return True

    except Exception as e:
        print("=" * 50)
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        return False


def test_behavior_text_specific():
    """模拟 test_behavior_text.py 中的测试逻辑"""
    print("\n" + "=" * 50)
    print("模拟 test_behavior_text.py 测试")
    print("=" * 50)

    try:
        from src.orchestrator import Orchestrator

        o = Orchestrator()
        print("✅ Orchestrator 实例化成功")

        # 调用测试方法
        o.relationship_state.recalibrate_for_testing()
        print("✅ recalibrate_for_testing() 调用成功")

        # 生成人格
        p = o.personality_resolver.resolve()
        print(f"✅ 人格解析成功: {p}")

        # 获取关系状态
        rs = o.relationship_state.get()
        print(f"✅ relationship_state.get() 返回: {rs}")

        print("=" * 50)
        print("🎉 behavior_text 模拟测试通过！")
        print("=" * 50)
        return True

    except Exception as e:
        print(f"❌ 模拟测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行所有测试
    result1 = test_orchestrator_basic()
    result2 = test_behavior_text_specific()

    if result1 and result2:
        print("\n" + "=" * 50)
        print("✅ 所有单项测试全部通过！")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("❌ 部分测试失败，请检查上述错误信息。")
        print("=" * 50)
        sys.exit(1)