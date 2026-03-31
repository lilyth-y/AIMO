# Agentic AI on Vertex AI (AIMO 실행안)

이 문서는 `docs/MATH_SOLVING_ARCHITECTURE_EVALUATION.md`를 기준 사양으로 삼아, 현재 AIMO 파이프라인을 Vertex AI 기반 Agentic 구조로 운영하기 위한 구현 계획을 정리합니다.

## 1) 목표와 기준

- 현재 강점(전략 라우팅, 분해, 검증, 폴백)을 유지한다.
- 약점(Stage1 분류 정확도, 복잡도 판단, 특수 경로 진입 타이밍)을 Vertex 기능으로 보강한다.
- 최종 목표는 "문제 1건 당 자동 계획 -> 도구 실행 -> 검증 -> 필요 시 재시도"가 로그/메트릭과 함께 재현 가능하게 동작하는 것이다.

## 2) 현재 파이프라인 -> Vertex 기능 매핑

| AIMO 구성 | 역할 | Vertex 매핑 |
|---|---|---|
| Stage1 (`classify_problem`, 변수 추출) | 문제 타입/복잡도 추정 | Gemini(소형 프롬프트) + Cloud Run 분류 서비스 |
| Stage2/3 (`CalculationRouter`, `StrategyBandit`) | 전략 후보 생성/우선순위 | Cloud Run Orchestrator + BigQuery 성능 로그 기반 재정렬 |
| Decompose/Hybrid | 복잡 문제 분해/그래프 풀이 | Gemini 계획 생성 + Cloud Run 작업 그래프 실행 |
| Stage4 Code Execution | 코드 실행/리소스 제한 | Cloud Run Jobs 또는 GKE sandbox executor |
| Stage5 Verification | 정답 등가/형식 검증 | 기존 SymPy verifier 유지 + Vertex Eval/BigQuery 리포팅 |
| RefineLoop / Self-Correction | 실패 시 재시도 | Orchestrator 루프 + 재프롬프트 + 최대 반복 수 정책 |
| 추론 백엔드 | LLM 호출 | Vertex Gemini + (필요 시) Vertex Endpoint(Qwen) |

## 3) 권장 아키텍처 (MVP)

1. **Ingress**: Cloud Run API (`/solve`)가 문제를 받는다.
2. **Planner**: Gemini가 `problem_type`, `complexity`, `strategy_list`를 구조화 JSON으로 반환한다.
3. **Executor Router**: Orchestrator가 전략 순서대로 실행한다.
4. **Tool Calls**: 코드 실행은 sandbox service로 호출한다.
5. **Verifier**: 기존 SymPy/정규화 로직으로 통과 여부를 판정한다.
6. **Refine Loop**: 실패 시 최대 N회 재시도한다.
7. **Observability**: Cloud Logging + BigQuery에 단계별 로그를 적재한다.

## 4) 구현 순서 (MVP -> 고도화)

### Phase A. MVP (2~4일)

- Cloud Run 오케스트레이터 진입점 추가 (`/solve`).
- 기존 `orchestrator.solve_problem`를 API에서 호출하도록 래핑.
- Stage1 앞단에 "LLM 1회 분류 옵션" 플래그 추가:
  - `use_llm_stage1_classifier=true`면 Gemini 분류 결과를 사용.
  - 실패 시 기존 키워드/정규식 분류로 폴백.
- 로그 스키마 통일:
  - `request_id`, `stage`, `strategy`, `verified`, `latency_ms`, `error_type`.

### Phase B. Agentic 강화 (1~2주)

- 전략 선택에 Bandit 피드백 반영:
  - BigQuery 최근 성능으로 전략 우선순위 재조정.
- 분해 경로 개선:
  - 복잡도 높음 + proof/find-all 유형은 초기부터 decompose/multi-agent 우선.
- RefineLoop 다중 반복 정책 정교화:
  - mismatch 유형별 최대 반복 횟수 차등.

### Phase C. 운영 고도화 (지속)

- Vertex Pipelines로 배치 평가 자동화.
- Vertex Model Monitoring/Custom metrics 대시보드 연결.
- 실패 케이스 자동 수집 -> 프롬프트/라우팅 정책 업데이트.

## 5) 핵심 정책 (문서의 약점 보완 포인트 반영)

### 5.1 Stage1 정확도 보강

- 기본은 기존 휴리스틱 유지(빠름, 비용 0).
- 고난도/긴 문제에만 Gemini 분류 1회 호출.
- 휴리스틱 vs LLM 결과가 다르면:
  - `complexity_score`가 높을 때 LLM 결과 우선.
  - 그렇지 않으면 휴리스틱 유지.

### 5.2 전략 진입 정책

- `problem_type in {proof, find_all}` 이고 복잡도 높으면:
  - multi-agent/decompose를 앞 순서에 배치.
- 수치 계산 중심 + 짧은 문제는:
  - 기존 Simulator 우선 정책 유지.

### 5.3 검증 우선 재시도

- 실행 성공 + 검증 실패일 때만 RefineLoop 강화.
- 실행 자체 실패는 즉시 다음 전략 폴백.
- 반복 상한 초과 시 "현재 최고 신뢰 후보 + 실패 로그" 반환.

## 6) Vertex 구성 권장값

- **리전**: 운영/비용 균형은 `us-central1`, 한국 지연 최소화는 `asia-northeast3`.
- **추론 모델**:
  - 분류/플래너: Gemini Flash 계열.
  - 수학 생성/코드: 기존 Qwen Endpoint 또는 Gemini 혼합.
- **서비스 분리**:
  - Orchestrator API (Cloud Run)
  - Code Executor (Cloud Run Job/GKE)
  - Endpoint Inference Client (내부 모듈)

## 7) 성공 기준 (운영 KPI)

- 정확도: 현재 baseline 대비 +X% (문제군별 분리 측정).
- 비용: 문제당 평균 추론 비용 상한 설정.
- 안정성: 5xx 비율, 타임아웃 비율, 재시도율 추적.
- 품질: `verification_pass_rate`, `fallback_rate`, `refine_success_rate`.

## 8) 바로 실행할 작업 항목

1. Cloud Run 오케스트레이터 엔드포인트 생성.
2. Stage1 LLM 분류 옵션 플래그 도입.
3. BigQuery 로그 테이블 생성(단계별 이벤트 스키마 고정).
4. 전략 재정렬(Bandit)용 오프라인 잡 초안 작성.
5. `docs/run-eval/VERTEX_AI.md`와 연결해 운영 체크리스트 추가.

---

실행 기준 문서:
- `docs/MATH_SOLVING_ARCHITECTURE_EVALUATION.md`
- `docs/run-eval/VERTEX_AI.md`
- `docs/guides/HYBRID_REASONING_ARCHITECTURE.md`
- `docs/guides/REFINE_LOOP_USAGE.md`
