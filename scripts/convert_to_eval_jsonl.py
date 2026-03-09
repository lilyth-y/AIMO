import json

# mcp_results.json을 평가용 JSONL로 변환
with open('mcp_results.json', encoding='utf-8') as f:
    data = json.load(f)

with open('eval_data.jsonl', 'w', encoding='utf-8') as f:
    for entry in data:
        # 평가에 필요한 주요 필드만 추출
        out = {
            'query': entry['problem']['description'],
            'response': entry.get('code', ''),
            'reasoning_steps': entry.get('reasoning_steps', []),
            'result': entry.get('result', {}),
            'tools': entry.get('tools', []),
            'type': entry.get('type', '')
        }
        f.write(json.dumps(out, ensure_ascii=False) + '\n')
print('✅ eval_data.jsonl 변환 완료')
