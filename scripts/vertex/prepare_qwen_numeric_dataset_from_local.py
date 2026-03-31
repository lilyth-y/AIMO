"""
로컬 디렉터리(또는 단일 .jsonl)의 Numina 호환 데이터 → train/dev/test JSONL

- proof 제외(question_type이 있으면)
- 숫자 답만 (기존 스크립트와 동일 규칙)
- **한 줄씩 스트리밍** + reservoir sampling → 1.2GB급도 메모리에 전부 안 올림

입력 레코드(한 줄 JSON) 기본 키:
  problem (또는 --problem-key), answer (--answer-key)
  선택: question_type → "proof" 이면 스킵

실행 예:
  python scripts/vertex/prepare_qwen_numeric_dataset_from_local.py ^
    --input-dir D:/data/numina_dump ^
    --seed 41 --train 3000 --dev 1000 --test 1000

  python scripts/vertex/prepare_qwen_numeric_dataset_from_local.py ^
    --input D:/data/problems.jsonl --recursive 0
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

# --- 아래는 prepare_qwen_numeric_dataset.py 와 동일 규칙 ---
NUMERIC_RE = re.compile(
    r"""^\s*[-+]?(?:
        (?:\d+/\d+) |
        (?:\d+(?:\.\d+)?) |
        (?:\.\d+) |
        (?:\d+(?:\.\d+)?[eE][-+]?\d+)
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


def discover_jsonl_files(root: Path, *, recursive: bool) -> List[Path]:
    if root.is_file():
        if root.suffix.lower() == ".jsonl":
            return [root.resolve()]
        raise ValueError(f"단일 파일은 .jsonl 이어야 합니다: {root}")
    if not root.is_dir():
        raise FileNotFoundError(f"경로 없음: {root}")
    pattern = "**/*.jsonl" if recursive else "*.jsonl"
    files = sorted(root.resolve().glob(pattern))
    if not files and recursive:
        # 하위 없이 루트만 있을 때
        files = sorted(root.glob("*.jsonl"))
    return files


def iter_parsed_lines(paths: List[Path]) -> Iterator[Tuple[Path, int, Dict[str, Any]]]:
    for path in paths:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line_no, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                yield path, line_no, obj


def reservoir_on_filtered_stream(
    stream: Iterator[Tuple[Path, int, Dict[str, Any]]],
    k: int,
    rng: random.Random,
    *,
    problem_key: str,
    answer_key: str,
    question_type_key: str,
    skip_proof: bool,
    max_raw_lines: int,
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Returns: (reservoir of size <= k, raw_lines_scanned, filtered_kept_count)
    """
    reservoir: List[Dict[str, Any]] = []
    scanned = 0
    kept = 0

    for path, line_no, item in stream:
        scanned += 1
        if max_raw_lines and scanned > max_raw_lines:
            break

        if skip_proof and question_type_key:
            qt = str(item.get(question_type_key) or "").strip().lower()
            if qt == "proof":
                continue

        problem = item.get(problem_key) or item.get("question") or ""
        answer = item.get(answer_key)
        if not isinstance(problem, str) or not problem.strip():
            continue
        if not is_numeric_answer(answer):
            continue

        ex = to_sft_example(problem, str(answer))
        ex["source"] = item.get("source", path.stem)
        ex["local_file"] = str(path)
        ex["local_line"] = line_no

        kept += 1
        if len(reservoir) < k:
            reservoir.append(ex)
        else:
            j = rng.randint(1, kept)
            if j <= k:
                reservoir[j - 1] = ex

        if kept % 100_000 == 0:
            print(f"... filtered_kept={kept}, reservoir={len(reservoir)}, raw_scanned={scanned}")

    return reservoir, scanned, kept


def main() -> int:
    ap = argparse.ArgumentParser(
        description="로컬 JSONL(대용량 가능)에서 Qwen SFT용 train/dev/test 생성"
    )
    ap.add_argument("--input-dir", type=str, default="", help="JSONL이 있는 디렉터리")
    ap.add_argument("--input", type=str, default="", help="단일 .jsonl 파일")
    ap.add_argument(
        "--recursive",
        type=int,
        default=1,
        help="1이면 하위 폴더까지 **/*.jsonl 수집 (기본 1)",
    )
    ap.add_argument("--seed", type=int, default=41)
    ap.add_argument("--train", type=int, default=3000)
    ap.add_argument("--dev", type=int, default=1000)
    ap.add_argument("--test", type=int, default=1000)
    ap.add_argument("--out-dir", type=str, default="data/finetune/qwen_numeric")
    ap.add_argument("--problem-key", type=str, default="problem")
    ap.add_argument("--answer-key", type=str, default="answer")
    ap.add_argument(
        "--question-type-key",
        type=str,
        default="question_type",
        help="비어 있으면 proof 스킵 안 함. 키가 있고 값이 proof면 스킵.",
    )
    ap.add_argument("--no-skip-proof", action="store_true", help="question_type=proof 도 포함")
    ap.add_argument(
        "--max-raw-lines",
        type=int,
        default=0,
        help="디버그용: 원본 줄 스캔 상한 (0=무제한)",
    )
    args = ap.parse_args()

    if bool(args.input_dir) == bool(args.input):
        print("ERROR: --input-dir 또는 --input 둘 중 하나만 지정하세요.")
        return 1

    root = Path(args.input_dir or args.input).expanduser()
    recursive = bool(args.recursive)
    files = discover_jsonl_files(root, recursive=recursive)
    if not files:
        raise FileNotFoundError(f".jsonl 파일을 찾지 못했습니다: {root} (recursive={recursive})")

    total_need = args.train + args.dev + args.test
    rng = random.Random(args.seed)
    skip_proof = not args.no_skip_proof

    print(f"JSONL 파일 {len(files)}개 (recursive={recursive})")
    if len(files) <= 10:
        for p in files:
            print(f"  - {p}")
    else:
        for p in files[:5]:
            print(f"  - {p}")
        print(f"  ... 외 {len(files) - 5}개")

    stream = iter_parsed_lines(files)
    qk = args.question_type_key.strip() if args.question_type_key else ""

    reservoir, scanned, kept = reservoir_on_filtered_stream(
        stream,
        k=total_need,
        rng=rng,
        problem_key=args.problem_key,
        answer_key=args.answer_key,
        question_type_key=qk,
        skip_proof=skip_proof,
        max_raw_lines=args.max_raw_lines or 0,
    )

    print(f"Done scan. raw_scanned={scanned}, filtered_kept={kept}, reservoir={len(reservoir)}")

    if len(reservoir) < total_need:
        raise RuntimeError(
            f"샘플 부족: reservoir={len(reservoir)} need={total_need}. "
            f"필터를 완화하거나 데이터를 늘리거나 --max-raw-lines 를 확인하세요."
        )

    rng.shuffle(reservoir)
    train = reservoir[: args.train]
    dev = reservoir[args.train : args.train + args.dev]
    test = reservoir[args.train + args.dev :]

    for i, ex in enumerate(train):
        ex["split"] = "train"
        ex["id"] = f"local_{args.seed}_train_{i}"
    for i, ex in enumerate(dev):
        ex["split"] = "dev"
        ex["id"] = f"local_{args.seed}_dev_{i}"
    for i, ex in enumerate(test):
        ex["split"] = "test"
        ex["id"] = f"local_{args.seed}_test_{i}"

    out_dir = Path(args.out_dir)
    write_jsonl(out_dir / "train.jsonl", train)
    write_jsonl(out_dir / "dev.jsonl", dev)
    write_jsonl(out_dir / "test.jsonl", test)

    print("OK: local dataset prepared")
    print(f"  source: {root}")
    print(f"  out: {out_dir}")
    print(f"  train/dev/test: {len(train)}/{len(dev)}/{len(test)} (seed={args.seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
