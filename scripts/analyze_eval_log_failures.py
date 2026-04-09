"""Summarize eval_log.jsonl: syntax_error, code-gen stub, strategies."""
import json
import collections
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    log = root / "logs" / "eval_log.jsonl"
    if not log.exists():
        print("No logs/eval_log.jsonl")
        return 1
    syn = 0
    cgf = 0
    strat = collections.Counter()
    mismatch_exec = 0
    verified_ok = 0
    for line in log.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("syntax_error"):
            syn += 1
        er = str(o.get("execution_result") or "")
        if "Code generation failed" in er:
            cgf += 1
        strat[str(o.get("strategy") or "?")] += 1
        if o.get("mismatch_type") == "execution_error":
            mismatch_exec += 1
        if o.get("verified"):
            verified_ok += 1

    n = sum(strat.values())
    print(f"Total log lines: {n}")
    print(f"syntax_error=True (from orchestrator log fields): {syn}")
    print(f"execution_result contains 'Code generation failed': {cgf}")
    print(f"verified=True: {verified_ok}")
    print(f"mismatch_type=execution_error: {mismatch_exec}")
    print("Top strategies:", strat.most_common(15))
    print(
        "\nNote: 'Code generation failed' is emitted in solver._extract_code when "
        "compile() fails on extracted LLM output (see src/pipeline/solver.py)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
