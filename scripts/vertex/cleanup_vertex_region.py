"""
지정 Vertex AI 리전의 Online Prediction 엔드포인트·모델을 정리한다.

순서:
  1) 각 엔드포인트에 배포된 모델을 모두 undeploy
  2) 엔드포인트 삭제
  3) 모델 삭제

기본은 displayName이 --prefix 로 시작하는 리소스만 대상(실수로 타 팀 리전 전체 삭제 방지).
리전 전체 삭제가 필요하면 --all 과 --yes 를 함께 사용.

사용 예:
  # AIMO 스모크 리소스만 (기본 prefix=aimo-)
  python scripts/vertex/cleanup_vertex_region.py --yes

  # 미리 보기
  python scripts/vertex/cleanup_vertex_region.py --dry-run

  # prefix 지정
  python scripts/vertex/cleanup_vertex_region.py --prefix aimo-smoke- --yes

  # 해당 리전의 엔드포인트·모델 전부 (위험)
  python scripts/vertex/cleanup_vertex_region.py --all --yes

환경변수:
  기본 공통: PROJECT_ID / GOOGLE_CLOUD_PROJECT, LOCATION / GOOGLE_CLOUD_LOCATION
  cleanup 전용 우선순위: VERTEX_CLEANUP_PROJECT_ID, VERTEX_CLEANUP_LOCATION

공통 기본값: vertex_common.py
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_VDIR = Path(__file__).resolve().parent
if str(_VDIR) not in sys.path:
    sys.path.insert(0, str(_VDIR))

from vertex_common import (  # noqa: E402
    DEFAULT_CLEANUP_DISPLAY_NAME_PREFIX,
    DEFAULT_VERTEX_LOCATION,
    DEFAULT_VERTEX_PROJECT_ID,
    filter_display_name_prefix,
    find_gcloud,
    gcloud_json,
    resolve_location,
    resolve_project_id,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Vertex AI 엔드포인트·모델 리전 정리")
    ap.add_argument(
        "--project",
        default=resolve_project_id(prefer_cleanup_alias=True),
        help=f"GCP 프로젝트 ID (기본: env 또는 {DEFAULT_VERTEX_PROJECT_ID})",
    )
    ap.add_argument(
        "--location",
        default=resolve_location(),
        help=f"Vertex 리전 (기본: env 또는 {DEFAULT_VERTEX_LOCATION})",
    )
    ap.add_argument(
        "--prefix",
        default=os.getenv("VERTEX_CLEANUP_PREFIX", DEFAULT_CLEANUP_DISPLAY_NAME_PREFIX),
        help="displayName 이 이 문자열로 시작하는 엔드포인트·모델만 대상. 빈 문자열이면 --all 없이는 사용 불가.",
    )
    ap.add_argument(
        "--all",
        action="store_true",
        help="prefix 무시하고 해당 리전의 엔드포인트·모델 전부 삭제 (--yes 필수)",
    )
    ap.add_argument("--dry-run", action="store_true", help="삭제하지 않고 대상만 출력")
    ap.add_argument("-y", "--yes", action="store_true", help="확인 없이 실행")
    args = ap.parse_args()

    if not args.all and args.prefix == "":
        print("ERROR: --prefix 를 빈 문자열로 두려면 리전 전체 삭제 의미이므로 --all --yes 를 사용하세요.", file=sys.stderr)
        return 2

    if args.all and not args.yes:
        print("ERROR: --all 은 실수 방지를 위해 --yes 가 필요합니다.", file=sys.stderr)
        return 2

    prefix: Optional[str] = None if args.all else args.prefix

    gcloud = find_gcloud()
    project, region = args.project, args.location

    endpoints: List[Dict[str, Any]] = gcloud_json(
        gcloud,
        ["ai", "endpoints", "list", "--region", region, "--project", project, "--format", "json"],
    )
    models: List[Dict[str, Any]] = gcloud_json(
        gcloud,
        ["ai", "models", "list", "--region", region, "--project", project, "--format", "json"],
    )

    endpoints = filter_display_name_prefix(endpoints, prefix)
    models = filter_display_name_prefix(models, prefix)

    print(f"project={project} location={region}", file=sys.stderr)
    print(f"filter={'(전체)' if prefix is None else repr(prefix)}", file=sys.stderr)
    print(f"endpoints={len(endpoints)} models={len(models)}", file=sys.stderr)

    if not endpoints and not models:
        print("삭제할 리소스가 없습니다.", file=sys.stderr)
        return 0

    if not args.yes and not args.dry_run:
        print("다음 작업을 수행합니다. 계속하려면 --yes 또는 --dry-run 을 사용하세요.", file=sys.stderr)
        for ep in endpoints:
            print("  endpoint:", ep.get("displayName"), ep["name"].split("/")[-1], file=sys.stderr)
        for m in models:
            print("  model:", m.get("displayName"), m["name"].split("/")[-1], file=sys.stderr)
        return 1

    def run_gc(cmd: Sequence[str]) -> None:
        if args.dry_run:
            print("[dry-run]", " ".join(cmd), file=sys.stderr)
            return
        r = subprocess.run([gcloud, *cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            sys.stderr.write(r.stderr or r.stdout or "")
            raise subprocess.CalledProcessError(r.returncode, [gcloud, *cmd])

    try:
        for ep in endpoints:
            eid = ep["name"].split("/")[-1]
            dn = ep.get("displayName", "")
            print(f"endpoint {eid} ({dn})", flush=True)
            for dm in ep.get("deployedModels") or []:
                did = str(dm["id"])
                print(f"  undeploy {did}", flush=True)
                run_gc(
                    [
                        "ai",
                        "endpoints",
                        "undeploy-model",
                        eid,
                        "--deployed-model-id",
                        did,
                        "--region",
                        region,
                        "--project",
                        project,
                        "--quiet",
                    ]
                )
            print(f"  delete endpoint", flush=True)
            run_gc(["ai", "endpoints", "delete", eid, "--region", region, "--project", project, "--quiet"])

        for m in models:
            mid = m["name"].split("/")[-1]
            dn = m.get("displayName", "")
            print(f"delete model {mid} ({dn})", flush=True)
            run_gc(["ai", "models", "delete", mid, "--region", region, "--project", project, "--quiet"])
    except subprocess.CalledProcessError:
        return 1

    if args.dry_run:
        print("dry-run 완료 (실제 삭제 없음).", file=sys.stderr)
    else:
        print("정리 완료.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
