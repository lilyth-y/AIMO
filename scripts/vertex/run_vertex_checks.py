#!/usr/bin/env python3
"""
GCP 자격 증명 + Vertex SDK 연결을 순서대로 확인합니다.

  python scripts/vertex/run_vertex_checks.py
  python scripts/vertex/run_vertex_checks.py --project YOUR_PROJECT --location asia-northeast3

`--project` / `--location` 을 주면 자식 프로세스에 GOOGLE_CLOUD_* 를 넣어 preflight 의
vertex_gemini_env 가 READY 로 잡히도록 합니다.

1) preflight_vertex.py — 네트워크 없음, import·ADC
2) vertex_env_check.py — Endpoint.list() 로 실제 Vertex API
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser(description="Run preflight + vertex_env_check")
    ap.add_argument("--project", default=os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID") or "")
    ap.add_argument("--location", default=os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("LOCATION") or "")
    args, rest = ap.parse_known_args()

    env = os.environ.copy()
    if args.project:
        env["GOOGLE_CLOUD_PROJECT"] = args.project
        env.setdefault("PROJECT_ID", args.project)
    if args.location:
        env["GOOGLE_CLOUD_LOCATION"] = args.location
        env.setdefault("LOCATION", args.location)

    r1 = subprocess.run(
        [sys.executable, str(ROOT / "scripts/vertex/preflight_vertex.py")],
        cwd=str(ROOT),
        env=env,
    )
    if r1.returncode != 0:
        return r1.returncode

    vc = [sys.executable, str(ROOT / "scripts/vertex/vertex_env_check.py")]
    if args.project:
        vc.extend(["--project", args.project])
    if args.location:
        vc.extend(["--location", args.location])
    vc.extend(rest)

    r2 = subprocess.run(vc, cwd=str(ROOT), env=env)
    if r2.returncode != 0:
        return r2.returncode

    print("\nOK: all Vertex checks passed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
