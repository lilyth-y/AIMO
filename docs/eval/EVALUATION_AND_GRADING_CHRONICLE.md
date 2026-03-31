# Eval·채점 개선 및 Vertex 운영 기록 (타임라인)

이 문서는 AIMO 프로젝트에서 **Vertex 온라인 추론**, **모델 전환(7B 등)**, **예산·타임아웃**, **채점 정규화·근사**, **추출/KPI·신뢰 데이터·보수적 규칙 확장(1→2→3)** 까지의 결정과 구현을 한곳에 정리한다.

---

## 1. Vertex·운영 맥락

- **엔드포인트**: `google.cloud.aiplatform.Endpoint.predict` 로 프롬프트·생성만 전달; strict `<ANS>` 검증은 클라이언트(`ans_format_guard`)에서 수행.
- **503 / 지연**: `predict` 타임아웃이 짧거나 `None`이면 gRPC 기본(~60s)에 걸려 끊기는 경우가 있어, eval 스크립트는 `_effective_predict_timeout` 으로 **최소**(기본 300s, `VERTEX_PREDICT_TIMEOUT_MIN`)·**바닥/상한**(기본 600s, `VERTEX_PREDICT_TIMEOUT_FLOOR` / `VERTEX_PREDICT_TIMEOUT_MAX`)을 맞춘다. 일시 오류는 클라이언트 재시도·행 단위 `predict_progress`로 추적한다.
- **비용**: L4 등 가격은 리전·할인·할당량에 따라 변동; **월 $10 수준·가끔 사용**은 소규모 `n-problems`·낮은 동시성·엔드포인트 미니 머신 구성으로 맞추는 식으로 설계. **실제 청구는 GCP 콘솔 Billing**에서 확인하는 것이 정확하다.
- **7B 전환**: 서빙/설정 문서 및 기본 모델 ID·스모크 eval JSONL 이름 등은 저장소 내 Vertex 관련 문서(`docs/vertex/` 등)와 스크립트 주석에 맞춰 갱신하는 흐름이 있었다.

---

## 2. 채점 파이프라인 (정규화 → 분류 → 지표)

### 2.1 정규화·근사

- `reasoning_utils.normalize_answer`: `\text{...}` 언랩, `\$`/`$` 제거, 공백·일부 기호 정리.
- `evaluation_utils.numeric_equivalent`: 두 값이 **유한 실수**로 읽힐 때만 `math.isclose` (기본 `rtol=1e-4` 등 — **116.67 vs 116.666…** 같은 표시 차이 허용).
- `classify_answer_match` / `check_answer_correctness`: **strict → ratio → interval → sympy → numeric** 순서(아래 3단계에서 interval 순서 확정).

### 2.2 Eval 출력

- JSONL 행에 `match_kind`(= `classify_answer_match` 결과), stdout 요약에 `match_kind_breakdown`.
- 대상 스크립트: `scripts/vertex/eval_vertex_endpoint_quality.py`, `scripts/eval_hf_local_quality.py`.

---

## 3. 순차 작업 1 → 2 → 3 (이번 세션 구현)

### 3.1 ① 추출 실패·파이프라인 KPI

- **공통 모듈** `src/evaluation/eval_grading.py`
  - `grade_completion_for_eval(reference, text, format_ok, fallback_boxed, last_resort, extractor)`
  - 경로: `ans_tag` / `no_ans_tag` / `ans_tag_empty` / `boxed_fallback` / `ans_tag_fallback` / `last_resort_tail` / `extract_failed` / `skipped`
- **선택 tail 추출**: `pipeline.reasoning_utils.extract_tail_answer_without_tags` — `<ANS>`·`\\boxed{}` 를 이미 시도한 **뒤**에만, 영문 “answer is”·문장형·마지막 숫자 줄·짧은 MCQ 한 글자 등 **보수적** 휴리스틱.
- **Vertex 플래그**: `--last-resort-extraction` 또는 `AIMO_EVAL_LAST_RESORT_EXTRACTION=1` (기본 **off**).
- **요약 지표**: `scoring_status_breakdown`, `extraction_route_breakdown`, `predicted_null_count` / `predicted_null_rate`, `nonempty_raw_predicted_null_count` / `…_rate`, 행 필드 `extraction_route`.
- **HF eval**도 동일 헬퍼를 쓰되 `fallback_boxed=False`, `last_resort=False` 로 기존 동작(형식 통과 시만 채점) 유지.

### 3.2 ② 검수·신뢰 가능한 eval 서브셋 (1차)

- **스크립트**: `scripts/eval/build_trusted_eval_subset.py`
  - Numina JSONL에서 소스·`answer` 길이·`problem` 길이로 필터 → `trusted_seed`·`subset_filters` 메타를 붙인 JSONL.
  - **최종 신뢰 라벨**(`trusted: true`)은 수동 검수 후 별도 관리하는 것을 전제로 한다.
- 예시 출력: `data/eval/trusted_subset_seed.jsonl` (로컬 생성 시).

### 3.3 ③ 채점 규칙 보수적 확장 (비율·구간)

- `**ratio_equivalent`**: 정답이 `a:b` (양의 정수 쌍)일 때만 `c/d`, `c:d` 또는 **정규화 후 스칼라**(예: `4/2` → `2`)와 분수 동치 비교.
- `**interval_pair_equivalent`**: 쉼표로 구분된 **두 실수 쌍**이 둘 다 동일 패턴일 때만 엔드포인트별 근사 비교; `normalize_answer`가 괄호·공백을 바꿔도 내부에서 괄호 제거 후 파싱.
- `**MatchKind`**: `ratio`, `interval` 추가; `classify_answer_match`에서 **interval을 sympy보다 앞**에 두어 순서쌍이 sympy Tuple 동치로만 잡히는 경우와 구분.

---

## 4. 테스트·회귀

- `tests/test_answer_match_grading.py`: strict/numeric/통화/`\text`/오답 유지 + **ratio·interval** 샘플.

---

## 5. 관련 파일 (빠른 탐색)


| 구분          | 경로                                                                     |
| ----------- | ---------------------------------------------------------------------- |
| 채점·분류       | `src/evaluation/evaluation_utils.py`                                   |
| Eval 공통 채점  | `src/evaluation/eval_grading.py`                                       |
| Tail 추출     | `src/pipeline/reasoning_utils.py` (`extract_tail_answer_without_tags`) |
| Vertex eval | `scripts/vertex/eval_vertex_endpoint_quality.py`                       |
| HF 로컬 eval  | `scripts/eval_hf_local_quality.py`                                     |
| 신뢰 서브셋 생성   | `scripts/eval/build_trusted_eval_subset.py`                            |
| 단위 테스트      | `tests/test_answer_match_grading.py`                                   |


---

## 6. 이후 권장

- `trusted_seed` JSONL을 **수동 검수**해 `trusted: true` 고정본을 만들고, eval에 `--data-file` 로만 쓰면 재현성이 좋다.
- tail 추출은 **오탐** 가능성이 있으므로, 리더보드 숫자에는 `--last-resort-extraction` 끈 값과 켠 값을 **나란히** 보고하는 것을 권장한다.

