"""
Numina 5k -> (proof 제외 + 숫자 답만) -> train/dev/test split 생성

입력:  data/numina_training_5k.jsonl
출력:  data/finetune/qwen_numeric/{train,dev,test}.jsonl

실행:
  python scripts/vertex/prepare_qwen_numeric_dataset.py --seed 41 --train 3000 --dev 1000 --test 1000
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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


def load_numina_5k(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            obj["_row_id"] = i
            rows.append(obj)
    return rows


def to_sft_example(problem: str, answer: str) -> Dict[str, Any]:
    """
    튜닝 목표: 형식 강제 + 숫자 답
    - prompt: 문제만
    - completion: <ANS>정답</ANS>
    """
    prompt = (
        "You are solving a math problem. "
        "Return ONLY the final answer wrapped in <ANS>...</ANS>.\n"
        "No explanation, no code.\n\n"
        f"Problem:\n{problem.strip()}\n"
    )
    completion = f"<ANS>{answer.strip()}</ANS>"
    return {"prompt": prompt, "completion": completion, "answer": answer.strip()}


def split_rows(rows: List[Dict[str, Any]], seed: int, n_train: int, n_dev: int, n_test: int) -> Tuple[List, List, List]:
    import random

    rng = random.Random(seed)
    rows2 = rows.copy()
    rng.shuffle(rows2)

    total = n_train + n_dev + n_test
    picked = rows2[:total]
    train = picked[:n_train]
    dev = picked[n_train : n_train + n_dev]
    test = picked[n_train + n_dev :]
    return train, dev, test


def write_jsonl(path: Path, items: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=str, default="data/numina_training_5k.jsonl")
    ap.add_argument("--out-dir", type=str, default="data/finetune/qwen_numeric")
    ap.add_argument("--seed", type=int, default=41)
    ap.add_argument("--train", type=int, default=3000)
    ap.add_argument("--dev", type=int, default=1000)
    ap.add_argument("--test", type=int, default=1000)
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(f"input not found: {in_path}")

    raw = load_numina_5k(in_path)
    filtered: List[Dict[str, Any]] = []
    for r in raw:
        prob = r.get("problem") or ""
        ans = r.get("answer")
        if not isinstance(prob, str) or not prob.strip():
            continue
        if not is_numeric_answer(ans):
            continue
        filtered.append(r)

    need = args.train + args.dev + args.test
    if len(filtered) < need:
        raise RuntimeError(f"filtered rows not enough: have={len(filtered)} need={need}")

    train, dev, test = split_rows(filtered, args.seed, args.train, args.dev, args.test)

    def convert(split_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for r in split_rows:
            ex = to_sft_example(r["problem"], str(r["answer"]))
            ex["id"] = r.get("_row_id")
            ex["source"] = r.get("source", "unknown")
            out.append(ex)
        return out

    out_dir = Path(args.out_dir)
    train_out = convert(train)
    dev_out = convert(dev)
    test_out = convert(test)

    write_jsonl(out_dir / "train.jsonl", train_out)
    write_jsonl(out_dir / "dev.jsonl", dev_out)
    write_jsonl(out_dir / "test.jsonl", test_out)

    print("OK: dataset prepared")
    print(f"  input: {in_path}")
    print(f"  filtered_available: {len(filtered)}")
    print(f"  out: {out_dir}")
    print(f"  train/dev/test: {len(train_out)}/{len(dev_out)}/{len(test_out)} (seed={args.seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

