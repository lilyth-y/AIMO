# Vertex 문서-코드 동기화 체크리스트

목표: Vertex 관련 스크립트/동작 변경 시 문서가 뒤처지지 않도록 최소 동기화 항목을 고정한다.

## 언제 실행하나

- `scripts/vertex/*.py` 변경
- Vertex 실행 플로우(인증, 리전, 머신 타입, 타임아웃) 변경
- endpoint 평가/채점 로직 변경
- requirements 분기 파일 변경

## 필수 동기화 대상

| 변경 유형 | 반드시 확인/수정할 문서 |
|-----------|--------------------------|
| Vertex 스모크/배포 스크립트 | `docs/VERTEX_SCRIPTS_EVALUATION.md`, `docs/vertex/VERTEX_MINIMUM_RUNBOOK.md` |
| endpoint 평가 스크립트 | `docs/run-eval/CLOUD_SHELL_ENDPOINT_EVAL.md`, `docs/run-eval/RALPH_VERTEX.md` |
| Gemini/Vertex 환경변수 | `docs/run-eval/VERTEX_AI.md`, `docs/run-eval/CLOUD_NUMINA_RUN.md` |
| 머신 타입/쿼터/정리 정책 | `docs/VERTEX_SCRIPTS_EVALUATION.md` |
| requirements 변경 | `docs/run-eval/REQUIREMENTS_SELECTION_GUIDE.md` |

## 변경 후 점검 순서

1. **실행 증거 갱신**: 명령/결과(성공·실패)를 `docs/VERTEX_SCRIPTS_EVALUATION.md` 실행 표에 반영
2. **운영 가이드 반영**: 설치/환경변수 변경을 `docs/run-eval` 문서에 반영
3. **리스크/회피책 갱신**: 실패 케이스와 정리 절차를 명시
4. **링크 검사**: 새 파일/명령이 `docs/README.md`에서 발견 가능한지 확인
5. **검증 커맨드 기록**: 최소 1개 스모크 명령을 문서에 남김

## 최소 검증 커맨드

```bash
python -m pytest -q tests/test_eval_vertex_prediction_text.py tests/test_vertex_genai_cache.py
python scripts/vertex/eval_vertex_endpoint_quality.py --help
```

## 승인 기준

- 문서가 코드의 입력값/출력값/실패 모드를 설명한다
- 실행 커맨드가 복붙 가능한 상태다
- 실패 사례와 복구 절차가 함께 있다
- requirements 선택 근거가 `REQUIREMENTS_SELECTION_GUIDE.md`와 일치한다
