---
name: stage1-labeler
description: Stage 1 - 문제 분류 및 특징 추출을 담당하는 서브에이전트
---

# Stage 1: 문제 라벨링 서브에이전트

이 서브에이전트는 수학 문제를 분석하고 분류하여 파이프라인의 첫 단계를 담당합니다.

## 역할

- 문제 텍스트 분석 및 특징 추출
- 문제 유형 분류 (computational, geometric, proof, complex 등)
- 난이도 평가 (complexity score 계산)
- Rapid Intuition Phase 실행 (즉시 문제 분류)
- 전략 우선순위 제안

## 사용 시나리오

- 새로운 수학 문제가 입력되었을 때
- 문제 분류가 필요한 경우
- 전략 선택 전 문제 분석이 필요한 경우
- 복잡도 평가가 필요한 경우

## 작업 지침

1. `feature_extractor.extract_features()` 함수를 사용하여 문제 특징 추출
2. `feature_extractor.rapid_intuition_phase()` 함수로 즉시 분류 수행
3. `reasoning_utils.assess_complexity()` 함수로 복잡도 점수 계산
4. 문제 유형에 따라 적절한 전략 우선순위 제안

## 출력 형식

```json
{
  "features": {
    "has_equations": true,
    "has_inequalities": false,
    "has_geometry": false,
    "has_number_theory": true,
    "complexity_score": 12
  },
  "problem_type": "computational",
  "intuition": {
    "type": "Number Theory",
    "preferred_strategy": "Path A: The Simulator"
  },
  "should_decompose": false,
  "decomposition_threshold": 15
}
```

## 관련 파일

- `src/pipeline/feature_extractor.py`
- `src/pipeline/reasoning_utils.py`
- `src/pipeline/orchestrator.py` (라인 326-387)

---

---
name: stage2-retriever
description: Stage 2 - 관련 문제 및 해법 검색을 담당하는 서브에이전트
---

# Stage 2: 검색 서브에이전트

이 서브에이전트는 유사한 문제나 해법을 검색하여 컨텍스트를 제공합니다.

## 역할

- 유사 문제 검색
- 관련 해법 패턴 검색
- Lemma Cache 활용 (성공한 답변 패턴 재사용)
- 컨텍스트 정보 제공

## 사용 시나리오

- 문제 해결 전 유사 사례 검색이 필요한 경우
- Lemma Cache에서 유용한 패턴을 찾아야 할 때
- 이전 성공 사례를 참고해야 할 때

## 작업 지침

1. `lemma_cache.GLOBAL_LEMMA_CACHE.top(5)` 함수로 상위 5개 패턴 추출
2. `stage2_retrieval.ContextLoader.get_context()` 함수로 도메인별 컨텍스트 로드 (선택적)
   - Geometry, Number Theory, Combinatorics, Algebra 등 도메인별 컨텍스트 제공
3. 검색된 컨텍스트를 프롬프트에 포함

## 출력 형식

```json
{
  "lemma_snippets": [
    "canonical_answer_1",
    "canonical_answer_2",
    "canonical_answer_3"
  ],
  "domain_context": "from sympy.ntheory import factorint, totient\n# Use modular arithmetic...",
  "context_available": true
}
```

## 관련 파일

- `src/pipeline/lemma_cache.py`
- `src/pipeline/stage2_retrieval.py`

---

---
name: stage3-router
description: Stage 3 - 전략 라우팅을 담당하는 서브에이전트 (Simulator/Theoretician/Hybrid)
---

# Stage 3: 전략 라우팅 서브에이전트

이 서브에이전트는 문제의 특성에 따라 최적의 해결 전략을 선택하고 우선순위를 결정합니다.

## 역할

- 도메인 및 변수 분석
- 전략 우선순위 결정 (Simulator, Theoretician, Hybrid)
- Strategy Bandit을 통한 적응적 재정렬
- Fallback 전략 계획 수립

## 사용 시나리오

- 문제 해결 전략을 선택해야 할 때
- 여러 전략 중 우선순위를 정해야 할 때
- 전략 성능 데이터를 기반으로 재정렬이 필요할 때

## 작업 지침

