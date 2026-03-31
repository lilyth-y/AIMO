"""
A/B evaluation on 1000 problems (paired comparison).

Default:
  - Baseline: local pipeline (Vertex disabled)
  - Treatment: Vertex AI with gemini-2.5-flash-lite

Outputs:
  - results/ab_eval_<dataset>_<n>_<timestamp>.json (paired + per-condition summaries)

Notes:
  - Uses Numina 5k JSONL by default and filters out non-numeric answers (e.g. "proof").
  - For statistical evidence, prints McNemar exact p-value on paired correctness.
  - Stratified McNemar by difficulty / problem_type / question_type (JSON + console when discordant_n > 0).

  Model load: default ``AIMO_EVAL_IN_PROCESS=1`` (one orchestrator per condition, weights once).
  Subprocess-per-problem only if ``AIMO_EVAL_IN_PROCESS=0`` and ``--problem-timeout`` is set.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import multiprocessing
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from tqdm import tqdm

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, "src"))

# Reduce TensorFlow oneDNN log noise (match other examples)
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

from evaluation.config import find_data_file, ensure_dir, RESULTS_DIR, NUMINA_TRAINING_FILE
from evaluation.evaluation_utils import (
    EvaluationMetrics,
    EvaluationResult,
    check_answer_correctness,
    determine_difficulty_from_source,
    mcnemar_exact_two_sided_p_value,
    stratified_mcnemar_paired_ab,
)
from pipeline.orchestrator import PipelineOrchestrator


@dataclass
class ProblemItem:
    idx: int
    problem: str
    answer: str
    source: str
    problem_type: Optional[str] = None
    question_type: Optional[str] = None


def _looks_non_numeric_answer(ans: str) -> bool:
    if ans is None:
        return True
    s = str(ans).strip().lower()
    if not s:
        return True
    # Numina has many proof-only entries; exclude for numeric answer eval.
    if s in {"proof", "prove", "proved", "true", "false"}:
        return True
    return False


def _solve_one(problem_text: str, time_budget: float) -> Dict[str, Any]:
    """Worker for per-problem subprocess timeout (must be top-level for Windows spawn)."""
    orch = PipelineOrchestrator()
    return orch.solve_problem(domain="general_math", variables={}, problem_text=problem_text, time_budget=time_budget)


def load_numina_jsonl_filtered(
    n: int,
    seed: int,
    filename: str = NUMINA_TRAINING_FILE,
) -> List[ProblemItem]:
    path = find_data_file(filename)
    rng = __import__("random").Random(seed)

    items: List[ProblemItem] = []
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
            pt = obj.get("problem_type")
            qt = obj.get("question_type")
            pool.append(
                ProblemItem(
                    idx=i,
                    problem=problem,
                    answer=str(answer),
                    source=str(source),
                    problem_type=str(pt).strip() if pt is not None and str(pt).strip() else None,
                    question_type=str(qt).strip() if qt is not None and str(qt).strip() else None,
                )
            )

    if len(pool) < n:
        raise RuntimeError(
            f"샘플링 가능한 문제가 부족합니다. requested={n}, available={len(pool)}. "
            f"dataset={path}"
        )

    rng.shuffle(pool)
    items = pool[:n]
    return items


def _eval_in_process_default_true() -> bool:
    """Default True: reuse one PipelineOrchestrator (single model load). Set AIMO_EVAL_IN_PROCESS=0 for subprocess mode."""
    raw = os.environ.get("AIMO_EVAL_IN_PROCESS")
    if raw is None or str(raw).strip() == "":
        return True
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def _set_env(overrides: Dict[str, Optional[str]]) -> None:
    """
    Apply env overrides:
      - value is None => delete if exists
      - else set to that string
    """
    for k, v in overrides.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = str(v)


def run_condition(
    name: str,
    problems: List[ProblemItem],
    time_budget: float,
    env_overrides: Dict[str, Optional[str]],
    problem_timeout: Optional[float] = None,
) -> Tuple[EvaluationMetrics, List[Dict[str, Any]]]:
    _set_env(env_overrides)
    eval_in_process = _eval_in_process_default_true()
    use_subproc = bool(problem_timeout) and not eval_in_process
    orch = None if use_subproc else PipelineOrchestrator()

    metrics = EvaluationMetrics(dataset_name=name)
    metrics.start()

    rows: List[Dict[str, Any]] = []
    for j, p in enumerate(tqdm(problems, desc=f"[{name}] Solving")):
        difficulty = determine_difficulty_from_source(p.source)
        row_meta: Dict[str, Any] = {}
        if p.problem_type:
            row_meta["problem_type"] = p.problem_type
        if p.question_type:
            row_meta["question_type"] = p.question_type
        start = time.time()
        error = None
        try:
            if use_subproc:
                # Rare: subprocess per problem (reloads model each time). Default is in-process.
                with multiprocessing.Pool(1) as pool:
                    async_res = pool.apply_async(_solve_one, (p.problem, time_budget))
                    try:
                        result = async_res.get(timeout=problem_timeout)
                    except multiprocessing.TimeoutError:
                        result = {"answer": None, "method": "timeout", "execution_result": f"Problem timed out after {problem_timeout}s"}
            else:
                result = orch.solve_problem(
                    domain="general_math",
                    variables={},
                    problem_text=p.problem,
                    time_budget=time_budget,
                )
            pred = result.get("answer", None)
            method = result.get("method", "unknown")
            is_correct = check_answer_correctness(p.answer, pred)
            if not is_correct or method == "all_failed":
                ex = result.get("execution_result") or result.get("error")
                if isinstance(ex, str) and ex:
                    error = ex[:500]
        except Exception as e:
            pred = None
            method = "exception"
            is_correct = False
            error = str(e)[:500]
        solve_time = time.time() - start

        eval_result = EvaluationResult(
            problem_id=p.idx,
            problem=p.problem,
            reference_answer=p.answer,
            predicted_answer=str(pred) if pred is not None else None,
            is_correct=is_correct,
            solve_time=solve_time,
            method=method,
            difficulty=difficulty,
            source=p.source,
            error=error,
            metadata={**row_meta, "sample_idx": j},
        )
        metrics.add_result(eval_result)
        rows.append(
            {
                "problem_id": p.idx,
                "sample_idx": j,
                "source": p.source,
                "difficulty": difficulty,
                "problem_type": p.problem_type,
                "question_type": p.question_type,
                "reference_answer": p.answer,
                "predicted_answer": str(pred) if pred is not None else None,
                "is_correct": is_correct,
                "method": method,
                "solve_time": solve_time,
                "error": error,
            }
        )

    metrics.finish()
    return metrics, rows


def paired_summary(
    baseline_rows: List[Dict[str, Any]],
    treatment_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    # Match by problem_id (and sample_idx as fallback)
    base_by_id = {(r["problem_id"], r["sample_idx"]): r for r in baseline_rows}
    treat_by_id = {(r["problem_id"], r["sample_idx"]): r for r in treatment_rows}

    keys = sorted(set(base_by_id.keys()) & set(treat_by_id.keys()))
    if not keys:
        raise RuntimeError("paired join 실패: 공통 키가 없습니다.")

    both_correct = 0
    both_wrong = 0
    b_only = 0  # baseline correct, treatment wrong
    t_only = 0  # baseline wrong, treatment correct

    paired: List[Dict[str, Any]] = []
    for k in keys:
        b = base_by_id[k]
        t = treat_by_id[k]
        bc = bool(b["is_correct"])
        tc = bool(t["is_correct"])
        if bc and tc:
            both_correct += 1
        elif (not bc) and (not tc):
            both_wrong += 1
        elif bc and (not tc):
            b_only += 1
        else:
            t_only += 1
        paired.append(
            {
                "problem_id": b["problem_id"],
                "sample_idx": b["sample_idx"],
                "source": b["source"],
                "difficulty": b["difficulty"],
                "problem_type": b.get("problem_type"),
                "question_type": b.get("question_type"),
                "reference_answer": b["reference_answer"],
                "baseline": {
                    "predicted_answer": b["predicted_answer"],
                    "is_correct": bc,
                    "method": b["method"],
                    "error": b["error"],
                },
                "treatment": {
                    "predicted_answer": t["predicted_answer"],
                    "is_correct": tc,
                    "method": t["method"],
                    "error": t["error"],
                },
            }
        )

    p_value = mcnemar_exact_two_sided_p_value(b_only, t_only)
    stratified = {
        "difficulty": stratified_mcnemar_paired_ab(paired, "difficulty"),
        "problem_type": stratified_mcnemar_paired_ab(paired, "problem_type"),
        "question_type": stratified_mcnemar_paired_ab(paired, "question_type"),
    }
    return {
        "n": len(keys),
        "contingency": {
            "both_correct": both_correct,
            "both_wrong": both_wrong,
            "baseline_only_correct": b_only,
            "treatment_only_correct": t_only,
        },
        "mcnemar_exact_p_value": p_value,
        "stratified_mcnemar": stratified,
        "paired_results": paired,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=41)
    ap.add_argument("--time-budget", type=float, default=float(os.getenv("AIMO_TIME_BUDGET", "60")))
    ap.add_argument(
        "--problem-timeout",
        type=float,
        default=float(os.getenv("EVAL_PROBLEM_TIMEOUT", "0")) or None,
        help="Seconds (unused for kill when AIMO_EVAL_IN_PROCESS=1, default). Subprocess+reload per problem only if AIMO_EVAL_IN_PROCESS=0.",
    )
    ap.add_argument("--dataset", type=str, default=NUMINA_TRAINING_FILE)

    # Baseline (local)
    ap.add_argument("--baseline-name", type=str, default=None)
    ap.add_argument("--baseline-model", type=str, default=os.getenv("OMI_MODEL", "Qwen/Qwen2.5-Coder-1.5B-Instruct"))
    # Alternative baseline: Vertex model (recommended for 1000-problem A/B speed)
    ap.add_argument(
        "--baseline-vertex-model",
        type=str,
        default=None,
        help="Set to run baseline on Vertex too (e.g. gemini-1.5-flash-002). If set, local baseline is skipped.",
    )

    # Treatment (Vertex)
    ap.add_argument("--treatment-name", type=str, default="treatment_vertex_gemini_2_5_flash_lite")
    ap.add_argument("--gcp-project", type=str, default=os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0300734101"))
    ap.add_argument("--vertex-location", type=str, default=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"))
    ap.add_argument("--vertex-model", type=str, default=os.getenv("VERTEX_AI_MODEL", "gemini-2.5-flash-lite"))
    args = ap.parse_args()

    # Make run labels unambiguous by default.
    if args.baseline_name is None:
        if args.baseline_vertex_model:
            args.baseline_name = f"baseline_vertex_{args.baseline_vertex_model}"
        else:
            args.baseline_name = "baseline_local"

    if args.treatment_name == "treatment_vertex_gemini_2_5_flash_lite" and args.vertex_model != "gemini-2.5-flash-lite":
        args.treatment_name = f"treatment_vertex_{args.vertex_model}"

    problems = load_numina_jsonl_filtered(n=args.n, seed=args.seed, filename=args.dataset)
    print(f"Loaded {len(problems)} problems from {args.dataset} (seed={args.seed})")

    if args.baseline_vertex_model:
        # Baseline: Vertex model (fast, consistent setup for 1000 problems)
        baseline_env = {
            "GOOGLE_CLOUD_PROJECT": args.gcp_project,
            "GOOGLE_CLOUD_LOCATION": args.vertex_location,
            "VERTEX_AI_MODEL": args.baseline_vertex_model,
        }
    else:
        # Baseline: ensure Vertex is disabled; force a small local model (optional)
        baseline_env = {
            "GOOGLE_CLOUD_PROJECT": None,
            "GCP_PROJECT": None,
            "GOOGLE_CLOUD_LOCATION": None,
            "VERTEX_AI_LOCATION": None,
            "VERTEX_AI_MODEL": None,
            "GOOGLE_GENAI_API_KEY": None,
            "VERTEX_AI_API_KEY": None,
            "OMI_MODEL": args.baseline_model,
        }

    # Treatment: enable Vertex + model
    treatment_env = {
        "GOOGLE_CLOUD_PROJECT": args.gcp_project,
        "GOOGLE_CLOUD_LOCATION": args.vertex_location,
        "VERTEX_AI_MODEL": args.vertex_model,
    }

    print(f"Baseline:  {args.baseline_name}")
    print(f"Treatment: {args.treatment_name}")
    if args.problem_timeout:
        if _eval_in_process_default_true():
            print(
                f"NOTE: --problem-timeout={args.problem_timeout} but AIMO_EVAL_IN_PROCESS defaults to 1 — "
                "using one orchestrator per condition (model loads once per condition); wall timeout not enforced."
            )
        else:
            print(
                f"WARNING: AIMO_EVAL_IN_PROCESS=0 — subprocess per problem; model reloads each problem (slow)."
            )

    b_metrics, b_rows = run_condition(args.baseline_name, problems, args.time_budget, baseline_env, problem_timeout=args.problem_timeout)
    t_metrics, t_rows = run_condition(args.treatment_name, problems, args.time_budget, treatment_env, problem_timeout=args.problem_timeout)

    paired = paired_summary(b_rows, t_rows)
    b_sum = b_metrics.calculate_metrics()
    t_sum = t_metrics.calculate_metrics()

    print("\n================ A/B SUMMARY ================")
    print(f"Baseline:  {args.baseline_name}  accuracy={b_sum['accuracy']:.2f}%  errors={b_sum['error_rate']:.2f}%")
    print(f"Treatment: {args.treatment_name}  accuracy={t_sum['accuracy']:.2f}%  errors={t_sum['error_rate']:.2f}%")
    print("--------------------------------------------")
    c = paired["contingency"]
    print("Paired contingency (McNemar):")
    print(f"  both correct           : {c['both_correct']}")
    print(f"  both wrong             : {c['both_wrong']}")
    print(f"  baseline-only correct  : {c['baseline_only_correct']}")
    print(f"  treatment-only correct : {c['treatment_only_correct']}")
    print(f"McNemar exact p-value: {paired['mcnemar_exact_p_value']:.6f}")

    sm = paired.get("stratified_mcnemar") or {}
    if sm:
        print("\nStratified McNemar (layers with discordant_n > 0 only; no multiplicity adjustment):")
        for layer, block in sm.items():
            strata = (block or {}).get("strata") or {}
            printed = False
            for slab, st in sorted(strata.items()):
                dn = int(st.get("discordant_n", 0))
                if dn <= 0:
                    continue
                printed = True
                print(
                    f"  [{layer}] {slab}: n_pairs={st['n_pairs']} discordant={dn} "
                    f"b_only={st['baseline_only_correct']} t_only={st['treatment_only_correct']} "
                    f"p={st['mcnemar_exact_p_value']:.6f}"
                )
            if not printed:
                print(f"  [{layer}] (no discordant pairs)")

    ensure_dir(RESULTS_DIR)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"ab_eval_{os.path.splitext(args.dataset)[0]}_{args.n}_{ts}.json"
    payload = {
        "timestamp": datetime.now().isoformat(),
        "dataset": args.dataset,
        "n": args.n,
        "seed": args.seed,
        "time_budget": args.time_budget,
        "baseline": {
            "name": args.baseline_name,
            "env": baseline_env,
            "summary": b_sum,
            "results": b_rows,
        },
        "treatment": {
            "name": args.treatment_name,
            "env": treatment_env,
            "model": args.vertex_model,
            "summary": t_sum,
            "results": t_rows,
        },
        "paired": {
            "summary": {k: v for k, v in paired.items() if k != "paired_results"},
            "paired_results": paired["paired_results"],
        },
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

