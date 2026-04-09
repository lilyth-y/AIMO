# 정확도 분석·선행 사례 적용 검토·개선 계획

저장소에 이미 정리된 설계·실험 문서와 최근 실행 관측을 바탕으로 작성한다.  
외부 논문 인용은 본 문서 범위에 포함하지 않으며, **레포 내부 선행(문서화된 패턴)** 만 다룬다.

---

## 1. 전체 구조에서의 “선행 사례” (레포 기준)와 적용 가능성


| 선행(문서·코드)                                                                                                                | 요지                                                                    | 현재 구조에서의 적용                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Vertex 엔드포인트 + `<ANS>` 형식 게이트** (`eval_vertex_endpoint_quality.py`, `ans_format_guard`, `FORMAT_AND_ACCURACY_PLAN.md`) | 배포 모델에 대해 **형식 준수율**과 **채점 정확도**를 분리 추적                               | **적용 가능·권장**: 커스텀 서빙(Qwen 등) 평가 시 1차 기준. 오케스트레이터+Gemini 경로와는 채점·출력 형식이 다를 수 있어 **동일 스크립트로 직접 비교할 때는 프롬프트·출력 프로토콜을 맞출 것**. |
| **STEP2 품질 게이트** (`STEP2_QUALITY_GATES.md`)                                                                              | `n≥50`, `strict_format_rate`, 최소 accuracy, null/API 오류 상한 등 **동시 조건** | **적용 가능**: 엔드포인트 배포 전 Go/No-Go. **주의**: STEP2의 최소 accuracy(0.2)는 **Ralph 80% 목표와 목적이 다름** — 역할을 혼동하지 말 것.                 |
| **Ralph 정확도 게이트** (`ralph_accuracy.py`, `RALPH_VERTEX.md`)                                                               | 단일 스칼라 목표(기본 80%) + 게이트 스크립트                                          | **적용 가능**: “한 숫자로 끝냈는가”에만 쓰고, **난이도 혼합 벤치**에서는 §3과 같이 목표를 재정의하는 것이 안전.                                                    |
| **연구 Arm 설계** (`RESEARCH_EXPERIMENT_PROTOCOL.md`)                                                                        | L1(엔드포인트) 고정, L2(오케스트레이터 on/off) 분리, 동일 $\mathcal{D}$·시드              | **적용 가능·핵심**: “정확도가 낮다”를 **모델 한계**인지 **파이프라인 오버헤드**인지 구분하려면 **Baseline-LLM vs Full-Pipeline** 대조가 필요.                     |
| **품질 실험 트랙** (`QUALITY_EXPERIMENT.md`)                                                                                   | 소량 데이터·별 출력 디렉터리·동일 채점기                                               | **적용 가능**: 대규모 학습과 섞이지 않게 실험용 아티팩트 분리.                                                                                    |
| **난이도별 목표 구간** (`TARGET_ACCURACY.md`)                                                                                    | Easy 80–90%, Medium 60–70%, Hard 30–40%                               | **적용 가능**: **혼합 난이도 60문항**에 “전체 80%”를 그대로 요구하면 목표가 과다할 수 있음. 보고는 **스트라타별**로 하는 것이 문서 의도와 일치.                              |
| **Numina 0% 진단** (`ZERO_ACCURACY_DEBUG.md`)                                                                              | 타임아웃, 참조 형식, SymPy, 실행 실패, 추출 실패                                      | **적용 가능**: 여전히 유효한 체크리스트.                                                                                                 |
| **실행 오류 문자열 처리** (`is_execution_error_output`, 투표/검증)                                                                    | `Error:` vs `ERROR:` 불일치 제거                                           | **이미 반영**: 투표·검증에서 실행 실패를 정답으로 세는 버그를 줄임.                                                                                 |


---

## 2. 현재 정확도가 낮게 나오는 이유 (다요인 분석)

### 2.1 목표·벤치의 정렬

