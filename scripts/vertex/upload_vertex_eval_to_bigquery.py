#!/usr/bin/env python3
"""
기존 vertex_eval JSONL을 BigQuery에 적재 (eval 직후가 아니어도 실행 가능).

예:
  set PROJECT_ID=your-project
  python scripts/vertex/upload_vertex_eval_to_bigquery.py results/vertex_eval_20260321_193618.jsonl \\
    --table your-project.aimo_vertex.eval_runs \\
    --endpoint-id 7467375001482559488

환경: VERTEX_EVAL_BQ_TABLE, GOOGLE_APPLICATION_CREDENTIALS(선택)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_VDIR = Path(__file__).resolve().parent
for p in (_ROOT / "src", _VDIR):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from vertex_common import resolve_location, resolve_project_id  # noqa: E402
from vertex_bigquery import new_run_id, upload_jsonl_to_bigquery  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="vertex_eval JSONL → BigQuery")
    ap.add_argument("jsonl", type=Path, help="eval_vertex_endpoint_quality.py 가 쓴 .jsonl")
    ap.add_argument(
        "--table",
        default=os.getenv("VERTEX_EVAL_BQ_TABLE", "").strip(),
        help="project.dataset.table (필수)",
    )
    ap.add_argument("--endpoint-id", default="", help="메타데이터용 엔드포인트 ID")
    ap.add_argument("--project", default=resolve_project_id(prefer_cleanup_alias=False))
    ap.add_argument("--location", default=resolve_location())
    ap.add_argument("--run-id", default="", help="미지정 시 타임스탬프+uuid")
    ap.add_argument(
        "--no-create",
        action="store_true",
        help="테이블/데이터셋이 없으면 실패 (자동 생성 안 함)",
    )
    ap.add_argument(
        "--dataset-location",
        default=os.getenv("VERTEX_EVAL_BQ_DATASET_LOCATION", "asia-northeast3"),
    )
    args = ap.parse_args()

    if not args.table:
        print("ERROR: --table 또는 VERTEX_EVAL_BQ_TABLE 필요", file=sys.stderr)
        return 1
    if not args.jsonl.is_file():
        print("ERROR: 파일 없음:", args.jsonl, file=sys.stderr)
        return 1

    rid = args.run_id.strip() or new_run_id()
    try:
        n, used_id = upload_jsonl_to_bigquery(
            args.jsonl,
            table=args.table,
            run_id=rid,
            endpoint_id=args.endpoint_id,
            vertex_project=args.project,
            vertex_location=args.location,
            create_table=not args.no_create,
            dataset_location=args.dataset_location,
        )
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        return 1

    print(json.dumps({"uploaded_rows": n, "run_id": used_id, "table": args.table}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
