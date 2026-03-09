"""
P6: 평가 결과로 문서 표 업데이트용 스크립트

사용법:
  python scripts/update_math_level_from_results.py [results/numina_balanced_results.json]
  python scripts/update_math_level_from_results.py results/numina_balanced_results.json results/aime_results.json

results JSON은 evaluation_utils.save_results() 형식(또는 results 리스트 + total/correct 등)을 기대합니다.
출력: docs/MATH_REASONING_LEVEL_AND_IMPROVEMENTS.md 의 "현재 수준" 칸에 붙여넣을 수 있는 문장/표 조각.
"""

import json
import sys
from pathlib import Path


def load_results(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def summarize(data: dict, name: str) -> dict:
    """정확도·난이도별 요약 추출. save_results() 형식(summary + results) 또는 단순 메트릭 지원."""
    out = {"name": name, "accuracy": None, "total": None, "by_difficulty": {}}
    # save_results() 형식: summary 안에 메트릭
    summary = data.get("summary") or data
    out["total"] = summary.get("total")
    out["accuracy"] = summary.get("accuracy")
    if out["accuracy"] is None and out["total"] and summary.get("correct") is not None:
        out["accuracy"] = (summary["correct"] / out["total"] * 100) if out["total"] else 0
    bd = summary.get("by_difficulty") or summary.get("difficulty_accuracy") or {}
    for k, v in bd.items():
        if isinstance(v, dict) and "accuracy" in v:
            out["by_difficulty"][k] = v["accuracy"]
        elif isinstance(v, (int, float)):
            out["by_difficulty"][k] = float(v)
    # results만 있으면 직접 집계
    if "results" in data and (out["accuracy"] is None or not out["by_difficulty"]):
        results = data["results"]
        total = len(results)
        correct = sum(1 for r in results if r.get("is_correct"))
        if out["total"] is None:
            out["total"] = total
        if out["accuracy"] is None:
            out["accuracy"] = (correct / total * 100) if total else 0
        by_diff = {}
        for r in results:
            d = r.get("difficulty") or "unknown"
            if d not in by_diff:
                by_diff[d] = {"total": 0, "correct": 0}
            by_diff[d]["total"] += 1
            if r.get("is_correct"):
                by_diff[d]["correct"] += 1
        if not out["by_difficulty"]:
            for d, s in by_diff.items():
                out["by_difficulty"][d] = (s["correct"] / s["total"] * 100) if s["total"] else 0
    return out


def main():
    root = Path(__file__).resolve().parents[1]
    paths = sys.argv[1:] if len(sys.argv) > 1 else [
        root / "results" / "numina_balanced_results.json",
        root / "results" / "aime_results.json",
    ]
    summaries = []
    for p in paths:
        path = Path(p)
        if not path.is_absolute():
            path = root / path
        if not path.exists():
            print(f"[skip] not found: {path}", file=sys.stderr)
            continue
        try:
            data = load_results(path)
            name = path.stem.replace("_results", "").replace("_", " ").title()
            summaries.append(summarize(data, name))
        except Exception as e:
            print(f"[error] {path}: {e}", file=sys.stderr)

    if not summaries:
        print("No result files processed. Usage: python scripts/update_math_level_from_results.py [result.json ...]")
        return

    print("\n--- 현재 수준 칸에 붙여넣을 문장 (docs/MATH_REASONING_LEVEL_AND_IMPROVEMENTS.md) ---\n")
    for s in summaries:
        acc = s["accuracy"]
        total = s["total"]
        if acc is not None and total is not None:
            print(f"- **{s['name']}**: {acc:.1f}% ({s['total']}문)")
        if s["by_difficulty"]:
            for diff, acc_d in s["by_difficulty"].items():
                print(f"  - {diff}: {acc_d:.1f}%")
    print("\n--- 위 값을 문서 표 '현재 수준' 열에 반영하면 됩니다. ---\n")


if __name__ == "__main__":
    main()
