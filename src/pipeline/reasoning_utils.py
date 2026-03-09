"""Reasoning Utilities
 - Structured prompt construction
 - Answer parsing / normalization
 - SymPy based lightweight verification
 - Self-refine draft -> improved reasoning (stub)
"""

from __future__ import annotations
import json
import re
import os
from typing import Optional, Dict, Any

try:
    import sympy as sp
except ImportError:  # SymPy optional
    sp = None

STRUCTURE_TAGS = ["FACTS", "GOAL", "PLAN", "DERIVATION", "CHECK", "ANS"]

PROOF_KEYWORDS = [
    'prove', 'show that', 'demonstrate', 'if and only if', 'forall', 'exists',
    'determine whether', 'find all', 'classify', 'maximum', 'minimum'
]
NUMBER_THEORY_KEYWORDS = [
    'prime', 'gcd', 'lcm', 'mod', 'divisible', 'integer solution', 'diophantine'
]
GEOMETRY_KEYWORDS = [
    'triangle', 'circle', 'angle', 'perpendicular', 'parallel', 'tangent', 'radius',
    'diameter', 'chord', 'polygon', 'midpoint'
]
COMPLEXITY_CLAUSE_SEPARATORS = [',', ';']
SYMBOLS = ['+', '-', '*', '/', '^', '=', '<', '>', '≥', '≤']

def assess_complexity(problem: str) -> int:
    """Compute a heuristic complexity score combining semantic and structural signals.
    Score components (integer, additive):
      + Keywords (proof/number theory/geometry) -> +1 each (capped per group)
      + Distinct keyword groups present -> extra +1 per group beyond first
      + Clauses (comma/semicolon separated) -> clause_count//2
      + Symbol density (unique math symbols) -> len(unique_symbols)
      + Multi-question markers (e.g. '?', occurrences>1) -> +1
      + Length bonus (>= STRUCTURED_LENGTH_THRESHOLD) -> +1
    """
    text_lower = problem.lower()
    score = 0
    present_groups = 0

    def count_keywords(keywords):
        c = sum(1 for k in keywords if k in text_lower)
        return min(c, 3)  # cap influence per list

    proof_hits = count_keywords(PROOF_KEYWORDS)
    if proof_hits:
        score += proof_hits
        present_groups += 1
    nt_hits = count_keywords(NUMBER_THEORY_KEYWORDS)
    if nt_hits:
        score += nt_hits
        present_groups += 1
    geo_hits = count_keywords(GEOMETRY_KEYWORDS)
    if geo_hits:
        score += geo_hits
        present_groups += 1

    if present_groups > 1:
        score += (present_groups - 1)  # reward multi-domain complexity

    # Clause heuristic
    clause_count = sum(problem.count(sep) for sep in COMPLEXITY_CLAUSE_SEPARATORS)
    score += clause_count // 2

    # Symbol density (unique occurrences)
    unique_symbols = {s for s in SYMBOLS if s in problem}
    score += len(unique_symbols)

    # Multi-question markers
    if problem.count('?') > 1:
        score += 1

    # Length bonus (soft)
    from . import config as _cfg
    if len(problem) >= _cfg.STRUCTURED_LENGTH_THRESHOLD:
        score += 1

    return score

def build_structured_prompt(problem: str) -> str:
    truncated = problem if len(problem) < 1200 else problem[:1200] + "..."
    return (
        "<FACTS>Extract key givens from problem here.</FACTS>\n"
        "<GOAL>State exactly what must be found or proven.</GOAL>\n"
        "<PLAN>List 2-4 high level steps.</PLAN>\n"
        f"<DERIVATION>{truncated}\nStep-by-step reasoning with explicit transformations.</DERIVATION>\n"
        "<CHECK>Substitute back / boundary / parity / dimension checks.</CHECK>\n"
        "<ANS>Final answer ONLY (compact canonical form).</ANS>"
    )

