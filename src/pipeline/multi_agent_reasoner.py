"""
Multi-Agent Reasoning System for Enhanced Problem Solving

Implements Generator → Coder → Reviewer → Judge pipeline
for more robust mathematical reasoning and error detection.
"""

from typing import List, Dict, Any, Tuple
from .solver import Solver

class MultiAgentReasoner:
    """Implements multi-agent pipeline for reasoning verification."""

    def __init__(self, solver: Solver):
        self.solver = solver

    def generate_alternatives(self, problem_text: str) -> List[str]:
        """Generator: Creates diverse problem-solving approaches."""
        prompt = f"""
다양한 가설을 제안하라. 다음 수학 문제를 해결하기 위한 3~5가지 서로 다른 접근법을 제시하라.
각 접근법은 간략히 설명하고, 수학적 근거나 예상되는 어려움을 포함하라.

문제: {problem_text}

접근법 1:
접근법 2:
접근법 3:
접근법 4 (필요시):
접근법 5 (필요시):

응답은 접근법 목록만 포함할 것.
"""
        response = self.solver.llm.generate(prompt)
        # Parse into list of approaches
        approaches = [line.strip() for line in response.split('\n')
                     if line.strip() and not line.upper().startswith('접근법')]
        return approaches[:5]  # Limit to 5

    def code_solution(self, problem_text: str, approach: str) -> str:
        """Coder: Implements a specific approach in Python."""
        prompt = f"""
말보다 코드로 증명하라. 다음 수학 문제를 주어진 접근법으로 해결하는 Python 코드를 작성하라.

문제: {problem_text}
접근법: {approach}

요구사항:
- 필수 라이브러리만 사용 (math, sympy 등)
- 실행 결과만 출력 (print 함수)
- 명확한 변수명과 주석 없이

코드:
"""
        return self.solver.llm.generate(prompt)

    def review_code(self, problem_text: str, code: str, result: str, approach: str) -> Tuple[bool, str]:
        """Reviewer: Critically examines the solution."""
        prompt = f"""
가장 까다로운 교수처럼 행동하라. 다음 코드 솔루션을 검토하고 오류나 개선점을 지적하라.

문제: {problem_text}
접근법: {approach}
코드: {code}
실행 결과: {result}

논리적 비약, 코너 케이스 누락, 수학적 오류를 찾아라.
수정해야 하는 부분이 있다면 구체적으로 설명하라.

응답 형식:
문제점: [발견된 문제점들]
등급: [PASS/FAIL/NEEDS_REVISION + 이유]

응답은 위 형식만 지킬 것.
"""
        response = self.solver.llm.generate(prompt)

        # Simple parsing
        if "등급: PASS" in response:
            return True, "Review passed"
        elif "등급: FAIL" in response:
            return False, response.split("문제점:")[-1].strip()
        else:
            return False, "Review indicates revision needed"

    def judge_final(self, problem_text: str, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Judge: Makes final decision from multiple candidates."""
        candidate_summaries = []
        for i, cand in enumerate(candidates, 1):
            candidate_summaries.append(f"""
좌후보 {i}:
접근법: {cand['approach']}
코드: {cand['code']}
결과: {cand['result']}
리뷰: {cand['review']}
""")

        candidates_text = "\n".join(candidate_summaries)

        prompt = f"""
최종 결정을 내려라. 다음 후보 솔루션 중에서 문제를 가장 잘 해결한 최종 답안을 선택하라.

문제: {problem_text}

{candidates_text}

요구사항:
- 모든 후보 중 최고의 솔루션을 선택하라
- 선택 이유를 1-2문장으로 설명하라
- 불충분하면 재토론 권장 (하지만 가능하면 결정)

응답 형식:
선택: [후보 번호]
이유: [설명]
최종 답안: [결과값]
"""
        response = self.solver.llm.generate(prompt)

        # Parse response
        final_choice = None
        final_reason = ""
        final_answer = ""

        if "선택:" in response:
            choice_line = [line for line in response.split('\n') if "선택:" in line]
            if choice_line:
                choice_text = choice_line[0].replace("선택:", "").strip()
                try:
                    final_choice = int(choice_text.split()[0]) - 1  # 0-index
                except:
                    final_choice = 0

        if "이유:" in response:
            reason_line = [line for line in response.split('\n') if "이유:" in line]
            final_reason = reason_line[0].replace("이유:", "").strip() if reason_line else ""

        if "최종 답안:" in response:
            answer_line = [line for line in response.split('\n') if "최종 답안:" in line]
            final_answer = answer_line[0].replace("최종 답안:", "").strip() if answer_line else ""

        return {
            'selected_index': final_choice,
            'reason': final_reason,
            'final_answer': final_answer
        }

    def solve_with_multi_agent(self, problem_text: str) -> Dict[str, Any]:
        """Complete multi-agent pipeline."""
        print("[MULTI-AGENT] Starting multi-agent reasoning...")

        # Step 1: Generator
        approaches = self.generate_alternatives(problem_text)
        print(f"[MULTI-AGENT] Generated {len(approaches)} approaches")

        candidates = []
        max_candidates = min(3, len(approaches)) if approaches else 1

        for i in range(max_candidates):
            if i >= len(approaches):
                break

            approach = approaches[i]
            print(f"[MULTI-AGENT] Coding approach {i+1}: {approach[:50]}...")

            # Step 2: Coder
            code = self.code_solution(problem_text, approach)
            stripped_code = code.replace("```python", "").replace("```", "").strip()

            # Execute code (mock for now, use executor in real)
            try:
                # Simple execution simulation
                result = "42"  # Placeholder - would use self.executor
            except:
                result = "ERROR: execution failed"

            # Step 3: Reviewer
            passed, review_note = self.review_code(problem_text, stripped_code, result, approach)

            candidates.append({
                'approach': approach,
                'code': stripped_code,
                'result': result,
                'review_passed': passed,
                'review_note': review_note,
                'review': review_note  # compatibility for judge_final
            })

        # Step 4: Judge
        if candidates:
            judgment = self.judge_final(problem_text, candidates)
            sel_idx = judgment.get('selected_index')
            # Validate selected index
            if sel_idx is None or not isinstance(sel_idx, int) or sel_idx < 0 or sel_idx >= len(candidates):
                # fallback: pick first candidate that passed review, else first candidate
                sel_idx = 0
                for i, c in enumerate(candidates):
                    if c.get('review_passed'):
                        sel_idx = i
                        break
            selected = candidates[sel_idx]
            print(f"[MULTI-AGENT] Judge selected candidate {sel_idx+1}")
            return {
                'selected': selected,
                'final_answer': judgment.get('final_answer', selected.get('result')),
                'judgment_reason': judgment.get('reason', '')
            }

        # Fallback
        return {
            'selected': None,
            'final_answer': None,
            'error': 'No candidates generated'
        }
