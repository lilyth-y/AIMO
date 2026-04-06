# Requirements 선택 가이드

환경별로 `requirements*.txt`가 분리되어 있어 설치 실수를 줄이기 위한 빠른 선택표입니다.

## 빠른 선택 매트릭스

| 목적 | 권장 파일 | 포함 범위 | 비고 |
|------|-----------|-----------|------|
| 로컬 기본 실행/테스트(비-GPU) | `requirements.txt` | 코어 + 테스트 + CPU torch | 가장 범용 기본값 |
| 로컬 GPU 추론 | `requirements-gpu.txt` | GPU torch + bitsandbytes 포함 | CUDA/드라이버 선행 필요 |
| Vertex Gemini 최소 스모크 (Cloud Shell 권장) | `requirements-cloudshell-smoke.txt` | Vertex 호출 최소 의존성 | `/tmp` target 설치 권장 |
| Vertex Endpoint 품질 평가 전용 | `requirements-cloudshell-endpoint-eval.txt` | endpoint eval 전용 최소 세트 | `PYTHONPATH`에 `src` 추가 |
| Vertex SDK/도구 분리 설치 | `requirements-vertex-sdk.txt`, `requirements-vertex-tools.txt`, `requirements-vertex-bq.txt` | SDK/도구/BigQuery 분리 | 운영 스크립트별 선택 설치 |
| Kaggle 노트북 실행 | `requirements-kaggle.txt` | Kaggle 런타임 기준 패키지 | 노트북 체크리스트와 함께 사용 |
| Cloud Run API 배포 | `requirements-cloudrun.txt` | 서비스 API 런타임 최소 의존성 | 컨테이너 빌드 경로 참조 |

## 권장 순서

1. 실행 목표를 먼저 고정한다 (로컬, Kaggle, Vertex, Cloud Run).
2. 표에서 해당 파일 1개(또는 명시된 조합)만 선택한다.
3. 설치 후 스모크를 먼저 통과시킨다.
4. 필요할 때만 상위 스택(전체 `requirements.txt`)을 추가한다.

## 자주 하는 실수

- Cloud Shell에서 `requirements.txt` 전체를 `--user`로 설치해 홈 디스크를 채움
- Kaggle에서 CPU torch 라인을 중복 설치함
- Vertex endpoint 평가만 필요한데 전체 스택을 먼저 설치함
- 리포 루트가 아닌 위치에서 `-r requirements-*.txt`를 실행함

## 관련 문서

- [CLOUD_NUMINA_RUN.md](./CLOUD_NUMINA_RUN.md)
- [CLOUD_SHELL_ENDPOINT_EVAL.md](./CLOUD_SHELL_ENDPOINT_EVAL.md)
- [VERTEX_AI.md](./VERTEX_AI.md)
- [KAGGLE_ENV_CHECK.md](./KAGGLE_ENV_CHECK.md)