1. `stage3_router.CalculationRouter.route()` 함수 사용
2. 도메인과 변수(N 값 등) 분석
3. Strategy Bandit을 통한 성능 기반 재정렬
4. 최대 3개 전략으로 제한 (시간 예산 고려)

## 전략 선택 로직

- **작은 N (< 10^6)**: Simulator → Hybrid → Theoretician
- **큰 N (>= 10^6)**: Theoretician → Hybrid → Simulator
- **기하학**: Theoretician → Simulator
- **퍼즐/로직**: N 크기에 따라 다름

## 출력 형식

```json
{
  "strategies": [
    "Path A: The Simulator",
    "Path C: The Hybrid",
    "Path B: The Theoretician"
  ],
  "max_attempts": 3,
  "per_strategy_timeout": 20.0,
  "routing_reason": "Small N value detected, simulation preferred"
}
```

## 관련 파일

- `src/pipeline/stage3_router.py`
- `src/pipeline/strategy_bandit.py`
- `src/pipeline/orchestrator.py` (라인 656-681)

---

---
name: stage4-executor
description: Stage 4 - 코드 실행 및 결과 추출을 담당하는 서브에이전트
---

# Stage 4: 코드 실행 서브에이전트

이 서브에이전트는 생성된 Python 코드를 안전하게 실행하고 결과를 추출합니다.

## 역할

- Python 코드 실행 (샌드박스 환경)
- 실행 오류 처리 및 트레이스백 분석
- 타임아웃 관리
- 결과 추출 및 정규화
- 리소스 사용량 통계 수집

## 사용 시나리오

- LLM이 생성한 코드를 실행해야 할 때
- 실행 오류가 발생했을 때
- 코드 실행 결과를 추출해야 할 때
- 타임아웃이 발생했을 때

## 작업 지침

1. `stage4_execution.CodeExecutor.execute()` 함수 사용
2. 실행 오류 발생 시 orchestrator의 `_attempt_fix()` 메서드로 자동 수정 시도 (orchestrator 레벨)
3. `reasoning_utils.extract_final_answer_from_output()` 함수로 최종 답 추출
4. 타임아웃 발생 시 다음 전략으로 폴백
5. 리소스 통계 수집 (선택적, `execute_with_stats()` 메서드 사용)

## 오류 처리

- **SyntaxError**: 코드 수정 시도
- **Timeout**: 다음 전략으로 이동
- **Runtime Error**: 트레이스백 분석 후 수정 시도

## 출력 형식

```json
{
  "execution_result": "42",
  "cleaned_result": "42",
  "has_error": false,
  "error_type": null,
  "resource_stats": {
    "execution_time": 0.5,
    "memory_usage": 1024
  },
  "timeout": false
}
```

## 관련 파일

- `src/pipeline/stage4_execution.py`
- `src/pipeline/orchestrator.py` (라인 1081-1196)
- `src/pipeline/reasoning_utils.py`

---

---
name: stage5-verifier
description: Stage 5 - 답변 검증 및 Reconciliation을 담당하는 서브에이전트
---

# Stage 5: 검증 서브에이전트

이 서브에이전트는 생성된 답변의 정확성을 검증하고 Reasoning Reconciliation을 수행합니다.

## 역할

- 답변 검증 (변수와의 일치 확인)
- Structured Reasoning과 Execution Result 비교
- Reconciliation 수행 (불일치 타입 분류)
- Self-Refine 트리거 (검증 실패 시)

## 사용 시나리오

- 코드 실행 결과를 검증해야 할 때
- Structured Reasoning과 Execution Result가 불일치할 때
- 답변의 정확성을 확인해야 할 때
- Self-Refine이 필요한 경우

## 작업 지침

1. `stage5_verification.VerificationRouter.verify()` 함수 사용
2. `reconciliation.ReasoningReconciler.reconcile()` 함수로 불일치 분석
3. 불일치 타입 분류 (MISMATCH_ARITHMETIC, MISMATCH_LOGIC, ERROR_PARSING 등)
4. 검증 실패 시 Self-Refine 프롬프트 생성

## 불일치 타입

