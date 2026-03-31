"""
Research A/B:
  Baseline: Vertex Gemini model (e.g. gemini-2.5-flash)
  Treatment: Your fine-tuned Qwen Vertex Endpoint (answer-only mode)

Same dataset + same answer-only prompt + same extractor + paired McNemar.

Requires:
  - GOOGLE_CLOUD_PROJECT set
  - AIMO_VERTEX_ENDPOINT set (full resource name)
  - python -m pip install -r requirements-vertex-sdk.txt
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from tqdm import tqdm

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, "src"))

from evaluation.config import find_data_file, ensure_dir, RESULTS_DIR, NUMINA_TRAINING_FILE
from evaluation.evaluation_utils import (
    check_answer_correctness,
    determine_difficulty_from_source,
    mcnemar_exact_two_sided_p_value,
)
from pipeline.answer_extraction import AnswerExtractor
from pipeline.vertex_inference import generate_vertex
from pipeline.vertex_endpoint_inference import is_vertex_endpoint_configured, build_answer_only_prompt, predict_vertex_endpoint_answer_only


@dataclass
class ProblemItem:
    idx: int
    problem: str
    answer: str
    source: str


def _looks_non_numeric_answer(ans: str) -> bool:
    if ans is None:
        return True
    s = str(ans).strip().lower()
    if not s:
        return True
    if s in {"proof", "prove", "proved", "true", "false"}:
        return True
    return False


def load_numina_jsonl_filtered(n: int, seed: int, filename: str = NUMINA_TRAINING_FILE) -> List[ProblemItem]:
    path = find_data_file(filename)
    rng = __import__("random").Random(seed)
    pool: List[ProblemItem] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            problem = obj.get("problem") or ""
            answer = obj.get("answer")
            source = obj.get("source") or "unknown"
            if not isinstance(problem, str) or not problem.strip():
                continue
            if _looks_non_numeric_answer(answer):
                continue
            pool.append(ProblemItem(idx=i, problem=problem, answer=str(answer), source=str(source)))
    if len(pool) < n:
        raise RuntimeError(f"requested={n}, available={len(pool)} in {path}")
    rng.shuffle(pool)
    return pool[:n]


def run_gemini(model: str, problems: List[ProblemItem], max_output_tokens: int) -> List[Dict[str, Any]]:
    extractor = AnswerExtractor()
    rows: List[Dict[str, Any]] = []
    for j, p in enumerate(tqdm(problems, desc="[baseline-gemini]")):
        prompt = build_answer_only_prompt(p.problem)
        start = time.time()
        text = generate_vertex(prompt, model=model, max_output_tokens=max_output_tokens)
        dt = time.time() - start
        ext = extractor.extract_from_text(text or "")
        pred = ext.value
        pred_str = str(pred) if pred is not None else None
        rows.append(
            {
                "problem_id": p.idx,
                "sample_idx": j,
                "source": p.source,
                "difficulty": determine_difficulty_from_source(p.source),
                "reference_answer": p.answer,
                "raw_text": (text[:500] if isinstance(text, str) else str(text)) if text else "",
                "predicted_answer": pred_str,
                "extracted": {"value": pred, "format": ext.format, "confidence": ext.confidence, "error": ext.error},
                "is_correct": bool(check_answer_correctness(p.answer, pred_str)),
                "latency_s": dt,
            }
        )
    return rows


def run_endpoint(problems: List[ProblemItem], max_new_tokens: int) -> List[Dict[str, Any]]:
    if not is_vertex_endpoint_configured():
        raise RuntimeError("AIMO_VERTEX_ENDPOINT not set.")
    rows: List[Dict[str, Any]] = []
    for j, p in enumerate(tqdm(problems, desc="[treatment-endpoint]")):
        start = time.time()
        resp = predict_vertex_endpoint_answer_only(p.problem, max_new_tokens=max_new_tokens)
        dt = time.time() - start
        pred_str = resp["predicted_answer"]
        rows.append(
            {
                "problem_id": p.idx,
                "sample_idx": j,
                "source": p.source,
                "difficulty": determine_difficulty_from_source(p.source),
                "reference_answer": p.answer,
                "raw_text": (resp["raw_text"][:500] if isinstance(resp["raw_text"], str) else str(resp["raw_text"])) if resp["raw_text"] else "",
                "predicted_answer": pred_str,
                "extracted": resp["extracted"],
                "is_correct": bool(check_answer_correctness(p.answer, pred_str)),
                "latency_s": dt,
            }
        )
    return rows


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    correct = sum(1 for r in rows if r["is_correct"])
    extracted_ok = sum(1 for r in rows if r["predicted_answer"] is not None)
    avg_latency = sum(r["latency_s"] for r in rows) / total if total else 0.0
    return {
        "total": total,
        "correct": correct,
        "accuracy": (correct / total * 100) if total else 0.0,
        "extraction_success_rate": (extracted_ok / total * 100) if total else 0.0,
        "avg_latency_s": avg_latency,
    }


def paired(b_rows: List[Dict[str, Any]], t_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    b_by = {(r["problem_id"], r["sample_idx"]): r for r in b_rows}
    t_by = {(r["problem_id"], r["sample_idx"]): r for r in t_rows}
    keys = sorted(set(b_by.keys()) & set(t_by.keys()))
    b_only = t_only = both_correct = both_wrong = 0
    for k in keys:
        bc = bool(b_by[k]["is_correct"])
        tc = bool(t_by[k]["is_correct"])
        if bc and tc:
            both_correct += 1
        elif (not bc) and (not tc):
            both_wrong += 1
        elif bc and (not tc):
            b_only += 1
        else:
            t_only += 1
    return {
        "n": len(keys),
        "contingency": {
            "both_correct": both_correct,
            "both_wrong": both_wrong,
            "baseline_only_correct": b_only,
            "treatment_only_correct": t_only,
        },
        "mcnemar_exact_p_value": mcnemar_exact_two_sided_p_value(b_only, t_only),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=41)
    ap.add_argument("--dataset", type=str, default=NUMINA_TRAINING_FILE)
    ap.add_argument("--baseline-gemini-model", type=str, default="gemini-2.5-flash")
    ap.add_argument("--max-output-tokens", type=int, default=256)
    ap.add_argument("--endpoint-max-new-tokens", type=int, default=256)
    args = ap.parse_args()

    problems = load_numina_jsonl_filtered(args.n, args.seed, args.dataset)
    print(f"Loaded {len(problems)} problems from {args.dataset} (seed={args.seed})")
    print(f"Baseline Gemini: {args.baseline_gemini_model}")
    print("Treatment: Vertex Endpoint (AIMO_VERTEX_ENDPOINT)")

    b_rows = run_gemini(args.baseline_gemini_model, problems, args.max_output_tokens)
    t_rows = run_endpoint(problems, args.endpoint_max_new_tokens)

    b_sum = summarize(b_rows)
    t_sum = summarize(t_rows)
    p = paired(b_rows, t_rows)

    print("\n================ A/B SUMMARY (ENDPOINT ANSWER-ONLY) ================")
    print(f"Baseline  accuracy={b_sum['accuracy']:.2f}%  extraction={b_sum['extraction_success_rate']:.2f}%  avg_latency={b_sum['avg_latency_s']:.2f}s")
    print(f"Treatment accuracy={t_sum['accuracy']:.2f}%  extraction={t_sum['extraction_success_rate']:.2f}%  avg_latency={t_sum['avg_latency_s']:.2f}s")
    c = p["contingency"]
    print("--------------------------------------------")
    print("Paired contingency (McNemar):")
    print(f"  baseline-only correct  : {c['baseline_only_correct']}")
    print(f"  treatment-only correct : {c['treatment_only_correct']}")
    print(f"McNemar exact p-value: {p['mcnemar_exact_p_value']:.6f}")

    ensure_dir(RESULTS_DIR)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"ab_eval_endpoint_answer_only_{os.path.splitext(args.dataset)[0]}_{args.n}_{ts}.json"
    payload = {
        "timestamp": datetime.now().isoformat(),
        "dataset": args.dataset,
        "n": args.n,
        "seed": args.seed,
        "prompt_template": "Problem -> <ANS> only",
        "baseline": {"type": "gemini", "model": args.baseline_gemini_model, "summary": b_sum, "results": b_rows},
        "treatment": {"type": "vertex_endpoint", "endpoint": os.getenv("AIMO_VERTEX_ENDPOINT"), "summary": t_sum, "results": t_rows},
        "paired": p,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

