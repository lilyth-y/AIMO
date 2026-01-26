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
from typing import Optional, Dict

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

def extract_answer(text: str) -> Optional[str]:
    m = ANS_REGEX.search(text)
    if not m:
        return None
    ans = m.group(1).strip()
    # Remove trailing explanatory clutter
    ans = ans.split("\n")[0].strip()
    return normalize_answer(ans)

def extract_final_answer_from_output(output: str) -> str:
    """
    Extract the final answer from code execution output.
    Takes the last non-empty line that looks like a numeric answer.
    """
    if not output or output.startswith("Error:"):
        return output.strip()
    
    lines = output.strip().split('\n')
    # Filter out empty lines and error messages
    candidate_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("Error:") or line.startswith("Warning:"):
            continue
        # Remove common prefixes like "Result:", "Answer:", "The answer is", etc.
        cleaned = re.sub(r'^(Result|Answer|The answer is|Final answer|답변|결과)[:：\s]*', '', line, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        if cleaned:
            candidate_lines.append(cleaned)
    
    if not candidate_lines:
        return output.strip()
    
    # Return the last candidate line (most likely the final answer)
    final = candidate_lines[-1]
    # If it contains multiple values, try to extract the last one
    # Common patterns: "x = 42", "answer: 42", "42 (answer)"
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

def log_result(entry: Dict, path: str = "logs/eval_log.jsonl") -> None:
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
