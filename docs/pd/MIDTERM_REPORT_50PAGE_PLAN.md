# 중간보고서 작성 계획 (~50페이지, 실험·시각화 중심)

> 이론은 **최소한**으로 두고, **가설 → 설정 → 실행 로그 → 수치 → 해석 → 한계** 순으로 채운다.  
> 인용·근거는 주로 `docs/` 아래 문서와 `results/*.json`, `logs/*.log`, `gradient_report_*.json` 을 사용한다.

---

## 1. 권장 분량(페이지 가이드)


| 절   | 주제                    | 권장 p | 비고                             |
| --- | --------------------- | ---- | ------------------------------ |
| 1   | 표지·요약·목차              | 2–3  | 한글 초록 + 키워드                    |
| 2   | 연구 목표·문제 정의           | 3–4  | 배경은 1–2p, 나머지는 **무엇을 재현·측정할지** |
| 3   | 시스템·데이터·평가 지표         | 5–7  | 파이프라인·Numina·채점만 간단히           |
| 4   | 실험 환경(Vertex·리전·모델)   | 6–8  | **표 + 가용성 매트릭스**가 본문           |
| 5   | 실험 A: 기준선·소규모 티어      | 6–8  | easy 30 등                      |
| 6   | 실험 B: 난이도·병렬(workers) | 8–10 | **가장 두껍게** — AB 설계 명시          |
| 7   | 실험 C: 429·토큰·경량 프리셋   | 6–8  | 스크립트·환경변수·관측                   |
| 8   | 결과 종합·시각화             | 8–12 | **그림 8–14개** + 표               |
| 9   | 논의·한계·윤리(조작 금지)       | 3–4  | 리전 편향, API 한도                  |
| 10  | 향후 계획·참고문헌·부록         | 4–6  | 명령어·환경 스냅샷은 부록                 |


**합계:** 약 48–58p (본문 조절로 50p 부근 맞춤)

---

## 2. `docs/` 우선순위 매핑 (절별)

**필수(실험·재현에 직결)**


| 문서 경로                                                         | 보고서에서 쓰는 위치         |
| ------------------------------------------------------------- | ------------------- |
| `docs/run-eval/VERTEX_AI.md`                                  | 절4 환경 변수·Vertex 조건  |
| `docs/run-eval/CLOUD_NUMINA_RUN.md`                           | 절3–5 클라우드 Numina 절차 |
| `docs/run-eval/RALPH_VERTEX.md` (있으면)                         | 정확도 게이트·엔드포인트 평가    |
| `docs/vertex/CAPACITY_AND_TOKEN_EFFICIENCY_EXECUTION_PLAN.md` | 절7 429·토큰 전략        |
| `docs/guides/NUMINA_INTEGRATION.md`                           | 절3 데이터·통합           |
| `docs/structure/PROJECT_STRUCTURE_AND_ORDER.md`               | 절3 스테이지·모듈 순서(짧게)   |
| `docs/eval/EVALUATION_AND_GRADING_CHRONICLE.md`               | 절3 채점·지표 연대기        |


**보조(필요 시 1–2p만)**


| 문서 경로                                              | 용도                |
| -------------------------------------------------- | ----------------- |
| `docs/getting-started/INTRODUCTION_HIGH_LEVEL.md`  | 절2 한 장 요약         |
| `docs/run-eval/QUICK_REFERENCE.md`, `FAST_EVAL.md` | 부록 명령             |
| `docs/guides/REFINE_LOOP_USAGE.md`                 | 실험에서 refine 켰을 때만 |
| `docs/todo/NEXT_STEPS.md`, `docs/todo/TODO.md`     | 절10               |
| `docs/pd/PD_WEEKLY_PROGRESS_300B.md`               | 주차별 타임라인(표로 압축)   |
| `docs/AIMO3/Report.md`                             | 대회 맥락 1p 이하       |


**이론 과다 방지:** `HYBRID_REASONING_ARCHITECTURE.md` 등은 **다이어그램 1개 + 한 단락**으로 제한.

---

## 3. 시각화 목록 (권장 10–14개 그림)

각 그림마다 **캡션에**: 데이터 출처 파일명, N(문항 수), 모델·리전, 날짜(또는 커밋 해시).


