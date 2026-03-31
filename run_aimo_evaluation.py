"""
AIMO Progress Prize reference problems (5 IMO-level items) from JSONL.

Default data: `archive/legacy/AIMO_core/data/aimo_problems.jsonl`
Override: `AIMO_REFERENCE_JSONL` = absolute or repo-relative path.

Docker `entrypoint.sh` `aimo` mode invokes this from repo root.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from evaluation.config import RESULTS_DIR, ensure_dir  # noqa: E402
from evaluation.evaluation_utils import (  # noqa: E402
    EvaluationMetrics,
    EvaluationResult,
    check_answer_correctness,
)
from pipeline.orchestrator import PipelineOrchestrator  # noqa: E402
from tqdm import tqdm  # noqa: E402


def _default_jsonl() -> Path:
    env = os.environ.get("AIMO_REFERENCE_JSONL")
    if env:
        p = Path(env)
        if not p.is_file():
            p = ROOT / env
        return p
    return ROOT / "archive" / "legacy" / "AIMO_core" / "data" / "aimo_problems.jsonl"


def load_problems(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Reference JSONL not found: {path}\n"
            "Set AIMO_REFERENCE_JSONL or add archive/legacy/AIMO_core/data/aimo_problems.jsonl"
        )
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main() -> None:
    data_path = _default_jsonl()
    print("=" * 70)
    print("AIMO reference problem evaluation")
    print("=" * 70)
    print(f"Data: {data_path}")

    problems = load_problems(data_path)
    print(f"Problems: {len(problems)}")

    orchestrator = PipelineOrchestrator()
    metrics = EvaluationMetrics(dataset_name="AIMO_Reference")
    metrics.start()

    for idx, row in enumerate(tqdm(problems, desc="AIMO reference")):
        pid = row.get("id", str(idx))
        problem = row["problem"]
        reference_answer = str(row.get("answer", ""))

        try:
            t0 = time.time()
            result = orchestrator.solve_problem(
                domain="general_math",
                variables={},
                problem_text=problem,
            )
            solve_time = time.time() - t0
            predicted = result.get("answer", "N/A")
            is_correct = check_answer_correctness(reference_answer, predicted)

            metrics.add_result(
                EvaluationResult(
                    problem_id=idx,
                    problem=problem,
                    reference_answer=reference_answer,
                    predicted_answer=predicted,
                    is_correct=is_correct,
                    solve_time=solve_time,
                    method=result.get("method", "unknown"),
                    difficulty="hard",
                    source="aimo_reference",
                    metadata={"external_id": pid},
                )
            )
        except Exception as e:
            print(f"\nError on {pid}: {e}")
            metrics.add_result(
                EvaluationResult(
                    problem_id=idx,
                    problem=problem,
                    reference_answer=reference_answer,
                    is_correct=False,
                    error=str(e),
                    difficulty="hard",
                    source="aimo_reference",
                    metadata={"external_id": pid},
                )
            )

    metrics.finish()
    metrics.print_summary()

    ensure_dir(RESULTS_DIR)
    out = metrics.save_results(
        output_dir=str(RESULTS_DIR),
        filename="aimo_evaluation_results.json",
    )
    print(f"Results saved to: {out}")


if __name__ == "__main__":
    main()
