"""
Numina JSONL에서 **휴리스틱으로** ‘덜 애매한’ eval 서브셋을 만든다.

- 수동 검수·라벨링으로 `trusted: true`를 붙인 JSONL이 **정답**이지만,
  그 전 단계로 소스·답 길이·문제 길이로 1차 필터링할 때 사용한다.
- 결과는 `problem` / `answer` / `source` / `idx` / `filters` 메타를 유지한다.

예:
  python scripts/eval/build_trusted_eval_subset.py \\
    --data-file numinamath_full.jsonl \\
    --sources orca_math,gsm8k \\
    --max-answer-len 100 --max-problem-len 6000 \\
    --limit 400 --output data/eval/trusted_subset_seed.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from evaluation.config import find_data_file  # noqa: E402


def _parse_sources(s: str) -> Optional[Set[str]]:
    if not (s or "").strip():
        return None
    return {p.strip().lower() for p in s.split(",") if p.strip()}


def main() -> int:
    ap = argparse.ArgumentParser(description="Numina JSONL → 신뢰도 1차 필터 서브셋")
    ap.add_argument("--data-file", required=True, help="find_data_file 기준 파일명")
    ap.add_argument(
        "--sources",
        default="orca_math,gsm8k",
        help="쉼표 구분 소스 허용(소문자). 비우면 소스 필터 없음.",
    )
    ap.add_argument("--max-answer-len", type=int, default=120)
    ap.add_argument("--max-problem-len", type=int, default=8000)
    ap.add_argument("--limit", type=int, default=500, help="최대 출력 행 수")
    ap.add_argument("--output", required=True, help="출력 JSONL 경로")
    args = ap.parse_args()

    allow = _parse_sources(args.sources)
    path = find_data_file(args.data_file)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    scanned = 0
    with open(path, "r", encoding="utf-8") as inf, open(out_path, "w", encoding="utf-8") as outf:
        for i, line in enumerate(inf):
            line = line.strip()
            if not line:
                continue
            scanned += 1
            try:
                obj: Dict[str, Any] = json.loads(line)
            except Exception:
                continue
            problem = obj.get("problem") or ""
            answer = obj.get("answer")
            src_raw = obj.get("source") or "unknown"
            src = str(src_raw).strip().lower()
            if not isinstance(problem, str) or not problem.strip():
                continue
            if allow is not None and src not in allow:
                continue
            if len(problem) > int(args.max_problem_len):
                continue
            ans_s = str(answer).strip() if answer is not None else ""
            if not ans_s or len(ans_s) > int(args.max_answer_len):
                continue
            row = dict(obj)
            row["idx"] = i
            row["trusted_seed"] = True
            row["subset_filters"] = {
                "sources": sorted(allow) if allow else None,
                "max_answer_len": args.max_answer_len,
                "max_problem_len": args.max_problem_len,
            }
            outf.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1
            if written >= int(args.limit):
                break

    summary = {
        "input": str(path),
        "output": str(out_path.resolve()),
        "scanned_lines": scanned,
        "written": written,
        "filters": {
            "sources": sorted(allow) if allow else None,
            "max_answer_len": args.max_answer_len,
            "max_problem_len": args.max_problem_len,
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
