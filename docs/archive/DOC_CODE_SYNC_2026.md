# 문서–코드베이스 대조 반영 요약 (2026)

Cursor 플랜(문서 vs 현재 레포 갭 정리)에 따라 **문서만** 업데이트한 작업의 기록이다. 플랜 원본은 IDE `.cursor/plans/` 등에 남을 수 있으며, **레포 기준 진실은 아래 링크**를 따른다.

## 단일 진실 원천

- **파이프라인 환경 변수·기본값**: [`src/pipeline/settings.py`](../../src/pipeline/settings.py)
- **문서 인덱스**: [`docs/README.md`](../README.md)

## 반영한 내용 (요지)

1. **인덱스** (`docs/README.md`): `vertex/`, `eval/`, `pd/`, 루트 `MATH_SOLVING_ARCHITECTURE_EVALUATION.md`, `VERTEX_SCRIPTS_EVALUATION.md` 안내. **Vertex 두 축** 구분 — 관리형 Gemini API는 [`run-eval/VERTEX_AI.md`](../run-eval/VERTEX_AI.md), GCS·커스텀 엔드포인트는 [`vertex/`](../vertex/) 및 [`vertex/WHY_THIS_VERTEX_STACK.md`](../vertex/WHY_THIS_VERTEX_STACK.md).
2. **구조 문서** (`docs/structure/PROJECT_STRUCTURE_AND_ORDER.md`): `docker/`, `scripts/vertex/`, `requirements-*.txt`, 파이프라인의 `remote_inference`·`vertex_*` 모듈, §3.5 클라우드 경로. §3.2 환경 변수명을 `OMI_*` / `AIMO_*`로 통일.
3. **루트 README**: `settings.py`와 맞춘 환경 변수 표·빠른 시작 예시.
4. **실행·모델** (`docs/run-eval/README_MODELS.md`, `README_AIMO_EVAL.md`, `RUN_EVALUATION_ENVIRONMENT.md` 일부): HF 전체 `repo_id`, `examples/` 경로, Docker는 `AIMO_FAST_TEST` 등. 이후 **루트 래퍼** 추가: `test_solver.py`, `run_numina_evaluation.py` → `examples/`, `run_aimo_evaluation.py` → 참조 JSONL (`entrypoint.sh`와 정합).
5. **기타**: `docs/finetuning-resources/README_DOCKER.md`의 FAST_TEST 변수명, `QUICK_REFERENCE.md`의 절대 경로 제거, `.cursor/rules/self-refine-pattern.mdc`의 Refine 가이드 경로를 `docs/guides/REFINE_LOOP_USAGE.md`로 수정.
6. **구명칭**: 일부 아카이브·과거 문서의 **MathCodeOrchestrator** 표기는 역사적 참고용; 현재 코드·루트 README는 **OMI / AIMO** 변수 체계를 사용한다는 안내를 인덱스·구조 문서에 추가.

## 관련 정리 문서

- [`docs/CLEANUP_2026.md`](../CLEANUP_2026.md) — 루트·gitignore·문서 폴더 정리 요약 (별도 축)

## 이후 작업 시

- 문서만 고칠 때도 **`settings.py`와 불일치하면 안 됨**.
- Vertex 관련 작업 전에 위 **두 갈래 Vertex** 표를 확인할 것.
