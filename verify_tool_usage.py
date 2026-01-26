import ast
import json
import os

# 자동 도구 파싱 및 검증 함수
def parse_and_verify_tools(result_entry):
    code = result_entry.get('code', '')
    tools = result_entry.get('tools', [])
    used_tools = set()
    if not code:
        return False, [], tools
    try:
        tree = ast.parse(code)
        # import된 모듈
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    used_tools.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    used_tools.add(node.module.split('.')[0])
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_tools.add(node.value.id)
    except Exception as e:
        return False, [], tools
    # 요구 도구와 실제 사용 도구 비교
    required = set(t.split('.')[0] for t in tools)
    used = used_tools
    missing = required - used
    return len(missing) == 0, list(missing), list(used)

def verify_all_results(results_path):
    with open(results_path, encoding='utf-8') as f:
        results = json.load(f)
    for i, entry in enumerate(results):
        ok, missing, used = parse_and_verify_tools(entry)
        print(f"[문제 {i+1}] 요구 도구: {entry.get('tools', [])}")
        print(f"  코드 내 사용 도구: {used}")
        if ok:
            print("  ✅ 모든 요구 도구가 코드에서 사용됨")
        else:
            print(f"  ⚠️  미사용 도구: {missing}")
            # 콜백: 추가 도구 사용 요청
            if missing:
                print(f"  → LLM에 다음 도구 사용을 명시적으로 요청하세요: {missing}")

if __name__ == '__main__':
    verify_all_results('mcp_results.json')
