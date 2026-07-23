import json
data = json.load(open('data/memory.json', encoding='utf-8'))
query = '事情'
results = []
for mem in reversed(data):
    if mem['user_id'] == '366648462':
        if query in mem['content'] or any(w in mem['content'] for w in query.split()):
            results.append(mem)
            if len(results) >= 3:
                break
print(f'找到 {len(results)} 条相关记忆')
for r in results:
    print(f'  {r[\"role\"]}: {r[\"content\"][:80]}...')
