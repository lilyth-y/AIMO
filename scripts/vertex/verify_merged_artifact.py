#!/usr/bin/env python3
"""
1단계: 머지(HF) 아티팩트가 배포·평가에 쓸 수 있는지 검증.

- 로컬 디렉터리: config.json, (권장) tokenizer.json 또는 tokenizer_config.json
- GCS 프리픽스(gs://.../merged/): gcloud storage ls 로 동일 파일 존재 확인

사용 예:
  python scripts/vertex/verify_merged_artifact.py --local D:/models/my-merged
  python scripts/vertex/verify_merged_artifact.py --gcs-uri gs://BUCKET/aimo/models/qwen_numeric/merged/
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_VERTEX_DIR = Path(__file__).resolve().parent

if str(_VERTEX_DIR) not in sys.path:
    sys.path.insert(0, str(_VERTEX_DIR))

from vertex_common import find_gcloud  # noqa: E402


def _run_gcloud_ls(uri: str) -> tuple[int, str]:
    gcloud = find_gcloud()
    r = subprocess.run(
        [gcloud, "storage", "ls", uri],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, out


def verify_local(path: Path) -> int:
    p = path.expanduser().resolve()
    if not p.is_dir():
        print(f"[FAIL] 디렉터리가 아님: {p}")
        return 1
    cfg = p / "config.json"
    if not cfg.is_file():
        print(f"[FAIL] config.json 없음: {p}")
        return 1
    tok_json = p / "tokenizer.json"
    tok_cfg = p / "tokenizer_config.json"
    if not tok_json.is_file() and not tok_cfg.is_file():
        print(
            "[WARN] tokenizer.json / tokenizer_config.json 둘 다 없음. "
            "일부 환경에서는 로드 실패할 수 있음."
        )
    else:
        print("[OK] 토크나이저 관련 파일 확인.")

    # 권장 HF 파일
    weights = list(p.glob("model*.safetensors")) + list(p.glob("pytorch_model*.bin"))
    if not weights and not (p / "adapter_config.json").is_file():
        print("[WARN] model*.safetensors / pytorch_model*.bin 없음 (가중치 확인).")

    print(f"[OK] 로컬 머지 아티팩트: {p}")
    print("     다음: python scripts/eval_hf_local_quality.py --model <위 경로> --n-problems 5")
    return 0


def verify_gcs(uri: str) -> int:
    u = uri.strip()
    if not u.startswith("gs://"):
        print("[FAIL] gs:// 로 시작하는 URI 필요")
        return 1
    if not u.endswith("/"):
        u = u + "/"

    code, out = _run_gcloud_ls(u)
    if code != 0:
        print(f"[FAIL] gcloud storage ls 실패 (권한·경로 확인):\n{out}")
        return 1

    lines = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("gs://")]
    names = [ln.rsplit("/", 1)[-1] for ln in lines if "/" in ln]
    if "config.json" not in names:
        print(f"[FAIL] config.json 이 목록에 없음. 출력:\n{out[:2000]}")
        return 1

    if "tokenizer.json" not in names and "tokenizer_config.json" not in names:
        print("[WARN] tokenizer 관련 파일이 목록에 없을 수 있음.")

    print(f"[OK] GCS 머지 프리픽스: {u}")
    print("     다음: $env:VERTEX_MERGED_ARTIFACT_URI = '<위 URI>' 후 배포 스크립트 또는")
    print("           serve.py 가 읽는 AIP_STORAGE_URI 와 동일 규약으로 업로드되었는지 확인.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="머지 HF 아티팩트(1단계) 검증")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--local", type=str, help="로컬 머지 디렉터리 (config.json 포함)")
    g.add_argument("--gcs-uri", type=str, help="GCS 프리픽스 gs://.../merged/")
    args = ap.parse_args()

    if args.local:
        return verify_local(Path(args.local))
    return verify_gcs(args.gcs_uri)


if __name__ == "__main__":
    sys.exit(main())
