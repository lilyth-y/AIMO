# Vertex 스모크·정리 스크립트 평가

`scripts/vertex/vertex_common.py`, `track_colab_vertex_smoke_seoul.py`, `cleanup_vertex_region.py`에 대한 실전 점검과 확장성 평가입니다.

문서 구성: **실행 점검 표** → **구조·모듈화 평가 표** → **리스크·개선** → **종합 판단** → **공식 문서 교차 검증**.

---

## 1. 실행 점검 (로컬 / gcloud 인증 전제)

| 단계 | 명령 | 결과 |
|------|------|------|
| 공통 모듈 로드 | `python -c "… import vertex_common …"` | ✅ `resolve_project_id`, `resolve_location` 정상 |
| 정리 스크립트 | `python scripts/vertex/cleanup_vertex_region.py --dry-run` | ✅ gcloud JSON 조회·필터·요약 정상 |
| 스모크 트래킹 | `ARTIFACT_URI=…/tiny-gpt2-nofast/ SMOKE_ACCELERATOR_MODE=CPU MACHINE_TYPE=n1-standard-1 … track_colab_vertex_smoke_seoul.py` | ⚠️ Model upload·Endpoint 생성 **성공**, Deploy **실패** (아래 참고) |

### Deploy 실패 사례 (기록)