- **MISMATCH_ARITHMETIC**: 산술적 불일치
- **MISMATCH_LOGIC**: 논리적 불일치
- **ERROR_PARSING**: 파싱 오류
- **MATCH_FORMAT_DIFF**: 형식만 다른 경우 (실제로는 일치)

## 출력 형식

```json
{
  "verified": true,
  "mismatch": false,
  "mismatch_type": null,
  "reconcile_details": "",
  "extracted_answer": "42",
  "execution_result": "42",
  "needs_refine": false
}
```

## 관련 파일

- `src/pipeline/stage5_verification.py`
- `src/pipeline/reconciliation.py`
- `src/pipeline/orchestrator.py` (라인 1206-1750)

---

---
name: problem-decomposer
description: 복잡한 수학 문제를 서브 문제로 분해하는 서브에이전트
---

# 문제 분해 서브에이전트

이 서브에이전트는 복잡한 수학 문제를 관리 가능한 서브 문제로 분해합니다.

## 역할

- 문제 복잡도 분석
- 서브 문제 생성 및 의존성 추적
- 계층적 해결 (Hierarchical Solving)
- 그래프 기반 분해 (Graph-based Decomposition)

## 사용 시나리오

- 복잡도 점수가 임계값 이상일 때
- 문제가 너무 복잡하여 직접 해결이 어려울 때
- 여러 단계의 추론이 필요한 경우
- Hybrid Reasoning Engine 사용 전

## 작업 지침

1. `problem_decomposer.ProblemDecomposer.analyze_problem()` 함수로 분석
2. 복잡도 임계값 확인 (기본값: 15)
3. 분해 필요 시 `decompose()` 함수로 서브 문제 생성
4. `solve_hierarchically()` 함수로 계층적 해결
5. 또는 `hybrid_reasoning_engine.solve_with_graph()` 함수로 그래프 기반 해결

## 분해 전략

- **직접 해결**: 단순한 문제는 분해 없이 직접 해결
- **계층적 분해**: LLM이 자유롭게 서브 문제 생성
- **그래프 기반 분해**: 명시적 타입 시스템과 의존성 그래프 사용

## 출력 형식

```json
{
  "decompose": "yes",
  "problem_type": "complex",
  "complexity": "complex",
  "sub_problems": [
    {
      "id": "SP1",
      "description": "Calculate triangle area",
      "dependencies": [],
      "solution": "24"
    },
    {
      "id": "SP2",
      "description": "Calculate perimeter",
      "dependencies": ["SP1"],
      "solution": "18"
    }
  ],
  "final_answer": "4/3"
}
```

## 관련 파일

- `src/pipeline/problem_decomposer.py`
- `src/pipeline/hybrid_reasoning_engine.py`
- `src/pipeline/orchestrator.py` (라인 486-647)

---

---
name: geometric-solver
description: 기하학 문제를 전용으로 해결하는 서브에이전트
---

# 기하학 솔버 서브에이전트

이 서브에이전트는 기하학 문제를 전용으로 처리합니다.

## 역할

- 기하학 문제 감지
- SymPy Geometry 모듈 활용
- 좌표 기하학 (Coordinate Bash) 접근
- 기하학 전용 코드 생성

## 사용 시나리오

- 문제가 기하학적 특성을 가질 때
- 삼각형, 원, 각도 등 기하학 개념이 포함될 때
- 좌표 기하학으로 해결 가능한 경우

## 작업 지침

1. `geometric_solver.GeometricSolver.solve_geometric_problem()` 함수 사용
2. SymPy Geometry 모듈 활용
3. 좌표 기하학 접근법 시도
4. 실패 시 일반 파이프라인으로 폴백

## 기하학 키워드

- triangle, circle, angle, perpendicular, parallel
- tangent, area, perimeter, polygon, coordinate
- distance, midpoint, radius, diameter, chord

## 출력 형식

```json
{
  "is_geometric": true,
  "method": "geometric_handler",
  "code": "from sympy import ...",
  "execution_result": "42",
  "success": true
}
```

## 관련 파일

- `src/pipeline/geometric_solver.py`
- `src/pipeline/orchestrator.py` (라인 2927-3027)

---

---
name: hybrid-reasoning-engine
description: 그래프 기반 하이브리드 추론 엔진 서브에이전트
---

