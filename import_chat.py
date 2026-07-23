import json
import csv
from pathlib import Path

# 读取 CSV
chat_file = Path("data/chat_all.csv")
memory_file = Path("data/memory.json")

messages = []

if chat_file.exists():
    with open(chat_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # 跳过表头
        for row in reader:
            if len(row) == 2 and row[0] in ["user", "assistant"]:
                messages.append({
                    "user_id": "366648462",
                    "role": row[0],
                    "content": row[1],
                    "timestamp": "2026-07-16T13:37:00"
                })

# 读取已有的 memory.json（如果存在）
if memory_file.exists():
    with open(memory_file, "r", encoding="utf-8") as f:
        existing = json.load(f)
else:
    existing = []

# 合并（去重：避免重复导入相同的消息）
# 简单去重：比较 role 和 content
existing_contents = {(m["role"], m["content"]) for m in existing}
new_messages = [m for m in messages if (m["role"], m["content"]) not in existing_contents]

existing.extend(new_messages)

# 保存
with open(memory_file, "w", encoding="utf-8") as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)

print(f"✅ 成功导入 {len(new_messages)} 条新历史消息")
print(f"📊 memory.json 中共有 {len(existing)} 条记忆")