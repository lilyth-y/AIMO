"""
연구 프로토콜 Arm A — Baseline-LLM (오케스트레이터 없이 직접 생성·채점).

`eval_hf_local_quality.py` 를 고정 인자로 호출한다 (동일 채점·형식 게이트).

사용:
  python scripts/research/run_arm_a_baseline_eval.py
  set AIMO_RESEARCH_MODEL=Qwen/Qwen2.5-Math-7B-Instruct
  python scripts/research/run_arm_a_baseline_eval.py --n-problems 50 --seed 99

환경변수:
  AIMO_RESEARCH_MODEL — HF 모델 ID 또는 로컬 머지 경로 (기본: Qwen2.5-Math-7B-Instruct)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_EVAL = _ROOT / "scripts" / "eval_hf_local_quality.py"


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Arm A: Baseline-LLM 로컬 평가 (프로토콜 고정)")
    ap.add_argument("--n-problems", type=int, default=100)
    ap.add_argument("--seed", type=int, default=41)
    ap.add_argument("--device", choices=("auto", "cpu"), default="auto")
    ap.add_argument("--max-format-retries", type=int, default=3)
    ap.add_argument("--model", default=os.getenv("AIMO_RESEARCH_MODEL", "Qwen/Qwen2.5-Math-7B-Instruct"))
    args = ap.parse_args()

    if not _EVAL.is_file():
        print(f"Missing {_EVAL}", file=sys.stderr)
        return 1

    out_dir = _ROOT / "results" / "research"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = out_dir / f"arm_a_baseline_{args.seed}_{args.n_problems}p.jsonl"

    cmd = [
        sys.executable,
        str(_EVAL),
        "--model",
        args.model,
        "--n-problems",
        str(args.n_problems),
        "--seed",
        str(args.seed),
        "--device",
        args.device,
        "--max-format-retries",
        str(args.max_format_retries),
        "--output",
        str(out_jsonl),
    ]
    print("Arm A (Baseline-LLM):", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=str(_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
