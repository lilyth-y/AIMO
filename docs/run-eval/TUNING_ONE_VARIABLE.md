# 경로별 튜닝 (한 번에 변수 하나)

[FORMAT_AND_ACCURACY_PLAN.md](../vertex/FORMAT_AND_ACCURACY_PLAN.md)와 동일 원칙.  
실험마다 [EXPERIMENT_NOTE_TEMPLATE.md](EXPERIMENT_NOTE_TEMPLATE.md) 5줄을 채우고, **변경한 환경변수·CLI 인자는 한 개**만 기록한다.

**환경**: 튜닝 실험의 추론은 **Vertex/클라우드**에서 수행하는 것을 전제로 한다 ([ARM_AB_PROTOCOL.md](../experiments/ARM_AB_PROTOCOL.md)).

## Path B — Vertex 엔드포인트 (`eval_vertex_endpoint_quality.py`)

한 실험당 아래 **하나만** 바꾼다 (나머지는 이전 실행과 동일).

| 변수 | 의미 |
|------|------|
| `max_format_retries` | 형식 재시도 횟수 |
| `retry_temperature` | 재시도 시 온도 |
| `verify_max_new_tokens` | 검증 단계 토큰 상한 |
| `--last-resort-extraction` | 마지막 수단 추출 on/off |
| `--no-format-gate` | 형식 게이트 비교 전용 실험 시 |

**분석**: 결과 JSONL에 대해 [scripts/vertex/diagnose_vertex_eval_jsonl.py](../../scripts/vertex/diagnose_vertex_eval_jsonl.py) 실행.

## Path A — 오케스트레이터 + Gemini (Numina 등)

한 실험당 아래 **하나만** 바꾼다.

| 변수 | 파일·참고 |
|------|-----------|
| `AIMO_OPTIMIZE_ACCURACY` | `src/pipeline/settings.py` |
| `OMI_USE_VOTING` | 다후보 투표 |
| `OMI_NUM_CANDIDATES` | 후보 수 |
| `OMI_REFINE_*` | Refine 루프 |
| `AIMO_SELF_CORRECTION_MAX_ATTEMPTS` | 자기 수정 횟수 |

**규모**: 소량 `n`(예: 5~10)으로 순차 비교한 뒤, §3.0 정책에 맞는 스트라타·게이트로 확대한다.

## 금지

- 지표·데이터·시드·문제 수를 동시에 바꿔 “개선된 것처럼” 보이게 하기 (연구 규정 위반).
