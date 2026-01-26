import json
from typing import List, Dict, Any
import importlib
import subprocess
import sys

# MCP context structure for each problem
class MCPContext:
    def __init__(self, problem: Dict[str, Any]):
        self.problem = problem
        self.type = self.detect_type(problem)
        self.tools = self.select_tools(self.type)
        self.strategies = self.select_strategies(self.type)
        self.reasoning_steps = []
        self.code = None
        self.result = None
        self.evaluation = {}
        self.intermediate = {}

    def detect_type(self, problem: Dict[str, Any]) -> str:
        # Example: Use tags or keywords to detect type (확장)
        tags = [t.lower() for t in problem.get('tags', [])]
        if 'geometry' in tags:
            return 'geometry'
        if 'algebra' in tags:
            return 'algebra'
        if 'number theory' in tags or 'nt' in tags:
            return 'number_theory'
        if 'combinatorics' in tags or 'combo' in tags:
            return 'combinatorics'
        if 'probability' in tags:
            return 'probability'
        return 'unknown'

    def select_tools(self, problem_type: str) -> List[str]:
        # 주제별 대표 도구 매핑
        mapping = {
            'geometry': ['sympy.geometry', 'matplotlib'],
            'algebra': ['sympy', 'numpy'],
            'number_theory': ['sympy.ntheory', 'math'],
            'combinatorics': ['itertools', 'math', 'networkx'],
            'probability': ['random', 'numpy', 'scipy.stats'],
            'unknown': ['sympy']
        }
        return mapping.get(problem_type, ['sympy'])

    def select_strategies(self, problem_type: str) -> List[str]:
        # 주제별 사고방식/전략 매핑
        mapping = {
            'geometry': [
                '도형의 성질 활용', '좌표화', '벡터화', '작도/구성', '삼각함수 변환', '면적/길이/각도 계산'
            ],
            'algebra': [
                '치환', '인수분해', '부등식 변형', '함수적 접근', '수열/점화식', '최대최소'
            ],
            'number_theory': [
                '약수/배수 분석', '합동식 변환', '정수해 조건', '유클리드 알고리즘', '소수성 판정', '나머지 분류'
            ],
            'combinatorics': [
                '경우의 수 분할', '포함배제', '그래프 모델링', '순열/조합 공식', '귀납/점화', '생성함수'
            ],
            'probability': [
                '경우의 수 세기', '조건부 확률', '기대값/분산', '확률분포', '시뮬레이션', '트리 다이어그램'
            ],
            'unknown': ['문제의 구조를 분석하고 적합한 전략을 선택']
        }
        return mapping.get(problem_type, ['문제의 구조를 분석하고 적합한 전략을 선택'])

    def add_reasoning(self, step: str, params: Dict[str, Any]):
        self.reasoning_steps.append({'step': step, 'params': params})

    def set_code(self, code: str):
        self.code = code

    def set_result(self, result: Any):
        self.result = result

    def set_evaluation(self, evaluation: Dict[str, Any]):
        self.evaluation = evaluation

    def add_intermediate(self, key: str, value: Any):
        self.intermediate[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            'problem': self.problem,
            'type': self.type,
            'tools': self.tools,
            'reasoning_steps': self.reasoning_steps,
            'code': self.code,
            'result': self.result,
            'evaluation': self.evaluation,
            'intermediate': self.intermediate
        }

def ensure_package(package_name):
    try:
        importlib.import_module(package_name)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])

# Example pipeline using MCPContext