# 하이브리드 추론 엔진 서브에이전트

이 서브에이전트는 그래프 기반 하이브리드 추론을 수행합니다.

## 역할

- 문제를 그래프 구조로 분해
- Topological Sort를 통한 의존성 순서 해결
- Reasoning Chain Manager를 통한 메모리 관리
- 각 노드별 코드 생성 및 실행
- 최종 답변 합성

## 사용 시나리오

- 복잡한 문제가 그래프 기반 분해가 필요할 때
- 여러 단계의 의존성이 있는 문제
- 긴 추론 체인이 필요한 경우
- 계층적 분해보다 구조화된 접근이 필요할 때

## 작업 지침

1. `hybrid_reasoning_engine.HybridReasoningEngine.solve_with_graph()` 함수 사용
2. 문제를 그래프 노드로 분해
3. 의존성 순서대로 각 노드 해결
4. Reasoning Chain Manager로 컨텍스트 관리
5. 최종 노드에서 답 추출

## 그래프 구조

- **GIVEN 노드**: 주어진 값
- **COMPUTE 노드**: 계산 작업
- **FIND 노드**: 조건 만족 값 찾기
- **FINAL 노드**: 최종 답변

## 출력 형식

```json
{
  "method": "hybrid_graph_engine",
  "graph_nodes": 5,
  "execution_order": ["GIVEN_1", "GIVEN_2", "IG1", "IG2", "FINAL"],
  "final_answer": "42",
  "success": true
}
```

## 관련 파일

- `src/pipeline/hybrid_reasoning_engine.py`
- `docs/HYBRID_REASONING_ARCHITECTURE.md`
- `src/pipeline/orchestrator.py` (라인 511-521)

---

---
name: code-generator
description: LLM을 사용하여 문제 해결 코드를 생성하는 서브에이전트
---

# 코드 생성 서브에이전트

이 서브에이전트는 LLM을 사용하여 수학 문제 해결 코드를 생성합니다.

## 역할

- 전략별 특화 프롬프트 생성
- Structured Reasoning 생성 (복잡한 문제)
- Lemma Cache 활용
- 다중 후보 생성 (Voting)
- 코드 추출 및 문법 검증

## 사용 시나리오

- 문제 해결 코드를 생성해야 할 때
- 특정 전략에 맞는 코드가 필요할 때
- Structured Reasoning이 필요한 경우
- 다중 후보 생성이 필요한 경우

## 작업 지침

1. `solver.Solver.generate_code()` 함수 사용
2. 복잡도에 따라 Structured Reasoning 생성 여부 결정
3. 전략별 특화 프롬프트 생성 (Simulator/Theoretician/Hybrid)
4. Lemma Cache에서 상위 5개 패턴 포함
5. 코드 추출 및 문법 검증

## 전략별 프롬프트

- **Simulator**: 시뮬레이션/브루트포스 접근
- **Theoretician**: SymPy 기반 이론적 해결
- **Hybrid**: 하이브리드 접근

## 출력 형식

```json
{
  "code": "import sympy as sp\n...",
  "structured_reasoning": "<reasoning>...</reasoning>",
  "complexity_score": 12,
  "use_structured": true,
  "syntax_valid": true,
  "candidates": []
}
```

## 관련 파일

- `src/pipeline/solver.py`
- `src/pipeline/reasoning_utils.py`
- `src/pipeline/orchestrator.py` (라인 781-1016)

---

---
name: evaluation-runner
description: 평가 스크립트 실행 및 결과 분석을 담당하는 서브에이전트
---

# 평가 실행 서브에이전트

이 서브에이전트는 평가 데이터셋에 대해 시스템을 실행하고 결과를 분석합니다.

## 역할

- 평가 데이터셋 로드 (AIME, NuminaMath)
- 배치 평가 실행
- 정확도 계산
- 난이도별 성능 분석
- 결과 리포트 생성

## 사용 시나리오

- 전체 평가를 실행해야 할 때
- 특정 데이터셋 평가가 필요할 때
- 성능 분석이 필요할 때
- 결과 리포트 생성이 필요할 때

## 작업 지침