- **혼합 난이도**(`numina_eval_balanced.json`: easy/medium/hard)에서 **단일 전체 정확도 80%**는 `TARGET_ACCURACY.md`의 **Easy 구간**과 동일 수준을 요구하는 셈이 되어, **통계적으로 기대치가 과도**할 수 있다.
- **Ralph 게이트 기본값(80%)**과 **스트라타 목표**를 동시에 만족시키려면 `AIMO_RALPH_GATE_MODE=easy` 또는 `by_difficulty` 보고를 병행해야 한다.

### 2.2 채점기 vs 파이프라인 의미

- Numina 평가에서 `variables={}`이면 `**verification_includes_reference_answer`는 false** — 오케스트레이터의 `verified`는 “내부 검증 통과”에 가깝고, **최종 채점은 `check_answer_correctness(reference, predicted)`** (`run_numina_evaluation.py` 경로).
- 따라서 **파이프라인 로그상 verified**와 **리포트 정확도**가 어긋날 수 있음.

### 2.3 모델·경로 이중성

- **Vertex Gemini** (`vertex_inference`)로 풀 오케스트레이터를 돌리는 경우와 **커스텀 엔드포인트**(`eval_vertex_endpoint_quality`)로만 평가하는 경우는 **같은 “정확도” 숫자가 아님** (프롬프트·형식·토큰 상한이 다름).

### 2.4 실행·추론 오류 (관측·코드)

- 생성 코드가 **샌드박스에서 실패**(`Error: ...`)하면 답 품질이 떨어짐. **투표/합의**가 잘못된 문자열을 끌어올리는 문제는 `is_execution_error_output`으로 완화.
- **기하·대수** 등에서 **다전략·다후보**가 비용·노이즈를 키움 — `OMI_USE_VOTING`, 후보 수, `AIMO_OPTIMIZE_ACCURACY`는 **정확도·비용 트레이드오프**.

### 2.5 형식 vs 정확도 (엔드포인트 경로)

- `FORMAT_AND_ACCURACY_PLAN.md` 요지: **strict 형식률**과 **최종 채점 정확도**는 별개. 폴백·검수로 정확도는 나와도 strict는 낮을 수 있음.

---

## 3. 개선 계획 (단계·변수 1개 원칙)

사용자 규칙과 `FORMAT_AND_ACCURACY_PLAN.md`의 **1단계→2단계→3단계**에 맞춘다.

### 3.0 선택된 정책 (Phase 1 — 목표·게이트 정렬)

아래를 **기본 채택**한다. 변경 시 본 절과 실험 노트([EXPERIMENT_NOTE_TEMPLATE.md](EXPERIMENT_NOTE_TEMPLATE.md))를 함께 갱신한다.


| 항목                | 선택                                                  | 근거                                                                                            |
| ----------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **1차 성공 기준**      | **스트라타 보고** (`by_difficulty` / `EvaluationMetrics`) | `TARGET_ACCURACY.md` 구간과 혼합 난이도 벤치에 맞추고, 전체 단일 %만으로 성공·실패를 단정하지 않는다.                          |
| **전체 정확도(Ralph)** | **보조 지표**                                           | `AIMO_RALPH_TARGET_ACCURACY_PCT` 기본 80%는 **참고**; 혼합 벤치에서만 “전체 80% 달성”을 **필수 성공 조건**으로 두지 않는다. |
| **Ralph 게이트 모드**  | 선택적 `AIMO_RALPH_GATE_MODE=easy`                     | Easy 버킷이 채워진 결과에서만 easy 단일 목표로 게이트할 때 사용 (`src/evaluation/ralph_accuracy.py`).                |
| **난이도 상한**        | 필요 시 `EVAL_DIFFICULTY_AT_MOST` 등                    | 범위를 줄인 뒤 목표 퍼센트를 **재등록**하고 문서·노트에 기록한다.                                                       |


**Path A vs B**: 동일 숫자로 **직접 비교하지 않는다** — `run_numina_evaluation` vs `eval_vertex_endpoint_quality`는 별도 실험 노트로 관리한다.

### 3.1 1단계 — 측정 정의 고정 (비용 적음)


