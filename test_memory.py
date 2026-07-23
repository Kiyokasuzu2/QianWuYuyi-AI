import json
from pathlib import Path


MEMORY_FILE = Path("data/memory.json")


def load_memory():
    """加载记忆数据"""
    assert MEMORY_FILE.exists(), f"找不到记忆文件: {MEMORY_FILE}"

    with MEMORY_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    assert isinstance(data, list), "memory.json 必须是列表结构"

    return data


def search_memory(data, query, user_id=None, limit=3):
    """
    简单记忆搜索

    参数:
        data: 记忆列表
        query: 搜索关键词
        user_id: 用户过滤
        limit: 返回数量
    """

    results = []

    for mem in reversed(data):

        if user_id and mem.get("user_id") != user_id:
            continue

        content = mem.get("content", "")

        if (
            query in content
            or any(
                word in content
                for word in query.split()
            )
        ):
            results.append(mem)

            if len(results) >= limit:
                break

    return results


def test_memory_file_load():
    """
    测试记忆文件可以正常读取
    """

    data = load_memory()

    assert len(data) >= 0


def test_memory_search():
    """
    测试基础记忆检索
    """

    data = load_memory()

    results = search_memory(
        data,
        query="事情",
        limit=3
    )

    assert isinstance(results, list)

    print(
        f"找到 {len(results)} 条相关记忆"
    )

    for item in results:
        print(
            f'  {item.get("role", "unknown")}: '
            f'{item.get("content", "")[:80]}...'
        )


def test_memory_structure():
    """
    测试记忆格式
    """

    data = load_memory()

    if len(data) == 0:
        return

    memory = data[0]

    assert isinstance(
        memory,
        dict
    )

    assert "content" in memory