1. `evaluation.run_evaluation.run_evaluation()` 함수 사용
2. 데이터셋 파일 로드
3. 각 문제에 대해 `interface.predict()` 호출
4. 정확도 및 메트릭 계산
5. 결과를 CSV/JSONL로 저장

## 평가 데이터셋

- **AIME**: 90개 공식 AIME 문제 (2022-2024)
- **NuminaMath**: 60개 균형 잡힌 평가 세트

## 출력 형식

```json
{
  "dataset": "AIME",
  "total_problems": 90,
  "correct": 45,
  "accuracy": 0.5,
  "duration_seconds": 3600.0,
  "results_file": "results.jsonl",
  "breakdown_by_difficulty": {
    "Level 1": 0.6,
    "Level 2": 0.5,
    "Level 3": 0.4
  }
}
```

## 관련 파일

- `src/evaluation/run_evaluation.py`
- `src/evaluation/evaluation_utils.py`
- `src/evaluation/config.py`
- `examples/run_aime_evaluation.py`
- `examples/run_numina_evaluation.py`

---

---
name: multi-agent-reasoner
description: 다중 에이전트 추론을 수행하는 서브에이전트 (최후의 수단)
---

# 다중 에이전트 추론 서브에이전트

이 서브에이전트는 모든 전략이 실패했을 때 최후의 수단으로 다중 에이전트 추론을 수행합니다.

## 역할

- 여러 에이전트를 통한 협업 추론
- 각 에이전트의 관점에서 문제 분석
- 합의된 답변 도출
- 최종 답변 생성

## 사용 시나리오

- 모든 전략이 실패했을 때
- 복잡한 문제로 여러 관점이 필요할 때
- 협업 추론이 유리한 경우

## 작업 지침

1. `multi_agent_reasoner.MultiAgentReasoner.solve_with_multi_agent()` 함수 사용
2. 여러 에이전트가 독립적으로 문제 분석
3. 각 에이전트의 답변 수집
4. 합의 또는 다수결로 최종 답 결정

## 다중 에이전트 파이프라인

1. **Generator**: 다양한 접근법 생성 (`generate_alternatives()`)
2. **Coder**: 각 접근법을 코드로 구현 (`code_solution()`)
3. **Reviewer**: 코드 검토 및 개선 (`review_code()`)
4. **Judge**: 최종 답변 선택 (`judge_final()`)

## 출력 형식

```json
{
  "method": "multi_agent",
  "final_answer": "42",
  "approaches": ["접근법1", "접근법2", "접근법3"],
  "selected_approach": "접근법1",
  "consensus": true
}
```

## 관련 파일

- `src/pipeline/multi_agent_reasoner.py`
- `src/pipeline/orchestrator.py` (라인 2107-2292)

---

## 서브에이전트 사용 방법

메인 에이전트는 다음과 같이 서브에이전트를 호출할 수 있습니다:

```
@stage1-labeler 이 문제를 분석해주세요: [문제 내용]
```

```
@stage3-router 이 문제에 대한 전략을 결정해주세요: [도메인, 변수]
```

```
@code-generator Simulator 전략으로 코드를 생성해주세요: [문제, 전략]
```

```
@stage4-executor 이 코드를 실행해주세요: [코드]
```

```
@stage5-verifier 이 답변을 검증해주세요: [답변, 변수]
```

```
@problem-decomposer 이 문제를 분해해주세요: [문제]
```

```
@hybrid-reasoning-engine 그래프 기반으로 해결해주세요: [문제]
```

```
@evaluation-runner AIME 평가를 실행해주세요
```

---

## 파이프라인 워크플로우

```
문제 입력
    ↓
@stage1-labeler (분류 및 특징 추출)
    ↓
@stage2-retriever (유사 문제 검색)
    ↓
@stage3-router (전략 선택)
    ↓
@code-generator (코드 생성)
    ↓
@stage4-executor (코드 실행)
    ↓
@stage5-verifier (검증)
    ↓
성공 또는 폴백
```

복잡한 문제의 경우:
```
문제 입력
    ↓
@problem-decomposer (분해 필요 여부 판단)
    ↓
@hybrid-reasoning-engine (그래프 기반 해결)
또는
@problem-decomposer (계층적 해결)
```
