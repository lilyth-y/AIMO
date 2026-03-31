"""
연구 도구(Arm A 래퍼, 비교기)가 레포에서 문제 없이 동작하는지 빠르게 확인.

  python scripts/research/verify_research_structure.py

- eval_hf_local_quality.py 존재
- compare_research_arms: 최소 JSONL로 짝 비교 1회
- (선택) orchestrator.solve_problem 시그니처 import

종료 코드 0 = 통과, 1 = 실패.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def check_paths() -> list[str]:
    errs: list[str] = []
    p = _ROOT / "scripts" / "eval_hf_local_quality.py"
    if not p.is_file():
        errs.append(f"Missing {p}")
    p2 = _ROOT / "scripts" / "research" / "compare_research_arms.py"
    if not p2.is_file():
        errs.append(f"Missing {p2}")
    p3 = _ROOT / "scripts" / "research" / "run_arm_a_baseline_eval.py"
    if not p3.is_file():
        errs.append(f"Missing {p3}")
    p4 = _ROOT / "scripts" / "research" / "run_arm_b_full_pipeline_eval.py"
    if not p4.is_file():
        errs.append(f"Missing {p4}")
    return errs


def check_compare_minimal() -> tuple[bool, str]:
    """두 개의 동형 JSONL로 비교기 실행."""
    import subprocess

    rows = [
        {"problem_id": 1, "is_correct": True, "strict_format_ok": True},
        {"problem_id": 2, "is_correct": False, "strict_format_ok": False},
    ]
    line = json.dumps(rows[0], ensure_ascii=False) + "\n" + json.dumps(rows[1], ensure_ascii=False) + "\n"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        pa = td / "a.jsonl"
        pb = td / "b.jsonl"
        pa.write_text(line, encoding="utf-8")
        pb.write_text(line, encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(_ROOT / "scripts" / "research" / "compare_research_arms.py"), "--a", str(pa), "--b", str(pb)],
            capture_output=True,
            text=True,
            cwd=str(_ROOT),
        )
        if r.returncode != 0:
            return False, (r.stderr or r.stdout or "compare failed")
        if "n_paired" not in (r.stdout or ""):
            return False, "unexpected compare output"
        return True, ""


def check_orchestrator_import() -> tuple[bool, str]:
    """solve_problem 존재만 확인 (무거운 실행 없음)."""
    src = _ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    try:
        from pipeline.orchestrator import PipelineOrchestrator

        o = PipelineOrchestrator()
        if not callable(getattr(o, "solve_problem", None)):
            return False, "solve_problem not callable"
        return True, ""
    except Exception as e:
        return False, f"import orchestrator: {e}"


def main() -> int:
    errs = check_paths()
    if errs:
        for e in errs:
            print("FAIL:", e, file=sys.stderr)
        return 1

    ok, msg = check_compare_minimal()
    if not ok:
        print("FAIL: compare_research_arms:", msg, file=sys.stderr)
        return 1
    print("OK: compare_research_arms minimal paired run")

    ok2, msg2 = check_orchestrator_import()
    if not ok2:
        print("WARN:", msg2, file=sys.stderr)
    else:
        print("OK: PipelineOrchestrator.solve_problem importable")

    print("OK: verify_research_structure passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
