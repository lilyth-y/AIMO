#!/usr/bin/env python3
"""
Export pipeline JSONL logs (logs/eval_log.jsonl) to dashboard static files:

  - dashboard/public/eval_data.json
  - dashboard/public/numina_eval_balanced.json

This enables the dashboard `/process` page to show *real* chain-of-thought (if logged),
generated code, and runtime output/tracebacks.

Usage:
  python scripts/export_dashboard_from_log.py
  python scripts/export_dashboard_from_log.py --log logs/eval_log.jsonl --limit 50
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import ast


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _iter_brace_blocks(s: str) -> List[str]:
    """Split top-level `{...}` segments (for parsing logged chat dict blobs)."""
    out: List[str] = []
    i = 0
    n = len(s)
    while i < n:
        j = s.find("{", i)
        if j < 0:
            break
        depth = 0
        k = j
        while k < n:
            if s[k] == "{":
                depth += 1
            elif s[k] == "}":
                depth -= 1
                if depth == 0:
                    out.append(s[j : k + 1])
                    i = k + 1
                    break
            k += 1
        else:
            break
    return out


def _extract_reasoning_text(raw: Any) -> str:
    """
    Normalize solver `llm_reasoning` for dashboard markdown:
    - Plain string -> as-is
    - Concatenated {'role': 'user'|'assistant', 'content': ...} blobs -> assistant parts only
    """
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    if "{'role'" not in s and '"role"' not in s:
        return s
    parts: List[str] = []
    for block in _iter_brace_blocks(s):
        try:
            obj = ast.literal_eval(block)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        role = str(obj.get("role") or "")
        content = obj.get("content")
        if role == "assistant" and isinstance(content, str) and content.strip():
            parts.append(content.strip())
    if parts:
        return "\n\n".join(parts)
    return s


def _is_errorish(text: Optional[str]) -> bool:
    if not text:
        return False
    t = str(text)
    return (
        "Traceback" in t
        or "ERROR:" in t
        or "Error:" in t
        or "SyntaxError" in t
        or "invalid syntax" in t
        or "unterminated string" in t
        or "All strategies failed" in t
    )


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                out.append(obj)
    return out


def _sort_key(e: Dict[str, Any]) -> Tuple[int, str]:
    attempt = e.get("attempt")
    try:
        a = int(attempt) if attempt is not None else 999999
    except Exception:
        a = 999999
    strat = str(e.get("strategy") or "")
    return a, strat


def _pick_best_entry(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Prefer verified entries; otherwise the last attempt.
    verified = [e for e in entries if bool(e.get("verified"))]
    if verified:
        verified.sort(key=_sort_key)
        return verified[-1]
    entries.sort(key=_sort_key)
    return entries[-1] if entries else {}


def _pick_display_code(run_entries: List[Dict[str, Any]], best: Dict[str, Any]) -> str:
    """Prefer a real Python payload for the bottom panel (like the original mock)."""
    if isinstance(best.get("generated_code"), str) and best["generated_code"].strip():
        return best["generated_code"].strip()
    for e in sorted(run_entries, key=_sort_key):
        gc = e.get("generated_code")
        if not isinstance(gc, str) or not gc.strip():
            continue
        if gc.strip().startswith("print('ERROR") or "Code generation failed" in gc:
            continue
        return gc.strip()
    # Fallback: last non-empty code even if error stub
    for e in reversed(sorted(run_entries, key=_sort_key)):
        gc = e.get("generated_code")
        if isinstance(gc, str) and gc.strip():
            return gc.strip()
    ex = best.get("execution_output_raw") or best.get("execution_result")
    return str(ex) if ex is not None else ""


def _to_eval_data(run_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    best = _pick_best_entry(run_entries)
    query = str(
        best.get("problem_text")
        or best.get("problem_preview")
        or run_entries[0].get("problem_text")
        or run_entries[0].get("problem_preview")
        or ""
    )

    reasoning_steps = []
    for e in sorted(run_entries, key=_sort_key):
        step_name = str(e.get("strategy") or "unknown")
        llm_reasoning = e.get("llm_reasoning")
        generated_code = e.get("generated_code")
        exec_raw = e.get("execution_output_raw")
        exec_clean = e.get("execution_result")
        cot = _extract_reasoning_text(llm_reasoning)
        params = {
            "iteration": e.get("attempt"),
            # CoT only — code/runtime rendered separately in Process.tsx (matches original demo layout).
            "llm_response": cot,
            "generated_code": generated_code,
            "execution_output_raw": exec_raw,
            "execution_result": exec_clean,
            "verified": e.get("verified"),
            "mismatch": e.get("mismatch"),
            "mismatch_type": e.get("mismatch_type"),
            "reconcile_details": e.get("reconcile_details"),
        }
        reasoning_steps.append({"step": step_name, "params": params})

    response = _pick_display_code(run_entries, best)

    out_raw = best.get("execution_output_raw")
    out_clean = best.get("execution_result")
    output_text = out_raw if isinstance(out_raw, str) and out_raw.strip() else (out_clean if isinstance(out_clean, str) else None)

    err = None
    if not bool(best.get("verified")) and (_is_errorish(output_text) or _is_errorish(str(best.get("execution_result") or ""))):
        err = "execution_or_verification_failed"

    return {
        "query": query,
        "response": response,
        "reasoning_steps": reasoning_steps,
        "result": {
            "output": output_text,
            "error": err,
            "traceback": output_text if (output_text and "Traceback" in output_text) else None,
        },
        "tools": ["python_executor", "sympy"],
        "type": str(best.get("strategy") or "run"),
    }


def _to_problem_row(run_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    best = _pick_best_entry(run_entries)
    problem = str(
        best.get("problem_text")
        or best.get("problem_preview")
        or run_entries[0].get("problem_text")
        or run_entries[0].get("problem_preview")
        or ""
    )
    ans = best.get("extracted_answer")
    if ans is None:
        # Fall back to cleaned execution result for display (not guaranteed to be reference answer).
        ans = best.get("execution_result")
    # Infer a rough type from logged strategy features (optional)
    feat = best.get("strategy_features") or {}
    dom = str(feat.get("dominant_domain") or "Other")
    problem_type = "Geometry" if dom == "geometry" else ("Number Theory" if dom == "number_theory" else ("Algebra" if dom == "algebra" else "Other"))

    # Compose a readable markdown "solution" that includes reasoning + code + runtime.
    parts: List[str] = []
    for e in sorted(run_entries, key=_sort_key):
        parts.append(f"### {e.get('strategy')}")
        lr = _extract_reasoning_text(e.get("llm_reasoning"))
        if lr:
            parts.append(lr)
        gc = e.get("generated_code")
        if gc:
            parts.append("```python\n" + str(gc) + "\n```")
        raw = e.get("execution_output_raw")
        if raw:
            parts.append("```text\n" + str(raw) + "\n```")
    solution = "\n\n".join(parts).strip() or "*No detailed reasoning/code was logged for this run.*"

    return {
        "problem": problem,
        "solution": solution,
        "answer": str(ans) if ans is not None else "",
        "source": "pipeline_log",
        "problem_type": problem_type,
        "question_type": "unknown",
        "run_id": best.get("run_id"),
        "problem_id": best.get("problem_id"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", type=Path, default=Path("logs/eval_log.jsonl"))
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--limit", type=int, default=50, help="Max runs to export (most recent by file order).")
    ap.add_argument(
        "--eval-data-only",
        action="store_true",
        help="Write only dashboard/public/eval_data.json (keep existing numina_eval_balanced.json).",
    )
    args = ap.parse_args()

    root = _repo_root()
    log_path = args.log
    if not log_path.is_absolute():
        log_path = (root / log_path).resolve()

    out_dir = args.out_dir or (root / "dashboard" / "public")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = _load_jsonl(log_path)
    if not rows:
        raise SystemExit(f"No log rows found at: {log_path}")

    # Group by run_id while preserving file order (later entries are newer).
    runs: Dict[str, List[Dict[str, Any]]] = {}
    run_order: List[str] = []
    for r in rows:
        rid = str(r.get("run_id") or "")
        if not rid:
            continue
        if rid not in runs:
            runs[rid] = []
            run_order.append(rid)
        runs[rid].append(r)

    # Take most recent N runs
    selected = run_order[-max(1, args.limit) :]

    eval_data = [_to_eval_data(runs[rid]) for rid in selected]
    (out_dir / "eval_data.json").write_text(json.dumps(eval_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(eval_data)} runs -> {out_dir / 'eval_data.json'}")
    if not args.eval_data_only:
        problems = [_to_problem_row(runs[rid]) for rid in selected]
        (out_dir / "numina_eval_balanced.json").write_text(json.dumps(problems, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {len(problems)} runs -> {out_dir / 'numina_eval_balanced.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

