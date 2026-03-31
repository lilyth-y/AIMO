"""
Multi-Agent Reasoning System for Enhanced Problem Solving

Implements Generator → Coder → Reviewer → Judge pipeline
for more robust mathematical reasoning and error detection.
"""

from typing import List, Dict, Any, Tuple
import re
from .solver import Solver
from .orchestrator_helpers import is_execution_error_output
from .reasoning_utils import extract_answer, _extract_answer_from_long_text, extract_final_answer_from_output

class MultiAgentReasoner:
    """Implements multi-agent pipeline for reasoning verification."""

    def __init__(self, solver: Solver, executor: Any = None):
        self.solver = solver
        self.executor = executor

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
        response = self.solver.llm.generate(prompt, do_sample=True)
        # Parse into list of approaches.
        # The model often includes labels like "접근법 1:"; the previous parser
        # filtered those lines out, frequently producing an empty list.
        text = (response or "").strip()
        approaches: List[str] = []

        # Prefer extracting the content after "접근법 k:" markers.
        for m in re.finditer(r"(?m)^\s*접근법\s*\d+\s*[:\-]\s*(.+?)\s*$", text):
            item = m.group(1).strip()
            if item:
                approaches.append(item)

        # Fallback: accept numbered/bulleted lines if no markers found.
        if not approaches:
            for ln in text.splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                # Drop pure label lines like "접근법 1:" with no content.
                if re.match(r"^\s*접근법\s*\d+\s*[:\-]?\s*$", ln):
                    continue
                # Strip common list prefixes.
                ln = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", ln).strip()
                if ln:
                    approaches.append(ln)

        # Ensure at least one usable approach so downstream doesn't generate 0 candidates.
        if not approaches:
            approaches = ["직접 풀이: 기하/대수 식을 정리하고 필요한 값을 계산한다."]

        # Deduplicate while preserving order, then cap.
        uniq: List[str] = []
        seen = set()
        for a in approaches:
            key = a.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            uniq.append(key)
        return uniq[:5]

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
- 출력은 '파이썬 코드만' 포함할 것 (설명/마크다운/백틱 금지)
- 첫 줄부터 코드여야 한다

코드:
"""
        return self.solver.llm.generate(prompt, do_sample=True)

    def code_solution_retry(self, problem_text: str, approach: str, bad_code: str, error_or_output: str) -> str:
        """PAL-style: one repair attempt after a failed or empty execution."""
        err_snip = (error_or_output or "")[:2000]
        prompt = f"""
이전 파이썬 코드가 실행에 실패했거나 출력이 비어 있다. 오류를 고쳐 실행 가능한 코드만 출력하라.

문제: {problem_text}
접근법: {approach}

이전 코드:
{bad_code}

실행 결과(일부):
{err_snip}

요구사항:
- math, sympy만 사용 가능
- 답은 print로만 출력
- 설명/마크다운/백틱 금지, 첫 줄부터 코드