ANS_REGEX = re.compile(r"<ANS>(.*?)</ANS>", re.DOTALL)
BOXED_REGEX = re.compile(r"\\boxed\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", re.DOTALL)
# Last number on a line or "answer is X" / "Answer: X"
LAST_NUMBER_REGEX = re.compile(
    r"(?:answer\s*[:\s=]|result\s*[:\s=]|final\s*[:\s=]|the answer is)\s*([-+]?\d+\.?\d*(?:/\d+)?(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)
SIMPLE_NUMBER_LINE = re.compile(r"^\s*[-+]?\d+\.?\d*(?:/\d+)?(?:[eE][-+]?\d+)?\s*$")
# Placeholder/invalid ANS content (prompt instruction, not actual answer)
ANS_PLACEHOLDER_PATTERNS = (
    "final answer only",
    "only compact canonical form",
    "compact canonical form",
)
# 최종 답안: / 결과값 extraction (multi-agent judge response)
FINAL_ANSWER_LINE_REGEX = re.compile(r"최종\s*답안\s*[:\s]*([^\n]+)", re.IGNORECASE)
RESULT_VALUE_REGEX = re.compile(r"결과값\s*[:\s]*([^\n]+)", re.IGNORECASE)
# LaTeX fraction (short answer form)
LATEX_FRAC_REGEX = re.compile(r"\\frac\{[^{}]+\}\{[^{}]+\}")

def _is_placeholder_ans(ans: str) -> bool:
    """True if ANS content looks like prompt placeholder, not a real answer."""
    if not ans or len(ans) > 200:
        return len(ans) > 200
    lower = ans.lower().strip()
    for p in ANS_PLACEHOLDER_PATTERNS:
        if p in lower:
            return True
    return False


def _extract_answer_from_long_text(text: str) -> Optional[str]:
    """
    From long/dialogue text, extract a short answer: 최종 답안: X, 결과값 X, last number, or LaTeX \\frac.
    """
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    # 1. "최종 답안: 302" or "최종 답안: \frac{1}{6}"
    m = FINAL_ANSWER_LINE_REGEX.search(text)
    if m:
        val = m.group(1).strip()
        if val and len(val) < 300 and not _looks_like_dialogue(val):
            return normalize_answer(val)
    # 2. "결과값: 302"
    m = RESULT_VALUE_REGEX.search(text)
    if m:
        val = m.group(1).strip()
        if val and len(val) < 300 and not _looks_like_dialogue(val):
            return normalize_answer(val)
    # 3. Last LaTeX fraction
    fracs = LATEX_FRAC_REGEX.findall(text)
    if fracs:
        return normalize_answer(fracs[-1])
    # 4. Last integer or simple number in text (avoid extracting from JSON keys)
    numbers = re.findall(r"(?<![.\d])([-+]?\d{1,10})(?![.\d])", text)
    if numbers:
        return normalize_answer(numbers[-1])
    return None


def _looks_like_dialogue(s: str) -> bool:
    """True if string looks like prompt/dialogue/JSON, not a math answer."""
    if len(s) > 400:
        return True
    s_lower = s.lower()
    if "'role'" in s or "'content'" in s or '"role"' in s or '"content"' in s:
        return True
    if "선택:" in s and "이유:" in s:
        return True
    if "접근법" in s and "코드:" in s:
        return True
    return False


def extract_answer(text: str) -> Optional[str]:
    if not (text or isinstance(text, str)):
        return None
    text = text.strip()
    # 1. <ANS>...</ANS>
    m = ANS_REGEX.search(text)
    if m:
        ans = m.group(1).strip().split("\n")[0].strip()
        if ans and not _is_placeholder_ans(ans):
            return normalize_answer(ans)
    # 2. \boxed{...}
    boxed = BOXED_REGEX.search(text)
    if boxed:
        ans = boxed.group(1).strip()
        if ans:
            return normalize_answer(ans)
    # 3. "answer is X" / "Answer: X"
    last_num = LAST_NUMBER_REGEX.search(text)
    if last_num:
        return normalize_answer(last_num.group(1).strip())
    # 4. Last line that is just a number
    for line in reversed(text.split("\n")):
        line = line.strip()
        if SIMPLE_NUMBER_LINE.match(line):
            return normalize_answer(line)
    # 5. Any last number in text — 비활성화: 긴 추론에서는 중간값(예: 32)이 선택되는 것을 막기 위해
    #    짧은 텍스트(<=400자)에서만 사용. 긴 추론은 실행 결과(cleaned_result)에 맡김.
    if len(text) <= 400:
        any_num = re.findall(r"[-+]?\d+\.?\d*(?:/\d+)?(?:[eE][-+]?\d+)?", text)
        if any_num:
            return normalize_answer(any_num[-1])
    return None


def normalize_multi_agent_answer(raw: Any) -> Optional[str]:
    """
    MULTI-AGENT 최종 답을 검증/저장용 문자열로 정규화.
    dict(role/content)이면 content에서 숫자 추출, 문자열이면 extract_answer 적용.
    긴 대화/JSON 문자열은 _extract_answer_from_long_text로 숫자·LaTeX만 추출.
    """
    if raw is None:
        return None
    if isinstance(raw, dict):
        text = (
            raw.get("content")
            or raw.get("text")
            or raw.get("value")
            or raw.get("answer")
            or raw.get("result")
        )
        if text is not None:
            raw = text
        else:
            raw = str(raw)
    if isinstance(raw, (int, float)):
        return str(raw)
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return None
        extracted = extract_answer(s)
        # 긴 문자열이거나 대화/JSON 형태면 raw 반환 금지, long-text 추출 시도
        if len(s) > 500 or _looks_like_dialogue(s):
            if extracted and not _looks_like_dialogue(extracted) and len(extracted) < 400:
                return extracted
            fallback = _extract_answer_from_long_text(s)
            return fallback if fallback is not None else (extracted if extracted and len(extracted) < 200 else None)
        return extracted if extracted is not None else s or None
    return str(raw).strip() or None


# 라벨이 붙은 줄(Answer:, 결과:, 최종 답안: 등)을 우선 찾기 위함
ANSWER_LABEL_PATTERN = re.compile(
    r'^(Result|Answer|The answer is|Final answer|답변|결과|최종\s*답안)\s*[：:\s]*\s*(.*)$',
    re.IGNORECASE
)


def extract_final_answer_from_output(output: str) -> str:
    """
    Extract the final answer from code execution output.
    Prefer lines that are explicitly labeled (Answer:, 결과:, 최종 답안:);
    otherwise use the last non-empty line that looks like a numeric answer.
    """
    if not output or output.startswith("Error:"):
        return output.strip()
    # 모델 로드 실패 등으로 실행된 에러 메시지에서 숫자(예: 32-bit의 32)가 추출되지 않도록
    out_upper = output.upper()
    if "ERROR" in out_upper or "MODEL FAILED" in out_upper or "32-BIT" in out_upper:
        return output.strip()
    
    lines = output.strip().split('\n')
    labeled_values = []
    candidate_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("Error:") or line.startswith("Warning:"):
            continue
        # 라벨이 붙은 줄 우선 수집 (Answer: 302, 결과: 1/6 등)
        label_match = ANSWER_LABEL_PATTERN.match(line)
        if label_match:
            val = label_match.group(2).strip()
            if val:
                labeled_values.append(val)
        cleaned = re.sub(r'^(Result|Answer|The answer is|Final answer|답변|결과)[:：\s]*', '', line, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        if cleaned:
            candidate_lines.append(cleaned)
    
    # 라벨이 붙은 값이 있으면 그 중 마지막 것 사용 (보통 최종 답 1개)
    if labeled_values:
        final = labeled_values[-1]
        match = re.search(r'[-+]?\d+\.?\d*(?:/\d+)?(?:[eE][-+]?\d+)?', final)
        if match:
            return match.group(0)
        # LaTeX \frac 등이면 그대로 반환
        if final and len(final) < 200:
            return final
    
    if not candidate_lines:
        return output.strip()
    
    # 기존: 마지막 후보 줄에서 숫자 추출
    final = candidate_lines[-1]
    match = re.search(r'[-+]?\d+\.?\d*(?:/\d+)?(?:[eE][-+]?\d+)?', final)
    if match:
        return match.group(0)
    return final

def normalize_answer(ans: str) -> str:
    """Normalize answer string to canonical form."""
    if not ans:
        return ""
    
    # Simple normalizations
    ans = ans.replace("\\", "\\")  # keep latex as-is
    ans = re.sub(r"\s+", " ", ans)
    
    # Convert common variants
    replacements = {
        "−": "-",
        "：": ":",
        "×": "*",
        "÷": "/",
        "√": "sqrt",
    }
    for k, v in replacements.items():
        ans = ans.replace(k, v)
    
    ans = ans.strip()
    
    # Remove common prefixes/suffixes
    ans = re.sub(r'^(Result|Answer|The answer is|Final answer|답변|결과)[:：\s]*', '', ans, flags=re.IGNORECASE)
    ans = re.sub(r'[\(\)\[\]]', '', ans)  # Remove parentheses/brackets that are just formatting
    
    # Basic power normalization caret->** (only for standalone expressions)
    if '^' in ans:
        ans = ans.replace('^', '**')
    
    # Attempt sympy simplification for fractions/roots if available
    if sp:
        try:
            expr = sp.sympify(ans)
            expr = sp.simplify(expr)
            # For integers, return as integer string
            if expr.is_Integer:
                ans = str(int(expr))
            else:
                ans = str(expr)
        except Exception:
            pass
    
    return ans.strip()

def sympy_equivalent(a: str, b: str) -> bool:
    if not sp:
        return a == b
    try:
        ea = sp.sympify(a)
        eb = sp.sympify(b)
        return sp.simplify(ea - eb) == 0
    except Exception:
        return a == b

def canonicalize_expression(text: str) -> str:
    """Return a canonical sympy string if possible; else original."""
    if not sp:
        return text
    try:
        expr = sp.sympify(text)
        simp = sp.simplify(expr)
        candidates = [simp, sp.factor(simp), sp.expand(simp)]
        best = min(candidates, key=lambda e: len(str(e)))
        return str(best)
    except Exception:
        return text

def verify_answer(expected: str, predicted: str) -> bool:
    if predicted is None:
        return False
    # Direct match
    if predicted.strip() == expected.strip():
        return True
    # SymPy equivalence
    return sympy_equivalent(predicted, expected)

def self_refine(problem: str, draft: str, llm_generate) -> str:
    """Given an initial draft reasoning, request a refinement.
    llm_generate: callable(prompt)->str
    """
    critique_prompt = (
        "You are a math reasoning critic. Identify issues and produce an improved reasoning.\n"
        f"Problem:\n{problem}\n\nDraft reasoning:\n{draft}\n\n"
        "Return ONLY improved reasoning using same tags (<FACTS>..<ANS>)."
    )
    improved = llm_generate(critique_prompt)
    return improved if any(tag in improved for tag in STRUCTURE_TAGS) else draft

def log_result(entry: Dict[str, Any], path: str = "logs/eval_log.jsonl") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def count_free_symbols(expr_text: str) -> int:
    if not expr_text or not sp:
        return 0
    try:
        e = sp.sympify(expr_text)
        return len(e.free_symbols)
    except Exception:
        return 0

def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(text.strip().split())

def make_ids(problem_text: str) -> Dict[str, str]:
    import uuid, hashlib
    run_id = str(uuid.uuid4())
    problem_hash = hashlib.sha1(problem_text.encode("utf-8")).hexdigest()[:12]
    return {"run_id": run_id, "problem_id": problem_hash}

def build_refine_prompt(problem_text: str, previous_reasoning: str | None, previous_code: str | None,
                        error_type: str, execution_result: str | None, extracted_answer: str | None) -> str:
    guidance_map = {
        'format': 'Formatting mismatch only: keep logic; adjust output formatting to canonical math form.',
        'arithmetic': 'Arithmetic error: find incorrect numeric step and recompute accurately.',
        'logic': 'Logical error: revise PLAN/DERIVATION ensuring each transformation is justified.',
        'verification_fail': 'Verification failed: correct final computation so reverse/expected checks pass.',
        'mismatch': 'Mismatch: align printed answer with <ANS> reasoning tag; recompute if necessary.',
        'other': 'General correction: minimally fix to produce correct final answer.'
    }
    guidance = guidance_map.get(error_type, guidance_map['other'])
    parts = [
        "You previously attempted this math problem and made an error.",
        f"Error category: {error_type}.",
        guidance,
        "Return ONLY corrected Python code that prints the final answer (no commentary)."
    ]
    if previous_reasoning:
        parts.append("Prior structured reasoning (reference):\n" + previous_reasoning)
    if previous_code:
        parts.append("Faulty code:\n```python\n" + previous_code + "\n```")
    if execution_result:
        parts.append(f"Observed output: {execution_result}")
    if extracted_answer:
        parts.append(f"Extracted <ANS>: {extracted_answer}")
    parts.append("Problem:\n" + problem_text)
    parts.append("Corrected Code:")
    return "\n\n".join(parts)
