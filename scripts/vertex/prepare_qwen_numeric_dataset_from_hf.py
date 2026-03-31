"""
HuggingFace NuminaMath-1.5 -> (proof 제외 + 숫자 답만) -> train/dev/test split 생성 (seed 고정)

입력:  HF dataset "AI-MO/NuminaMath-1.5" (streaming)
출력:  data/finetune/qwen_numeric/{train,dev,test}.jsonl

실행 예:
  python scripts/vertex/prepare_qwen_numeric_dataset_from_hf.py --seed 41 --train 3000 --dev 1000 --test 1000

주의:
  - streaming + reservoir sampling을 사용해 대용량을 메모리 폭발 없이 샘플링합니다.
  - question_type == "proof" 제외 + answer가 숫자(정수/소수/분수/과학표기)인 것만 사용합니다.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


NUMERIC_RE = re.compile(
    r"""^\s*[-+]?(?:
        (?:\d+/\d+) |                     # fraction
        (?:\d+(?:\.\d+)?) |               # int/float
        (?:\.\d+) |                       # leading dot float
        (?:\d+(?:\.\d+)?[eE][-+]?\d+)     # scientific
    )\s*$""",
    re.VERBOSE,
)


def is_numeric_answer(ans: Any) -> bool:
    if ans is None:
        return False
    s = str(ans).strip()
    if not s:
        return False
    if s.lower() in {"proof", "prove", "proved", "true", "false"}:
        return False
    return bool(NUMERIC_RE.match(s))


def to_sft_example(problem: str, answer: str) -> Dict[str, Any]:
    prompt = (
        "You are solving a math problem. "
        "Return ONLY the final answer wrapped in <ANS>...</ANS>.\n"
        "No explanation, no code.\n\n"
        f"Problem:\n{problem.strip()}\n"
    )
    completion = f"<ANS>{answer.strip()}</ANS>"
    return {"prompt": prompt, "completion": completion, "answer": answer.strip()}


def write_jsonl(path: Path, items: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def reservoir_sample(stream, k: int, rng: random.Random, max_read: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Reservoir sampling over streaming dataset.
    Keeps a uniform sample of size k from an arbitrarily long stream.
    """
    reservoir: List[Dict[str, Any]] = []
    seen = 0
    kept = 0

    for item in stream:
        seen += 1
        if max_read and seen > max_read:
            break

        # Filters
        qtype = (item.get("question_type") or "").strip().lower()
        if qtype == "proof":
            continue
        problem = item.get("problem") or item.get("question") or ""
        answer = item.get("answer")
        if not isinstance(problem, str) or not problem.strip():
            continue
        if not is_numeric_answer(answer):
            continue

        ex = to_sft_example(problem, str(answer))
        ex["hf_source"] = item.get("source", "unknown")
        ex["problem_type"] = item.get("problem_type")
        ex["question_type"] = item.get("question_type")
        ex["hf_seen_index"] = seen  # reproducible trace (given same streaming order)

        kept += 1
        if len(reservoir) < k:
            reservoir.append(ex)
        else:
            j = rng.randint(1, kept)
            if j <= k:
                reservoir[j - 1] = ex

        if kept % 5000 == 0:
            print(f"... filtered_kept={kept}, reservoir={len(reservoir)}, scanned={seen}")

    print(f"Done scan. scanned={seen}, filtered_kept={kept}, reservoir={len(reservoir)}")
    return reservoir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=41)
    ap.add_argument("--train", type=int, default=3000)
    ap.add_argument("--dev", type=int, default=1000)
    ap.add_argument("--test", type=int, default=1000)
    ap.add_argument("--out-dir", type=str, default="data/finetune/qwen_numeric")
    ap.add_argument("--dataset", type=str, default="AI-MO/NuminaMath-1.5")
    ap.add_argument("--split", type=str, default="train")
    ap.add_argument("--max-read", type=int, default=0, help="For smoke tests: stop after scanning N raw rows (0=unlimited).")
    args = ap.parse_args()

    total = args.train + args.dev + args.test
    rng = random.Random(args.seed)

    try:
        from datasets import load_dataset
    except Exception as e:
        print("ERROR: datasets 패키지가 필요합니다.")
        print("  python -m pip install datasets")
        print(f"  details: {e}")
        return 1

    print(f"Loading HF dataset (streaming): {args.dataset} split={args.split}")
    stream = load_dataset(args.dataset, split=args.split, streaming=True)

    max_read = args.max_read or None
    sampled = reservoir_sample(stream, k=total, rng=rng, max_read=max_read)
    if len(sampled) < total:
        raise RuntimeError(f"샘플 부족: got={len(sampled)} need={total}. max_read={args.max_read}")

    rng.shuffle(sampled)
    train = sampled[: args.train]
    dev = sampled[args.train : args.train + args.dev]
    test = sampled[args.train + args.dev :]

    # Add deterministic ids within this run
    for i, ex in enumerate(train):
        ex["split"] = "train"
        ex["id"] = f"hf_numina15_{args.seed}_train_{i}"
    for i, ex in enumerate(dev):
        ex["split"] = "dev"
        ex["id"] = f"hf_numina15_{args.seed}_dev_{i}"
    for i, ex in enumerate(test):
        ex["split"] = "test"
        ex["id"] = f"hf_numina15_{args.seed}_test_{i}"

    out_dir = Path(args.out_dir)
    write_jsonl(out_dir / "train.jsonl", train)
    write_jsonl(out_dir / "dev.jsonl", dev)
    write_jsonl(out_dir / "test.jsonl", test)

    print("OK: HF dataset prepared")
    print(f"  out: {out_dir}")
    print(f"  train/dev/test: {len(train)}/{len(dev)}/{len(test)} (seed={args.seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