| #   | 작업                                                                                                   | 완료 기준                                          |
| --- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| 1.1 | 평가 **경로** 명시: (A) Gemini+오케스트레이터 `run_numina_evaluation` vs (B) 엔드포인트 `eval_vertex_endpoint_quality` | 문서/실험 노트에 한 줄로 고정                              |
| 1.2 | **목표**를 스트라타와 정렬: 전체 / easy-only / medium-at-most 등                                                  | `TARGET_ACCURACY.md` 또는 `AIMO_RALPH_GATE_MODE` |
| 1.3 | 동일 `**seed`, `MAX_PROBLEMS`, 데이터 파일**로 재현성 확보                                                        | 결과 JSON에 `run_revision` 등 기록                   |


### 3.2 2단계 — 원인 분리 실험 (한 번에 하나만 변경)


| 우선순위 | 가설             | 실험                                                                                                                   | 비고                               |
| ---- | -------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| P0   | 모델 한계 vs 파이프라인 | **Arm A vs B** (동일 $\mathcal{D}$, 동일 L1) — [ARM_AB_PROTOCOL.md](../experiments/ARM_AB_PROTOCOL.md) (추론은 **클라우드 권장**) | “풀 파이프”가 베이스라인보다 나은지             |
| P1   | 형식 미준수         | `eval_vertex_endpoint_quality`에서 `max_format_retries`, `retry_temperature` (문서 표)                                    | 형식률·정확도 동시 표                     |
| P2   | 실행 실패율         | 코드 생성 프롬프트 / `AIMO_SELF_CORRECTION_MAX_ATTEMPTS` / executor 안정성                                                      | JSONL의 `error`, `scoring_status` |
| P3   | 난이도            | `--difficulty-at-most medium` 등으로 범위 축소 후 목표 재설정                                                                     | 혼합 60문항에서 80% 압박 완화              |


### 3.3 3단계 — 보고 가능한 규모

- `n-problems ≥ 50` (STEP2), 동일 프로토콜.
- 선택: BigQuery 적재, `diagnose_vertex_eval_jsonl.py`로 경로별 분해.

### 3.4 중단 기준·리스크

- **폴백만 늘리기**로 정확도만 올리면 strict 형식률은 그대로일 수 있음 (`FORMAT_AND_ACCURACY_PLAN.md` §5).
- **목표 지표·메트릭을 바꿔서** 성공한 것처럼 보이기 — **금지** (기존 연구 규정).

---

## 4. 요약


| 항목         | 결론                                                                          |
| ---------- | --------------------------------------------------------------------------- |
| 선행(레포) 적용  | Vertex·형식·Arm·스트라타 목표는 **그대로 적용 가능**; 다만 **경로별(Gemini vs 엔드포인트)** 지표 혼합 금지. |
| 저정확도 원인    | **목표-벤치 불일치**, **채점/verified 의미 차이**, **모델·실행·형식** 다층. 단일 원인이 아님.           |
| 개선 방향      | **측정 정의 고정 → Arm 대조 → 한 변수씩 튜닝 → 대규모 재현** 순서.                               |
| Phase 1 정책 | §3.0: 스트라타 1차, Ralph 전체 % 보조, optional easy 게이트·난이도 상한.                     |


본 문서는 `docs/vertex/FORMAT_AND_ACCURACY_PLAN.md`, `RESEARCH_EXPERIMENT_PROTOCOL.md`, `TARGET_ACCURACY.md`, `ZERO_ACCURACY_DEBUG.md`, `RALPH_VERTEX.md`와 함께 읽는 것을 권장한다.

**실행 보조 문서**: [EXPERIMENT_NOTE_TEMPLATE.md](EXPERIMENT_NOTE_TEMPLATE.md) · [../experiments/ARM_AB_PROTOCOL.md](../experiments/ARM_AB_PROTOCOL.md) · [TUNING_ONE_VARIABLE.md](TUNING_ONE_VARIABLE.md) · [SCALE_AND_GATES_RUNBOOK.md](SCALE_AND_GATES_RUNBOOK.md)