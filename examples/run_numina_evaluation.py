"""
Run evaluation on NuminaMath Balanced Set (60 problems)
- Mixed difficulty: 10 easy, 20 medium, 30 hard
- Development/testing benchmark

난이도 상한(올림피아드·AOPS 등 hard 소스 제외):
  python examples/run_numina_evaluation.py --difficulty-at-most medium
  또는: set EVAL_DIFFICULTY_AT_MOST=medium
(`evaluation_utils.determine_difficulty_from_source` 기준)

5k 학습 JSONL(5000문항, source 모두 olympiads = hard):
  python examples/run_numina_evaluation.py --data-file numina_training_5k.jsonl

난이도 상한(medium = easy+medium)과 함께 쓰려면 소스가 섞인 전체 Numina JSONL 사용:
  set MAX_PROBLEMS=200
  python examples/run_numina_evaluation.py --data-file numinamath_full.jsonl --difficulty-at-most medium
  (MAX_PROBLEMS가 있으면 JSONL은 스트리밍으로 읽어 전체를 메모리에 올리지 않음)

기본 동작: **모델은 프로세스당 한 번만** 로드한다 (``PipelineOrchestrator`` 하나를 끝까지 재사용).

``EVAL_PROBLEM_TIMEOUT`` 을 켜면 예전에는 문제마다 서브프로세스로 돌려 **매 문제마다 가중치를 다시 로드**했다.
지금은 기본이 **인프로세스**라서 타임아웃을 켜도 서브프로세스를 쓰지 않는다 (타임아웃은 무시됨).
정말 문제마다 자식 프로세스로 끊고 싶다면 ``AIMO_EVAL_IN_PROCESS=0`` 을 설정한다 (로컬 대형 모델에는 비권장).

진단·실험 채점:
  ``AIMO_EVAL_DIAGNOSTICS=1`` (기본): 행 메타에 추출 진단 필드 추가.
  ``AIMO_EVAL_PREFER_DIAGNOSTIC_CANDIDATE=1``: 진단상 alternate 추출이 정답과 일치하면 **그 문자열로 재채점** (실험용; 기본은 끔).

Easy 세분화 (``--difficulty-at-most easy`` 와 함께 권장):
  ``--easy-stratum source`` | ``problem_type`` | ``composite``
  또는 환경 변수 ``EVAL_EASY_STRATUM`` (동일 값). 결과 JSON·요약에 ``by_easy_stratum`` 및 행 ``easy_stratum`` 추가.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
# Reduce TensorFlow oneDNN log noise (set before any tf import)
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

import json
import time
import multiprocessing
from pipeline.orchestrator import PipelineOrchestrator
from evaluation.evaluation_utils import (
    EvaluationMetrics, EvaluationResult,
    check_answer_correctness,
    classify_answer_match,
    determine_difficulty_from_source,
    determine_easy_stratum,
)
from tqdm import tqdm

from evaluation.config import (
    find_data_file,
    ensure_dir,
    RESULTS_DIR,
    NUMINA_EVAL_BALANCED_FILE,
    NUMINA_TRAINING_FILE,
)

# Optional per-problem timeout (seconds). With default in-process eval, this does not spawn subprocesses (see below).
EVAL_PROBLEM_TIMEOUT = int(os.environ.get("EVAL_PROBLEM_TIMEOUT", "0")) or None


def _env_bool_default(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


# Default True: one orchestrator, HF weights load once. Set AIMO_EVAL_IN_PROCESS=0 only if you intentionally want
# subprocess-per-problem (e.g. hard kill) and accept full model reload each time.
AIMO_EVAL_IN_PROCESS = _env_bool_default("AIMO_EVAL_IN_PROCESS", True)
EVAL_WORKERS = max(1, int(os.environ.get("EVAL_WORKERS", "1")))


def _difficulty_rank(label: str) -> int:
    return {"easy": 0, "medium": 1, "hard": 2}.get(label, 1)


def _problem_passes_difficulty_at_most(p: dict, cap: str) -> bool:
    cap = cap.strip().lower()
    if cap not in ("easy", "medium", "hard"):
        return True
    src = str(p.get("source", "unknown")).strip().lower()
    d = determine_difficulty_from_source(src)
    return _difficulty_rank(d) <= _difficulty_rank(cap)


def filter_problems_by_difficulty_at_most(problems: List[dict], cap: str) -> List[dict]:
    """cap이 medium이면 easy+medium만 남기고 hard(올림피아드 등) 소스는 제외."""
    cap = cap.strip().lower()
    if cap not in ("easy", "medium", "hard"):
        return problems
    return [p for p in problems if isinstance(p, dict) and _problem_passes_difficulty_at_most(p, cap)]


def _parse_eval_cli() -> Tuple[Optional[str], str, int, str]:
    """Returns (difficulty_cap, data_filename, workers, easy_stratum_mode)."""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument(
        "--difficulty-at-most",
        choices=("easy", "medium", "hard"),
        default=None,
    )
    p.add_argument(
        "--data-file",
        default=None,
        help="예: numina_training_5k.jsonl (기본: numina_eval_balanced.json)",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=None,
        help="문제 단위 병렬 워커 수 (기본: env EVAL_WORKERS 또는 1)",
    )
    p.add_argument(
        "--easy-stratum",
        choices=("none", "source", "problem_type", "composite"),
        default=None,
        help="easy 난이도만 세부 층화(metadata easy_stratum, summary by_easy_stratum)",
    )
    args, _ = p.parse_known_args()
    cap = args.difficulty_at_most
    if cap is None:
        e = os.environ.get("EVAL_DIFFICULTY_AT_MOST", "").strip().lower()
        if e in ("easy", "medium", "hard"):
            cap = e
    data_file = args.data_file or os.environ.get("EVAL_DATA_FILE", "").strip()
    if not data_file:
        data_file = NUMINA_EVAL_BALANCED_FILE
    workers = int(args.workers) if args.workers is not None else EVAL_WORKERS
    workers = max(1, workers)
    easy_stratum = args.easy_stratum
    if easy_stratum is None:
        ee = os.environ.get("EVAL_EASY_STRATUM", "").strip().lower()
        if ee in ("none", "source", "problem_type", "composite"):
            easy_stratum = ee
        else:
            easy_stratum = "none"
    return cap, data_file, workers, easy_stratum


def load_numina_eval() -> List[dict]:
    """호환용: 균형 60문항만 로드 (`scripts/quick_smoke_test.py` 등)."""
    return load_eval_problems(NUMINA_EVAL_BALANCED_FILE)


def load_eval_problems(
    data_filename: str,
    *,
    difficulty_cap: Optional[str] = None,
    max_collect: Optional[int] = None,
) -> List[dict]:
    """JSON 배열(.json) 또는 JSONL(.jsonl). `find_data_file`로 경로 탐색.

    JSONL이고 max_collect가 있으면 스트리밍: 조건에 맞는 항목만 최대 max_collect개까지 읽음
    (대용량 numinamath_full.jsonl + medium 필터 + 부분 평가에 사용).
    """
    path = find_data_file(data_filename)
    print(f"Loaded Numina eval from: {path}")
    if str(path).lower().endswith(".jsonl") and max_collect is not None:
        out: List[dict] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    continue
                if difficulty_cap and not _problem_passes_difficulty_at_most(obj, difficulty_cap):
                    continue
                out.append(obj)
                if len(out) >= max_collect:
                    break
        if out and isinstance(out[0], dict) and "answer" not in out[0]:
            print("  WARNING: items should have 'problem', 'answer', 'source'.")
        return out
    if str(path).lower().endswith(".jsonl"):
        out = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                out.append(json.loads(line))
        if out and isinstance(out[0], dict) and "answer" not in out[0]:
            print("  WARNING: items should have 'problem', 'answer', 'source'.")
        return out
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        if data and isinstance(data[0], dict) and "answer" not in data[0]:
            print("  WARNING: Eval items should have 'answer' per item.")
        return data
    return []


def _solve_one(problem_text, domain, variables, time_budget):
    """Worker: create orchestrator and solve one problem (for subprocess timeout)."""
    orch = PipelineOrchestrator()
    return orch.solve_problem(domain, variables, problem_text, time_budget=time_budget)


_PARALLEL_WORKER_ORCH = None


def _init_parallel_worker():
    """ProcessPool worker initializer: load one orchestrator per process."""
    global _PARALLEL_WORKER_ORCH
    _PARALLEL_WORKER_ORCH = PipelineOrchestrator()


def _solve_one_parallel(idx: int, problem_text: str):
    """Solve one problem inside a long-lived worker process."""
    global _PARALLEL_WORKER_ORCH
    if _PARALLEL_WORKER_ORCH is None:
        _PARALLEL_WORKER_ORCH = PipelineOrchestrator()
    start_time = time.time()
    result = _PARALLEL_WORKER_ORCH.solve_problem(
        domain="general_math",
        variables={},
        problem_text=problem_text,
    )
    return idx, result, (time.time() - start_time)

def evaluate_numina(
    orchestrator,
    problems,
    max_problems=None,
    *,
    dataset_name: str = "NuminaMath_Balanced",
    results_filename: str = "numina_balanced_results.json",
    gradient_filename: str = "gradient_report_numina.json",
    workers: int = 1,
    easy_stratum_mode: str = "none",
):
    """
    Evaluate on NuminaMath balanced set
    
    Args:
        orchestrator: Orchestrator instance
        problems: List of NuminaMath problems
        max_problems: Limit number of problems (for testing)
        easy_stratum_mode: ``none`` | ``source`` | ``problem_type`` | ``composite`` — easy 소스만 세부 층 라벨
    """
    if max_problems:
        problems = problems[:max_problems]
    
    metrics = EvaluationMetrics(dataset_name=dataset_name)
    metrics.start()
    
    total = len(problems)
    
    print(f"\n{'='*70}")
    print(f"Evaluating on {total} NuminaMath Problems")
    print(f"{'='*70}\n")

    use_subproc_timeout = bool(EVAL_PROBLEM_TIMEOUT) and not AIMO_EVAL_IN_PROCESS
    if use_subproc_timeout:
        print(
            "WARNING: subprocess-per-problem is ON (AIMO_EVAL_IN_PROCESS=0 + EVAL_PROBLEM_TIMEOUT). "
            "The HF model will reload for every problem — very slow.",
            file=sys.stderr,
        )
    elif EVAL_PROBLEM_TIMEOUT and AIMO_EVAL_IN_PROCESS:
        print(
            "NOTE: in-process eval — EVAL_PROBLEM_TIMEOUT does not spawn workers; timeout is not enforced per problem.",
            file=sys.stderr,
        )
    parallel_workers = max(1, int(workers))
    parallel_enabled = parallel_workers > 1 and not use_subproc_timeout

    if parallel_enabled:
        print(f"Parallel mode ON: workers={parallel_workers}")
    elif parallel_workers > 1 and use_subproc_timeout:
        print(
            "NOTE: --workers is ignored when subprocess timeout mode is enabled.",
            file=sys.stderr,
        )

    def _build_eval_result(idx: int, problem_data: dict, result: dict, solve_time: float) -> EvaluationResult:
        problem = problem_data['problem']
        reference_answer = problem_data.get('answer', '')
        source = problem_data.get('source', 'unknown')
        difficulty = determine_difficulty_from_source(source)

        eval_meta = {}
        pt = problem_data.get("problem_type")
        if pt is not None and str(pt).strip():
            eval_meta["problem_type"] = str(pt).strip()
        qt = problem_data.get("question_type")
        if qt is not None and str(qt).strip():
            eval_meta["question_type"] = str(qt).strip()

        predicted_answer = result.get('answer', 'N/A')
        is_correct = check_answer_correctness(reference_answer, predicted_answer)

        if easy_stratum_mode and easy_stratum_mode != "none":
            es = determine_easy_stratum(
                source,
                problem_type=problem_data.get("problem_type"),
                style=easy_stratum_mode,
            )
            if es:
                eval_meta["easy_stratum"] = es

        if _env_bool_default("AIMO_EVAL_DIAGNOSTICS", True):
            try:
                from evaluation.answer_diagnostics import diagnose_numina_result

                eval_meta.update(
                    diagnose_numina_result(reference_answer, predicted_answer, result)
                )
            except Exception as e:
                eval_meta["diagnostics_error"] = str(e)[:200]

            if _env_bool_default("AIMO_EVAL_PREFER_DIAGNOSTIC_CANDIDATE", False):
                ba = eval_meta.get("best_alternate_answer")
                if eval_meta.get("alternate_would_pass") and ba:
                    eval_meta["original_predicted_answer"] = predicted_answer
                    predicted_answer = ba
                    is_correct = check_answer_correctness(reference_answer, predicted_answer)
                    eval_meta["graded_with_diagnostic_candidate"] = True
                    ps = predicted_answer
                    if isinstance(ps, str) and ps.strip().upper() == "N/A":
                        ps = None
                    if ps is None or (isinstance(ps, str) and not str(ps).strip()):
                        mk = "none"
                    else:
                        mk = classify_answer_match(
                            reference_answer, str(ps), use_sympy=True
                        )
                    eval_meta["grading_match_kind"] = mk
                    eval_meta["eval_failure_axis"] = (
                        "correct" if is_correct else eval_meta.get("eval_failure_axis")
                    )
                    eval_meta["counterfactual_would_pass"] = is_correct

        fail_reason = None
        if not is_correct or result.get('method') == 'all_failed':
            ex = result.get('execution_result') or result.get('error')
            if ex and isinstance(ex, str) and ('Error:' in ex or 'failed' in ex.lower()):
                fail_reason = ex[:500]
        if result.get('method') == 'timeout':
            fail_reason = result.get('execution_result') or 'timeout'

        return EvaluationResult(
            problem_id=idx,
            problem=problem,
            reference_answer=reference_answer,
            predicted_answer=predicted_answer,
            is_correct=is_correct,
            solve_time=solve_time,
            method=result.get('method', 'unknown'),
            difficulty=difficulty,
            source=source,
            error=fail_reason,
            metadata=eval_meta if eval_meta else None,
        )

    completed = 0
    if parallel_enabled:
        futures = {}
        with ProcessPoolExecutor(
            max_workers=parallel_workers,
            initializer=_init_parallel_worker,
        ) as executor:
            for idx, problem_data in enumerate(problems):
                futures[executor.submit(_solve_one_parallel, idx, problem_data["problem"])] = idx

            for fut in tqdm(as_completed(futures), total=total, desc="Solving NuminaMath (parallel)"):
                idx = futures[fut]
                problem_data = problems[idx]
                try:
                    _, result, solve_time = fut.result()
                except Exception as e:
                    result = {
                        'answer': None,
                        'method': 'worker_exception',
                        'execution_result': str(e),
                        'error': str(e),
                    }
                    solve_time = 0.0

                eval_result = _build_eval_result(idx, problem_data, result, solve_time)
                metrics.add_result(eval_result)

                completed += 1
                status = "ok" if eval_result.is_correct else "fail"
                print(f"\n  [{completed}/{total}] {status} ({result.get('method', '?')}) #problem={idx+1}")

                if completed % 10 == 0:
                    current_metrics = metrics.calculate_metrics()
                    current_accuracy = current_metrics['accuracy']
                    print(f"Progress: {completed}/{total} | Accuracy: {current_accuracy:.1f}%")
    else:
        for idx, problem_data in enumerate(tqdm(problems, desc="Solving NuminaMath")):
            problem = problem_data['problem']
            source = problem_data.get('source', 'unknown')
            try:
                start_time = time.time()
                if use_subproc_timeout:
                    # Run in subprocess so we can timeout and always move to next problem
                    with multiprocessing.Pool(1) as pool:
                        async_res = pool.apply_async(
                            _solve_one,
                            (problem, "general_math", {}, 60.0)
                        )
                        try:
                            result = async_res.get(timeout=EVAL_PROBLEM_TIMEOUT)
                        except multiprocessing.TimeoutError:
                            result = {
                                'answer': None,
                                'method': 'timeout',
                                'execution_result': f'Problem timed out after {EVAL_PROBLEM_TIMEOUT}s',
                            }
                else:
                    # variables 빈 dict 유지: 정답 레이블을 파이프라인에 넣지 않음(유출 방지).
                    # 최종 채점은 아래 check_answer_correctness(reference, pred)만 사용.
                    result = orchestrator.solve_problem(
                        domain="general_math",
                        variables={},
                        problem_text=problem
                    )
                solve_time = time.time() - start_time
                eval_result = _build_eval_result(idx, problem_data, result, solve_time)
                metrics.add_result(eval_result)
                status = "ok" if eval_result.is_correct else "fail"
                print(f"\n  [{idx+1}/{total}] {status} ({result.get('method', '?')})")

                if (idx + 1) % 10 == 0:
                    current_metrics = metrics.calculate_metrics()
                    current_accuracy = current_metrics['accuracy']
                    print(f"Progress: {idx+1}/{total} | Accuracy: {current_accuracy:.1f}%")
            except Exception as e:
                print(f"\nError on problem {idx} ({source}): {str(e)}")
                reference_answer = problem_data.get('answer', '')
                difficulty = determine_difficulty_from_source(source)
                eval_meta = {}
                pt = problem_data.get("problem_type")
                if pt is not None and str(pt).strip():
                    eval_meta["problem_type"] = str(pt).strip()
                qt = problem_data.get("question_type")
                if qt is not None and str(qt).strip():
                    eval_meta["question_type"] = str(qt).strip()
                eval_result = EvaluationResult(
                    problem_id=idx,
                    problem=problem,
                    reference_answer=reference_answer,
                    is_correct=False,
                    error=str(e),
                    difficulty=difficulty,
                    source=source,
                    metadata=eval_meta if eval_meta else None,
                )
                metrics.add_result(eval_result)
    
    metrics.finish()
    
    # Print summary
    metrics.print_summary()
    
    # If 0% correct, print diagnostic to help debug
    correct_count = sum(1 for r in metrics.results if r.is_correct)
    if correct_count == 0 and metrics.results:
        print("\n" + "="*70)
        print("DIAGNOSTIC (0% accuracy - possible causes below)")
        print("="*70)
        try:
            from pipeline.reasoning_utils import sympy_equivalent
            import sympy
            print("  SymPy: available")
        except Exception as e:
            print(f"  SymPy: NOT available ({e}) - equivalence check may be strict.")
        print("  Sample: first 3 problems [reference vs predicted]")
        for i, r in enumerate(metrics.results[:3]):
            ref = (r.reference_answer or "")[:60]
            pred = (r.predicted_answer if r.predicted_answer is not None else "None")[:60]
            print(f"    [{i+1}] ref={ref!r}  pred={pred!r}  method={r.method}")
        preds = [r.predicted_answer for r in metrics.results]
        refs_empty = all(not (r.reference_answer or "").strip() for r in metrics.results)
        if refs_empty:
            print("  → All reference answers are empty (check numina_eval_balanced.json has 'answer' per item).")
        if all(p is None for p in preds):
            print("  → All predicted answers are None (pipeline may be failing: model load, timeout, or executor).")
        elif all(p == "N/A" or p == "" for p in preds):
            print("  → All predicted are N/A or empty (answer extraction or orchestrator return check).")
        print("  See docs/run-eval/ZERO_ACCURACY_DEBUG.md for causes and fixes.")
        print("="*70 + "\n")
    
    # Save results
    ensure_dir(RESULTS_DIR)
    output_path = metrics.save_results(
        output_dir=str(RESULTS_DIR),
        filename=results_filename,
    )
    print(f"Results saved to: {output_path}")

    final_metrics = metrics.calculate_metrics()
    try:
        from evaluation.run_helpers import save_gradient_and_error_summary, print_gradient_summary
        grad_path = save_gradient_and_error_summary(
            final_metrics,
            [r.to_dict() for r in metrics.results],
            output_dir=RESULTS_DIR,
            dataset_name=dataset_name,
            filename=gradient_filename,
        )
        print(f"Gradient report saved to: {grad_path}")
        print_gradient_summary(final_metrics)
    except Exception as e:
        print(f"[Gradient report skip] {e}")

    return final_metrics['accuracy'], [r.to_dict() for r in metrics.results]

def main():
    difficulty_cap, data_filename, workers, easy_stratum = _parse_eval_cli()
    max_problems_env = os.environ.get("MAX_PROBLEMS")
    max_problems = int(max_problems_env) if max_problems_env is not None and max_problems_env.isdigit() else None
    path_resolved = find_data_file(data_filename)
    stem = Path(path_resolved).stem

    print("="*70)
    print("NuminaMath Evaluation")
    print("="*70)
    print(f"\nData file: {data_filename} ({path_resolved.name})")
    if stem == Path(NUMINA_EVAL_BALANCED_FILE).stem:
        print("Subset: Balanced 60 (10 easy / 20 medium / 30 hard)")
    elif stem == Path(NUMINA_TRAINING_FILE).stem:
        print("Subset: training JSONL (기본 5000 lines in repo)")
    elif stem == "numinamath_full":
        print("Subset: full Numina JSONL (mixed sources; --difficulty-at-most medium 권장)")
    if difficulty_cap:
        print(
            f"Difficulty: at most '{difficulty_cap}' (easy+medium만 원하면 medium) "
            "- olympiads/amc_aime/aops 등 hard 소스 제외"
        )
    print("Purpose: Development and mixed-difficulty testing")
    print(f"Workers: {workers}")
    if difficulty_cap == "easy" and easy_stratum != "none":
        print(f"Easy stratum mode: {easy_stratum} (--easy-stratum / EVAL_EASY_STRATUM)")
    print("="*70)
    
    # Load problems
    print("\nLoading problems...")
    stream_jsonl = str(path_resolved).lower().endswith(".jsonl") and max_problems is not None
    if stream_jsonl:
        problems = load_eval_problems(
            data_filename,
            difficulty_cap=difficulty_cap,
            max_collect=max_problems,
        )
        n_loaded = len(problems)
        print(f"[OK] {n_loaded} problems (JSONL stream, max_collect={max_problems})")
        if difficulty_cap:
            print(f"  (difficulty-at-most={difficulty_cap} applied while reading)")
        if n_loaded < max_problems:
            print(
                f"  WARNING: only {n_loaded} items matched before EOF.",
                file=sys.stderr,
            )
    else:
        problems = load_eval_problems(data_filename)
        n_loaded = len(problems)
        print(f"[OK] Loaded {n_loaded} problems")
        if difficulty_cap:
            problems = filter_problems_by_difficulty_at_most(problems, difficulty_cap)
            print(
                f"After difficulty-at-most={difficulty_cap}: {n_loaded} -> {len(problems)} problems"
            )
            if not problems:
                print("ERROR: no problems left after difficulty filter.", file=sys.stderr)
                if stem == Path(NUMINA_TRAINING_FILE).stem:
                    print(
                        "hint: numina_training_5k.jsonl is all source=olympiads; "
                        "use --data-file numinamath_full.jsonl for mixed sources.",
                        file=sys.stderr,
                    )
                raise SystemExit(1)

    # Initialize orchestrator
    print("\nInitializing solver...")
    orchestrator = PipelineOrchestrator()

    # Run evaluation (MAX_PROBLEMS env: full set if unset; stream path already limited)
    suffix = f"_max_{difficulty_cap}" if difficulty_cap else ""
    ds_name = f"NuminaEval_{stem}{suffix}"
    res_file = f"{stem}_results{suffix}.json"
    grad_file = f"gradient_report_{stem}{suffix}.json"
    print("\nStarting evaluation...")
    accuracy, results = evaluate_numina(
        orchestrator,
        problems,
        max_problems=max_problems,
        dataset_name=ds_name,
        results_filename=res_file,
        gradient_filename=grad_file,
        workers=workers,
        easy_stratum_mode=easy_stratum,
    )
    
    # Analysis
    print("\n" + "="*70)
    print("Performance Analysis")
    print("="*70)
    print(f"Your System: {accuracy:.2f}%")
    print("\nExpected performance ranges:")
    print("  Easy problems (Orca): 80-90%")
    print("  Medium problems (K-12): 60-70%")
    print("  Hard problems (Olympiad): 30-40%")
    print("="*70)

if __name__ == "__main__":
    main()