- **오류**: `400 Machine type "n1-standard-1" is not supported.`
- **공식 문서와의 대응**: Google Cloud [Configure compute resources for inference](https://cloud.google.com/vertex-ai/docs/predictions/configure-compute)의 **Machine types: CPU** 표에 나열된 타입은 `n1-standard-2`부터이며, **`n1-standard-1`은 표에 없음**. 동일 페이지에서 온라인 추론 기본 예시도 `DeployedModel`의 machine 리소스 기본값이 `n1-standard-2`로 안내됨. 따라서 본 400은 “특정 리전만”이 아니라 **Vertex AI가 허용하는 예측용 CPU 머신 목록에 포함되지 않은 타입**을 넣었을 때 나는 API 거절로 해석하는 것이 타당함.
- **권장**: `n1-standard-2` 이상 중에서 선택. CPU 쿼터는 머신 크기와 별도로 `CustomModelServingCPUsPerProjectPerRegion` 등으로 제한될 수 있음 (429 사례는 이전 세션 기록).
- **참고**: 이 실행으로 Model·Endpoint 리소스만 생성된 뒤 Deploy가 실패한 경우, `cleanup_vertex_region.py --yes` 로 정리할 수 있다 (해당 run: model `6291770571994693632`, endpoint `4139214876855762944` 등).

성공 시나리오(이전 세션): LRO 900초 한계는 `vertex_common.vertex_lro_polling_timeout_patch` + `SMOKE_LRO_TIMEOUT_SECONDS`로 완화 가능.

---

## 2. 구조·모듈화 평가

| 항목 | 평가 | 비고 |
|------|------|------|
| **중복 제거** | 양호 | 프로젝트/리전/아티팩트/이미지 URI·gcloud 헬퍼·LRO 보정이 `vertex_common`에 집약됨 |
| **연결성** | 양호 | `track` / `cleanup` 이 동일 상수·`resolve_*` 사용; 변경 시 한 파일 위주 수정 |
| **확장성** | 양호 | 새 스크립트는 `vertex_common`만 import 하면 동일 프로젝트 기본값 공유 |
| **안전성 (cleanup)** | 양호 | 기본 `prefix=aimo-`, `--all` 시 `--yes` 필수, `--dry-run` |
| **테스트 용이성** | 보통 | 단위 테스트는 아직 없음; dry-run·import 스모크로 검증 가능 |
| **의존성** | 주의 | LRO 패치는 `google.api_core` 내부 동작에 의존 → SDK 메이저 업 시 동작 확인 필요 |

---

## 3. 리스크·개선 아이디어

1. **머신 타입**: 배포 전 `gcloud ai machine-types list --region=…` 또는 문서로 허용 타입 확인 후 `MACHINE_TYPE` 설정.
2. **쿼터**: CPU/GPU 쿼터 429 시 콘솔 Quotas에서 상향 또는 리전·프로젝트 조정.
3. **남는 리소스**: Deploy 실패 시에도 Model/Endpoint가 생성될 수 있음 → `cleanup_vertex_region.py --yes` 로 정리.
4. **자동화**: CI에서는 `cleanup --dry-run` + import만 돌리고, 실제 스모크는 수동/스케줄 잡 권장.

---

## 4. 종합

- **실전성**: gcloud·Vertex SDK 혼용을 스크립트 경계로 나누었고, 운영에 필요한 안전장치(dry-run, prefix)가 있음.
- **베테랑 관점**: 과도한 추상화 없이 `vertex_common` 한 모듈로 **설정·헬퍼·스모크 설정**을 묶은 구성은 유지보수에 유리함.

**결론**: 공통 모듈 분리 후에도 실행 경로가 명확하고, 이번 실행에서 Deploy 단계만 **허용되지 않은 machine type(`n1-standard-1`)** 으로 막힌 것으로 보며, 이는 위 [configure-compute](https://cloud.google.com/vertex-ai/docs/predictions/configure-compute) CPU 표와도 일치한다. 이후 평가 시 본 문서의 실행 표를 갱신하면 된다.

---

## 5. 공식 문서 교차 검증 (웹·문서 근거)

| 확인 항목 | 출처 | 결과 |
|-----------|------|------|
| 커스텀 모델 온라인 추론 시 machine type 지정 | [Configure compute resources for inference](https://cloud.google.com/vertex-ai/docs/predictions/configure-compute) | `dedicatedResources.machineSpec`에 지정 필요 |
| 예측용 CPU(N1) 목록 | 동 문서 **Machine types: CPU** — N1 시리즈 표 | `n1-standard-2`부터 나열 — **`n1-standard-1` 없음** |
| `DeployedModel` 기본 machine type | [MachineSpec (REST)](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/MachineSpec) | optional 시 기본값 **`n1-standard-2`** (문서 설명) |
| 시스템 예약 CPU | [configure-compute](https://cloud.google.com/vertex-ai/docs/predictions/configure-compute) 본문 | 레플리카당 약 1 vCPU를 시스템에 예약 |

**보조 확인**: 동일 주제를 MCP 검색(Exa `web_search_exa`)으로 재질의해도 위 CPU 표가 `n1-standard-2`부터이고, 배포 예시에서 `MACHINE_TYPE` 기본이 `n1-standard-2`로 인용됨 — 로컬에서 관측한 `400 … n1-standard-1 is not supported`와 모순 없음.

리전별 CLI 확인: `gcloud ai machine-types list --region=REGION`

---

## 6. 발견 문제 → 해결방안 → 코드 반영

| 문제 | 원인(추론) | 해결방안 | 구현 |
|------|------------|----------|------|
| Deploy `400 … n1-standard-1 is not supported` | [configure-compute](https://cloud.google.com/vertex-ai/docs/predictions/configure-compute) CPU 표에 해당 타입 없음 | 허용 최소 N1(`n1-standard-2`)으로 교정하거나 사용자가 올바른 타입 지정 | `vertex_common._normalize_smoke_machine_type`: `n1-standard-1` → `n1-standard-2`, stderr 경고. `SMOKE_STRICT_MACHINE_TYPE=1` 시 교정 생략 |
| LRO 900초 타임아웃 | `google.api_core` LRO 기본 폴링 900초 | LRO `result()`에 더 긴 timeout 또는 무제한 | 기존: `vertex_lro_polling_timeout_patch` + `SMOKE_LRO_TIMEOUT_SECONDS` |
| Deploy 실패 후 Model/Endpoint만 남음 | 업로드·엔드포인트 생성은 Deploy보다 앞 단계 | 실패 시 정리 명령 안내 | `track_colab_vertex_smoke_seoul.py` 예외 처리: `cleanup_hint` 이벤트 + stderr HINT |
| `429` CustomModelServing CPU/GPU 쿼터 | 프로젝트·리전별 할당 한도 | 콘솔 Quotas 상향, 머신/가속기/리전 조정 | 동일 예외 블록: `quota_hint` 이벤트 + stderr HINT |
| 설정 중복·불일치 | 스크립트별 하드코딩 | 공통 상수·`resolve_*` | 기존: `vertex_common.py` |

**검증**: `MACHINE_TYPE=n1-standard-1` 로 `apply_smoke_env_overrides` 호출 시 `machine_type` 이 `n1-standard-2` 로 바뀌고 경고 목록이 비어 있지 않아야 함(로컬 Python 스모크).

---

## 7. 답 품질 평가 (실제 모델)

**로컬/HF vs Vertex** 두 경로와 명령은 [EVAL_REAL_MODEL.md](./vertex/EVAL_REAL_MODEL.md) 에 정리함.

### 7a Vertex 엔드포인트만

인프라 스모크와 별도로, 배포된 엔드포인트에 대해 **Numina 샘플 + 정답 비교**를 돌리려면:

```bash
python scripts/vertex/eval_vertex_endpoint_quality.py --endpoint-id <ENDPOINT_ID> --n-problems 20
```

- `PROJECT_ID`, `LOCATION` 은 `vertex_common` 과 동일하게 env 로 지정 가능.
- 채점: `pipeline.answer_extraction.AnswerExtractor` + `evaluation.evaluation_utils.check_answer_correctness`.
- 결과: `results/vertex_eval_<timestamp>.jsonl` + stdout 에 accuracy 요약.

실제 모델 아티팩트가 수학 추론에 맞는지에 따라 점수가 달라짐 (tiny-gpt2 스모크는 품질 지표로 부적합).

**실제 머지 모델 GCS 경로**: [vertex/MERGED_MODEL_ARTIFACT.md](./vertex/MERGED_MODEL_ARTIFACT.md) — `VERTEX_MERGED_ARTIFACT_URI` / `ARTIFACT_URI`.