| #   | 제목(예)                             | 유형            | 데이터 소스                             |
| --- | --------------------------------- | ------------- | ---------------------------------- |
| F1  | 5-Stage 파이프라인 개요                  | 블록 다이어그램      | `PROJECT_STRUCTURE_AND_ORDER` 기반   |
| F2  | 평가 흐름(데이터→추론→채점)                  | 플로우           | 동일                                 |
| F3  | 모델 가용성                            | 히트맵 또는 표 시각화  | 실측 표(Seoul vs us-central1, 404 여부) |
| F4  | Easy 30 — 정확도 vs workers          | 막대 그래프        | `ab_workers*.json` 요약              |
| F5  | Easy 30 — 벽시계 시간 vs workers       | 막대            | 동일                                 |
| F6  | Medium 포함 30 — 정확도·에러율 vs workers | 그룹 막대         | `ab_medium_workers*.json`          |
| F7  | 동일 조건 wall time 비교                | 막대            | 동일                                 |
| F8  | 난이도별 정확도                          | 스택 또는 그룹 막대   | `summary` / `by_difficulty`        |
| F9  | 출처·스트라타 분포                        | 파이 또는 막대      | 결과 JSON 메타                         |
| F10 | Gradient 리포트 요약                   | 테이블 + 미니 차트   | `gradient_report_*.json`           |
| F11 | 실패 유형 비율                          | 도넛/막대         | timeout vs 429 vs 기타(로그 파싱 시)      |
| F12 | 토큰/비용 민감도                         | 산점도 또는 막대     | 환경변수별 실행                           |
| F13 | 주차별 진행(선택)                        | Gantt 또는 타임라인 | `PD_WEEKLY_PROGRESS_300B.md` 압축    |


**도구:** Python(`matplotlib`/`seaborn`)으로 `results/*.json`에서 필드 추출 후 PNG/PDF 저장 → 본문 삽입.  
한 페이지에 그림 1–2개 + 짧은 해석 문단이면 50p 구성이 자연스럽다.

---

## 4. 본문에 넣을 **핵심 수치 블록** (로컬 `results/` 기준, 2026-04-07~08 검증)

> `**results/`·`logs/`·대부분의 `*.json`은 `.gitignore`에 있음.** 저장소 클론만 하면 비어 있을 수 있고, Cursor 검색에도 안 잡힐 수 있다. 보고서·재현용으로는 로컬 경로를 근거로 적거나, 필요한 JSON만 화이트리스트 커밋을 검토할 것.

### 4.1 Workers AB (동일 조건에서 `workers`만 변경, N=30)


| 구분                | 결과 파일                                     | 정확도                | 총 평가 시간(s)  | error_rate | 비고                                                       |
| ----------------- | ----------------------------------------- | ------------------ | ----------- | ---------- | -------------------------------------------------------- |
| easy, workers=1   | `ab_workers1_20260407-222255.json`        | **63.33%** (19/30) | **1627.92** | 0%         | `by_method`에 `all_failed_rate_limited` 3건                |
| easy, workers=2   | `ab_workers2_20260407-225053.json`        | **56.67%** (17/30) | **803.39**  | 0%         | `all_failed_rate_limited` **7건** (병렬 시 rate limit 악화 정황) |
| medium, workers=1 | `ab_medium_workers1_20260407-230914.json` | **23.33%** (7/30)  | **2656.86** | **10%**    | 소스 metamath 30                                           |
| medium, workers=2 | `ab_medium_workers2_20260407-235410.json` | **30.00%** (9/30)  | **1151.70** | **6.67%**  | 벽시계는 단축; 정확도·에러는 API 상태에 민감                              |


각 파일 상단 `run_revision`(sha·dirty)과 `timestamp`를 보고서에 한 줄 인용하면 재현성이 좋다.

### 4.2 같은 필터의 다른 배치 결과 (파일명 혼동 방지)


| 파일                                        | N       | 정확도               | 비고                                                               |
| ----------------------------------------- | ------- | ----------------- | ---------------------------------------------------------------- |
| `numinamath_full_results_max_easy.json`   | **100** | **68.00%**        | AB의 30문항 실험과 **문항 수가 다름** — 본문에서 구분할 것                           |
| `numinamath_full_results_max_medium.json` | 30      | 23.33%, error 10% | `ab_medium_workers1`과 수치가 거의 동일(실행 시각만 다름); 둘 중 하나를 “대표 실행”으로 고정 |


### 4.3 리전·모델

문서·실험 로그에 따른 서술은 그대로 두되, **직접 호출해 확인한 표**를 부록에 두면 된다(Seoul `gemini-2.5-pro` 404 등).

→ 실험 절에서는 **“한 번에 바꾼 변수”** 를 문장으로 명시(예: workers만 변경, 나머지 동일).

---

## 4.4 오답 분류(보고용) — 자동 스크립트 + 평가 시 진단 필드

**새 Numina 평가**(`examples/run_numina_evaluation.py`)는 기본으로 각 행에 진단 메타를 붙인다 (`AIMO_EVAL_DIAGNOSTICS=0` 으로 끔).  
실험용으로 **진단 alternate로 재채점**하려면 `AIMO_EVAL_PREFER_DIAGNOSTIC_CANDIDATE=1` (기본 끔; 보고서 메인 지표와 혼동 주의).


