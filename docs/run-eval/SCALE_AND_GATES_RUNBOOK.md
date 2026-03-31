# 규모 확대·게이트 역할 (Phase 4)

**추론(모델 실행)** 은 기본적으로 **GCP/Vertex·클라우드 Job** 에서만 돌린다 ([ARM_AB_PROTOCOL.md](../experiments/ARM_AB_PROTOCOL.md)). 로컬 HF 로드는 선택.

`n ≥ 50` 보고·배포 전에 아래를 구분해 사용한다. **서로 다른 목적**이므로 숫자·조건을 혼동하지 말 것.

## STEP2 품질 게이트

- **문서**: [STEP2_QUALITY_GATES.md](../vertex/STEP2_QUALITY_GATES.md)
- **역할**: 엔드포인트 배포 전 **형식률·null·API 오류·최소 accuracy** 등 **동시 조건** (예: `n≥50`).
- **주의**: STEP2의 최소 accuracy는 **Ralph 80%와 목적이 다름** — “STEP2 통과 = Ralph 목표 달성”이 아님.

## Ralph 정확도 게이트 (로컬/CI)

- **스크립트**: [scripts/ralph_accuracy_gate.py](../../scripts/ralph_accuracy_gate.py)
- **설정**: `AIMO_RALPH_TARGET_ACCURACY_PCT`, 선택 `AIMO_RALPH_GATE_MODE=easy` ([ACCURACY_ANALYSIS_AND_PLAN.md](ACCURACY_ANALYSIS_AND_PLAN.md) §3.0).

## Vertex Job 요약 + Ralph

- **문서**: [RALPH_VERTEX.md](RALPH_VERTEX.md), [GCP_AUTH.md](../vertex/GCP_AUTH.md)
- **흐름**: [scripts/vertex/submit_vertex_eval_job.py](../../scripts/vertex/submit_vertex_eval_job.py) — `--enforce-ralph-accuracy`, `--write-summary-json`, `--gcs-summary-uri` 등.
- **검사**: [scripts/vertex/run_vertex_checks.py](../../scripts/vertex/run_vertex_checks.py), [scripts/vertex/ralph_vertex_accuracy_gate.py](../../scripts/vertex/ralph_vertex_accuracy_gate.py)

## 대규모 실행 (클라우드 권장)

- [CLOUD_NUMINA_RUN.md](CLOUD_NUMINA_RUN.md) — Cloud Shell/GCE/Vertex Job 등에서 디스크·의존성 제약 준수. **대형 `n` 은 로컬 HF 대신 여기에 맞출 것.**

## 실험 노트

각 실행마다 [EXPERIMENT_NOTE_TEMPLATE.md](EXPERIMENT_NOTE_TEMPLATE.md)에 **어느 게이트를 통과시키려 했는지** 한 줄로 명시한다.
