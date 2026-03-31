# Vertex / GCP (AIMO)

저장소: `https://github.com/lilyth-y/AIMO.git`

| 문서 | 내용 |
|------|------|
| [GCP_AUTH.md](GCP_AUTH.md) | ADC·서비스 계정·환경 변수 |
| [AIMO_GCP_PROFILE.md](AIMO_GCP_PROFILE.md) | 프로젝트·버킷·엔드포인트·이중 리전·Cloud Build·Job 예시 |
| [EVAL_REAL_MODEL.md](EVAL_REAL_MODEL.md) | 엔드포인트·HF 로컬 평가 |
| [MERGED_MODEL_ARTIFACT.md](MERGED_MODEL_ARTIFACT.md) | GCS 아티팩트 |
| [RESEARCH_EXPERIMENT_PROTOCOL.md](RESEARCH_EXPERIMENT_PROTOCOL.md) | Arm A/B 연구 프로토콜 |

| run-eval | 내용 |
|----------|------|
| [../run-eval/RALPH_VERTEX.md](../run-eval/RALPH_VERTEX.md) | Ralph·Custom Job·게이트 |
| [../run-eval/CLOUD_NUMINA_RUN.md](../run-eval/CLOUD_NUMINA_RUN.md) | Numina 클라우드 전용 |

## 스크립트 (요약)

| 경로 | 용도 |
|------|------|
| `scripts/vertex/run_vertex_checks.py` | preflight + SDK 연결 |
| `scripts/vertex/run_aimo_gcp_smoke.sh` | Cloud Shell 원스톱 스모크 |
| `scripts/vertex/submit_vertex_eval_job.py` | 엔드포인트 eval Custom Job |
| `docker/vertex-eval/cloudbuild.yaml` | eval 이미지 Cloud Build |

실행 위치는 **Cloud Shell / GCE / CI** 우선 ([AIMO_GCP_PROFILE.md](AIMO_GCP_PROFILE.md) §실행 위치).
