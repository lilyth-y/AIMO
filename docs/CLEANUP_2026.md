# 프로젝트 정리 요약 (2026)

## 1. .gitignore 보강

- `.venv_hf_dl/` — 가상환경 폴더 추가
- `submission.parquet`, `*.parquet` — Kaggle 제출물
- `*.zip` — 빌드 아카이브 (예: aimo.zip)
- `adaptive_knowledge.json` — 데모 실행 시 생성 파일

## 2. 루트 디렉터리 정리

- **scripts/ 로 이동**: `organize_pd_project.py`, `rename_project.py`, `update_env_vars.py`  
  → 실행 시 프로젝트 루트 기준이므로 `python scripts/organize_pd_project.py` 처럼 사용
- **삭제**: `archive/legacy/AIMO_core/kaggle_math_pipeline.py.bak`

## 3. 문서 구조 (이미 반영됨)

- `docs/README.md` — 문서 인덱스
- `docs/getting-started/`, `structure/`, `run-eval/`, `finetuning-resources/`, `guides/`, `todo/` — 폴더별 정리
- `docs/archive/` — 과거·완료 문서 보관

## 4. README

- 프로젝트 구조 트리에 `dashboard/`, `notebooks/` 반영
- 문서 링크는 `docs/README.md` 및 `docs/structure/PROJECT_STRUCTURE_AND_ORDER.md` 기준

---

정리 후 **루트에 있는 파일**: `.dockerignore`, `.env`, `.gitignore`, `compose.yml`, `Dockerfile`, `entrypoint.sh`, `README.md`, `requirements.txt` (그 외 `adaptive_knowledge.json`, `aimo.zip`, `submission.parquet` 는 생성/아티팩트로 .gitignore 처리됨).