코드:
"""
        return self.solver.llm.generate(prompt, do_sample=True)

    @staticmethod
    def _needs_code_retry(result: str) -> bool:
        if not isinstance(result, str):
            return True
        t = result.strip()
        if not t:
            return True
        tl = t.lower()
        if tl.startswith("error:"):
            return True
        if "error: timeout" in tl or "cputimelimitexceeded" in tl:
            return True
        return False

    @staticmethod
    def _extract_python_code(text: str) -> str:
        """
        Best-effort extraction of Python code from LLM output.
        Prefer fenced code blocks when present; otherwise drop leading prose.
        """
        if not isinstance(text, str):
            return str(text)
        s = text.strip()
        # Prefer ```python ... ```
        m = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", s, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # Otherwise, remove obvious leading prose until a likely code line.
        lines = s.splitlines()
        start = 0
        for i, ln in enumerate(lines):
            t = ln.strip()
            if not t:
                continue
            if t.startswith(("import ", "from ", "def ", "class ", "print(", "if ", "for ", "while ")):
                start = i
                break
            # Common code patterns: assignment, function call, sympy symbols
            if re.match(r"^[A-Za-z_]\w*\s*=", t) or "symbols(" in t or "Symbol(" in t:
                start = i
                break
        return "\n".join(lines[start:]).strip()

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
        response = self.solver.llm.generate(prompt, do_sample=False)

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
추출된_답: {cand.get('parsed_answer')}
리뷰: {cand['review']}
""")

        candidates_text = "\n".join(candidate_summaries)
        
        # Determine if there is consensus among extracted answers (more stable than raw stdout).
        results = [c.get('parsed_answer') for c in candidates if c.get('parsed_answer')]
        consensus_counts = {}
        for r in results:
            if r and not is_execution_error_output(r):
                consensus_counts[r] = consensus_counts.get(r, 0) + 1
        
        consensus_info = ""
        if consensus_counts:
            most_common = max(consensus_counts.items(), key=lambda x: x[1])
            if most_common[1] > 1:
                consensus_info = f"\n[System Note: Found consensus on answer '{most_common[0]}' ({most_common[1]}/{len(candidates)} candidates)]"

        prompt = f"""
최종 결정을 내려라. 다음 후보 솔루션 중에서 문제를 가장 잘 해결한 최종 답안을 선택하라.{consensus_info}

문제: {problem_text}

{candidates_text}

요구사항:
- 모든 후보 중 최고의 솔루션을 선택하라
- 선택 이유를 1-2문장으로 설명하라
- 최종 답안은 반드시 해당 후보의 '추출된_답' 값을 그대로 사용하라 (새 숫자/식 생성 금지)

응답 형식:
선택: [후보 번호]
이유: [설명]
최종 답안: [결과값]
"""
        response = self.solver.llm.generate(prompt, do_sample=False)

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
                except Exception:
                    final_choice = 0

        if "이유:" in response:
            reason_line = [line for line in response.split('\n') if "이유:" in line]
            final_reason = reason_line[0].replace("이유:", "").strip() if reason_line else ""

        if "최종 답안:" in response:
            answer_line = [line for line in response.split('\n') if "최종 답안:" in line]
            final_answer = answer_line[0].replace("최종 답안:", "").strip() if answer_line else ""

        # If final_answer is empty or looks like full dialogue/prompt, extract number/LaTeX only
        if not final_answer or len(final_answer) > 200 or "'role'" in final_answer or "'content'" in final_answer:
            extracted = extract_answer(response) or _extract_answer_from_long_text(response)
            if extracted:
                final_answer = extracted

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
        # Always attempt at least one candidate (generator fallback ensures >=1).
        max_candidates = min(3, max(1, len(approaches)))

        for i in range(max_candidates):
            approach = approaches[i] if i < len(approaches) else approaches[0]

            # ASCII-safe log (avoid cp949 encoding errors on Windows)
            _preview = (approach.get("content", str(approach))[:50] if isinstance(approach, dict) else str(approach)[:50])
            _preview = _preview.encode("ascii", "replace").decode("ascii")
            print(f"[MULTI-AGENT] Coding approach {i+1}: {_preview}...")

            # Step 2: Coder (+ optional PAL-style single retry)
            code = self.code_solution(problem_text, approach)
            stripped_code = self._extract_python_code(code)

            def _exec_code(code_str: str) -> str:
                try:
                    if self.executor:
                        if hasattr(self.executor, 'execute_with_stats'):
                            r, _ = self.executor.execute_with_stats(code_str)
                            return r
                        return self.executor.execute(code_str)
                    return "ERROR: No executor provided"
                except Exception as e:
                    return f"ERROR: execution failed: {e}"

            result = _exec_code(stripped_code)
            if self._needs_code_retry(result):
                retry_code = self.code_solution_retry(problem_text, approach, stripped_code, result)
                stripped_code = self._extract_python_code(retry_code)
                result = _exec_code(stripped_code)

            # Parse the final answer from stdout (stable signal for judging / output).
            parsed_answer = None
            if isinstance(result, str):
                # Never treat executor error strings (which include line numbers) as answers.
                if is_execution_error_output(result):
                    parsed_answer = None
                else:
                    parsed_answer = extract_final_answer_from_output(result)
                    if parsed_answer and is_execution_error_output(parsed_answer):
                        parsed_answer = None

            # Step 3: Reviewer
            passed, review_note = self.review_code(problem_text, stripped_code, result, approach)

            candidates.append({
                'approach': approach,
                'code': stripped_code,
                'result': result,
                'parsed_answer': parsed_answer,
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
            # If judge picked a candidate without a parsed answer, prefer any candidate with a parsed answer
            # (and ideally one that passed review).
            if not candidates[sel_idx].get("parsed_answer"):
                idx_with_answer = [i for i, c in enumerate(candidates) if c.get("parsed_answer")]
                if idx_with_answer:
                    # Prefer review_passed among those with parsed answers.
                    best = None
                    for i in idx_with_answer:
                        if candidates[i].get("review_passed"):
                            best = i
                            break
                    sel_idx = best if best is not None else idx_with_answer[0]

            selected = candidates[sel_idx]
            print(f"[MULTI-AGENT] Judge selected candidate {sel_idx+1}")
            # Prefer extracted answer from the selected candidate; fall back to judge text; then raw result.
            final_answer = selected.get("parsed_answer") or judgment.get('final_answer') or selected.get('result')
            return {
                'selected': selected,
                'final_answer': final_answer,
                'judgment_reason': judgment.get('reason', '')
            }

        # Fallback
        return {
            'selected': None,
            'final_answer': None,
            'error': 'No candidates generated'
        }