def run_mcp_pipeline(problems: List[Dict[str, Any]], max_iters: int = 3):
    import traceback
    from src.pipeline.solver import LLMClient
    results = []
    llm = LLMClient()
    import ast
    def parse_and_verify_tools(result_entry):
        code = result_entry.get('code', '')
        tools = result_entry.get('tools', [])
        used_tools = set()
        if not code:
            return False, [], tools
        try:
            tree = ast.parse(code)
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
        required = set(t.split('.')[0] for t in tools)
        used = used_tools
        missing = required - used
        return len(missing) == 0, list(missing), list(used)

    for problem in problems:
        ctx = MCPContext(problem)
        ctx.add_reasoning('analyze_problem', {'description': problem.get('description', '')})
        ctx.add_reasoning('select_tools', {'tools': ctx.tools, 'strategies': ctx.strategies})
        prev_code = None
        prev_result = None
        for iter_num in range(max_iters):
            prompt = f"""
You are solving the following math problem:
{problem['description']}

Problem topic: {ctx.type}
Recommended tools: {ctx.tools}
Recommended strategies: {ctx.strategies}

Previous reasoning steps:
{json.dumps(ctx.reasoning_steps, ensure_ascii=False, indent=2)}

Previous code:
{prev_code or ''}

Previous result:
{prev_result or ''}

Reflect on the above. If the answer is incorrect or an error occurred, explain what went wrong and generate improved reasoning and code using the recommended tools and strategies. Otherwise, summarize the solution and output the final code only.
"""
            llm_response = llm.generate(prompt)
            ctx.add_reasoning('llm_reflection', {'iteration': iter_num+1, 'llm_response': llm_response})
            import re
            code_match = re.search(r"```python(.*?)```", llm_response, re.DOTALL)
            code = code_match.group(1).strip() if code_match else llm_response.strip()
            ctx.set_code(code)
            # 코드 실행 전 필요한 패키지 자동 설치
            for tool in ctx.tools:
                pkg = tool.split('.')[0]
                ensure_package(pkg)
            try:
                local_vars = {}
                exec(code, {}, local_vars)
                output = local_vars.get('solutions', local_vars.get('result', None))
                if output is None:
                    output = local_vars
                result = {'output': str(output)}
            except Exception as e:
                result = {'output': None, 'error': str(e), 'traceback': traceback.format_exc()}
                # (3) 코드 실행 중 import 오류 등도 reasoning_steps에 기록
                if 'No module named' in str(e) or 'not defined' in str(e) or 'ImportError' in str(e):
                    ctx.add_reasoning('tool_import_error', {
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                        'message': '코드 실행 중 도구 import 오류 또는 정의되지 않음 발생. 도구 사용을 명시적으로 프롬프트에 요청하세요.'
                    })
            ctx.set_result(result)
            prev_code = code
            prev_result = result
            # 평가(정답 비교는 샘플, 실제 문제에 맞게 수정 필요)
            correct = False
            score = 0.0
            if 'output' in result and result['output']:
                if '6' in result['output'] and '7' in result['output']:
                    correct = True
                    score = 1.0
            ctx.set_evaluation({'correct': correct, 'score': score, 'iteration': iter_num+1})
            if correct:
                break
        # (1) reasoning_steps에 콜백을 반드시 반영하여 저장
        ok, missing, used = parse_and_verify_tools(ctx.to_dict())
        if not ok and missing:
            ctx.add_reasoning('tool_usage_callback', {
                'missing_tools': missing,
                'message': f"LLM에 다음 도구 사용을 명시적으로 요청하세요: {missing}"
            })
        results.append(ctx.to_dict())

    with open('mcp_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # (2) 실행 후 reasoning_steps에 tool_usage_callback step이 있는지 자동 검증
    for i, entry in enumerate(results):
        steps = entry.get('reasoning_steps', [])
        has_callback = any(s.get('step') == 'tool_usage_callback' for s in steps)
        if has_callback:
            print(f"[문제 {i+1}] [WARNING] 도구 미사용 콜백이 reasoning_steps에 기록됨. LLM 프롬프트에 도구 사용을 명시적으로 요청하세요.")
        else:
            print(f"[문제 {i+1}] ✅ 모든 요구 도구가 코드에서 사용됨 또는 콜백 불필요.")

# Example usage
if __name__ == '__main__':
    # Load problems from file or define inline
    problems = [
        {
            'description': 'Let ABC be a triangle with AB = AC. The angle bisector of angle BAC meets BC at D. If BD = 3 and DC = 5, find the length of AB.',
            'tags': ['geometry', 'AIME']
        }
    ]
    run_mcp_pipeline(problems)