| 필드                          | 의미                                                                                                    |
| --------------------------- | ----------------------------------------------------------------------------------------------------- |
| `grading_match_kind`        | `classify_answer_match` 결과 (`strict` / `sympy` / `none` 등)                                            |
| `eval_failure_axis`         | `correct` / `pipeline_or_empty` / `extraction_recoverable` / `format_or_grading` / `reasoning_likely` |
| `alternate_would_pass`      | 채점은 틀렸지만 `execution_result` 등에서 **다른 추출 후보**가 정답과 일치                                                  |
| `counterfactual_would_pass` | 맞았거나 위 alternate 성공 (보조 지표, **기본 is_correct 는 변경 안 함**)                                               |


Easy만 돌릴 때 **소스·유형별 세분 층**: `python examples/run_numina_evaluation.py --data-file numinamath_full.jsonl --difficulty-at-most easy --easy-stratum source` (또는 `problem_type` / `composite`, 환경 변수 `EVAL_EASY_STRATUM`). 요약·JSON에 `by_easy_stratum`, 행에 `easy_stratum`.

`save_results()` JSON을 **범주별로 집계**하려면:

```bash
python scripts/analyze_numina_failure_modes.py _eval_gemini31_m30/results/numinamath_full_results_max_medium.json
python scripts/analyze_numina_failure_modes.py results/ab_medium_workers1_20260407-230914.json --incorrect-only
```


| 버킷                        | 의미                                                                      |
| ------------------------- | ----------------------------------------------------------------------- |
| `pipeline_or_empty`       | `predicted_answer` 없음 / `all_failed*`·timeout·worker 예외                 |
| `extraction_recoverable`  | (신규) 본문(`execution_result` 등)에서 **다른 추출 후보**가 정답과 일치하는데 최종 `answer`만 틀림 |
| `format_or_grading`       | 밑 진법·느슨 수치 등 표기/채점 민감                                                   |
| `reasoning_or_extraction` | 그 외 (`reasoning_likely`)                                                |


**옛 JSON(진단 필드 없음):** 예) Gemini 3.1 30문항 — 정답 7 · `format_or_grading` 1 · `reasoning_or_extraction` 22. Flash는 429로 `pipeline_or_empty`가 늘 수 있음.  
**새로 돌린 JSON:** `eval_failure_axis`·`counterfactual_would_pass` 로 추출 vs 추론을 구분해 집계.

`extraction_recoverable` 은 **진단 휴리스틱**이며, 보고서에 쓸 때 규칙(후보 추출기 목록)을 함께 밝힐 것.

### 정답률·정확도를 올리는 방향

1. **안정성 먼저** — `GOOGLE_CLOUD_PROJECT` 설정, `workers=1`, 429 완화 프리셋; 없으면 오답이 아니라 **공백 오답**으로 잡힘.
2. **최종 답 추출** — 긴 추론 뒤 `\boxed{}`·마지막 수치만 쓰도록 후처리·프롬프트 정렬 (MCQ는 선택지 문자).
3. **채점기와의 정렬** — 밑 표기·분수 표기 등 **합의된 정규화**를 `check_answer_correctness` / `normalize_answer`에 반영할지 **연구적으로 결정** (완화는 “난이도 변경”이 아니라 **채점 계약** 변경이므로 버전·이유를 문서화).
4. **모델·추론 예산** — 동일 프로토콜에서만 Flash vs Pro/3.1·토큰·`thinking_level` 비교 (**한 변수**).
5. **Refine·투표** — 비용 허용 시 후보만 늘리고, 베이스라인과 혼동되지 않게 실험 ID를 분리.
6. **층화 분석** — `problem_type`·`question_type`별로 버킷 비율을 보고, 어디에 크레딧을 쓸지 우선순위 결정.

---

## 5. 절별 작성 체크리스트

- 각 실험: **목표 1문장 / 독립변수 1개 / 고정한 조건 목록 / 재현 명령(부록)**  
- 그림·표 번호 연속, 본문에서 `그림 4`처럼 참조  
- 실패·낮은 점수도 동일 비중으로 기술(선별 보고 금지)  
- `NEXT_STEPS.md` 와 모순 없게 향후 과제 정리

---

## 6. 산출물 파일명(정리용)

- AB 원시 결과: `results/ab_workers1_20260407-222255.json`, `ab_workers2_20260407-225053.json`, `ab_medium_workers1_20260407-230914.json`, `ab_medium_workers2_20260407-235410.json`  
- 대표 배치: `results/numinamath_full_results_max_easy.json` (N=100), `numinamath_full_results_max_medium.json` (N=30)  
- 그래디언트/요약: `results/ab_*_gradient_*.json`, `results/gradient_report_numinamath_full_max_*.json`  
- 로그: `logs/pipeline.log`, `logs/eval_log.jsonl`  
- 429 완화 실행: `scripts/run_numina_429_safe.ps1`

---

*이 파일은 보고서 **목차·그림 기획**용이며, §4 표는 2026-04-08 시점 로컬 JSON과 대조해 검증함.*