# Hybrid Reasoning Architecture

## 개요

MathCodeOrchestrator 프로젝트의 긴 추론 체인 처리를 위한 하이브리드 아키텍처 설계 문서입니다.

## 핵심 질문과 해결책

### 1. 긴 추론 체인 처리 전략

**문제**: 복잡한 수학 문제는 여러 단계의 추론을 거쳐야 하는데, 각 단계의 맥락을 어떻게 유지할 것인가?

**해결책**: **ReasoningChainManager** - Mamba 스타일의 계층적 메모리 시스템

```
┌─────────────────────────────────────────────┐
│       Reasoning Chain Manager               │
├─────────────────────────────────────────────┤
│                                             │
│  Long-Term Memory (Compressed Checkpoints) │
│  ├─ Checkpoint 1: Steps 1-3 요약          │
│  ├─ Checkpoint 2: Steps 4-6 요약          │
│  └─ Checkpoint 3: Steps 7-9 요약          │
│                                             │
│  Working Memory (Recent Detailed Steps)    │
│  ├─ Step 10: 삼각형 넓이 계산 = 24       │
│  ├─ Step 11: 높이 구하기 = 6              │
│  └─ Step 12: 빗변 길이 = 10               │
│                                             │
└─────────────────────────────────────────────┘
```

**장점**:
- **O(n) 복잡도**: 긴 추론 체인도 효율적 처리 (Mamba 원리)
- **자동 압축**: Working memory가 가득 차면 자동으로 체크포인트 생성
- **계층적 컨텍스트**: 요약(개요) + 상세(최근) 정보 동시 제공

### 2. Transformer와 Mamba 조합 전략

**문제**: Transformer는 긴 시퀀스에서 O(n²) 복잡도로 비효율적이고, Mamba는 로컬 정밀 추론에 약함

**해결책**: **계층적 어텐션 시스템**

```
┌──────────────────────────────────────────────────┐
│         Hybrid Reasoning Architecture            │
├──────────────────────────────────────────────────┤
│                                                  │
│  Phase 1: Global Understanding (Mamba-style)    │
│  ┌────────────────────────────────────────────┐ │
│  │ 전체 문제 + 모든 서브 문제 구조 인코딩      │ │
│  │ • 의존성 관계 파악                          │ │
│  │ • 글로벌 맥락 생성 (O(n) 복잡도)          │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  Phase 2: Local Solving (Transformer)           │
│  ┌────────────────────────────────────────────┐ │
│  │ 각 서브 문제를 정밀하게 해결                │ │
│  │ • 글로벌 컨텍스트 + 로컬 의존성            │ │
│  │ • 짧은 시퀀스 → O(n²)도 괜찮음            │ │
│  │ • 현재 Qwen LLM 활용                        │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  Phase 3: Synthesis (Mamba-style)               │
│  ┌────────────────────────────────────────────┐ │
│  │ 모든 솔루션 통합하여 최종 답 생성          │ │
│  │ • 전체 문맥 고려 (O(n) 복잡도)            │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
└──────────────────────────────────────────────────┘
```

**실제 구현**:
- **Mamba 역할**: `ReasoningChainManager`가 긴 컨텍스트 압축 및 관리
- **Transformer 역할**: `Qwen LLM`이 각 노드(서브 문제) 정밀 해결
- **하이브리드**: 긴 시퀀스는 압축, 짧은 추론은 정밀하게

### 3. LLM이 이해할 수 있는 문제 분할 로직

**문제**: 문제를 어떻게 분할하고, LLM이 각 부분을 명확히 이해하도록 할 것인가?

**해결책**: **그래프 기반 구조화 + 명시적 타입 시스템**

#### 3.1 명시적 문제 타입

```python
PROBLEM_TYPES = {
    "COMPUTE": "Calculate a specific numeric value",
    "FIND": "Find values satisfying conditions",
    "PROVE": "Prove a mathematical statement",
    "COUNT": "Count objects meeting criteria",
    "OPTIMIZE": "Find maximum/minimum values"
}
```

각 노드는 명확한 타입을 가지며, LLM은 타입별로 특화된 프롬프트를 받습니다.

#### 3.2 문제 그래프 구조

```
예시 문제: "삼각형 ABC에서 AB=5, BC=7, CA=6일 때, 넓이를 구하고, 
           내접원의 반지름을 구하라."

생성된 그래프:
┌─────────────────────────────────────────────────┐
│              Problem Graph                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  ○ GIVEN_1 [GIVEN]                            │
│     "AB = 5"                                    │
│     Dependencies: None                          │
│                                                 │
│  ○ GIVEN_2 [GIVEN]                            │
│     "BC = 7"                                    │
│     Dependencies: None                          │
│                                                 │
│  ○ GIVEN_3 [GIVEN]                            │
│     "CA = 6"                                    │
│     Dependencies: None                          │
│                                                 │
│  ○ IG1 [COMPUTE]                              │
│     "삼각형의 넓이 계산 (헤론의 공식)"       │
│     Dependencies: GIVEN_1, GIVEN_2, GIVEN_3    │
│                                                 │
│  ○ IG2 [COMPUTE]                              │
│     "둘레(s) 계산"                              │
│     Dependencies: GIVEN_1, GIVEN_2, GIVEN_3    │
│                                                 │
│  ○ FINAL [COMPUTE]                            │
│     "내접원 반지름 r = Area / s"               │
│     Dependencies: IG1, IG2                      │
│                                                 │
└─────────────────────────────────────────────────┘

실행 순서 (Topological Sort):
GIVEN_1 → GIVEN_2 → GIVEN_3 → IG1 → IG2 → FINAL
```

#### 3.3 타입별 특화 프롬프트

**COMPUTE 타입**:
```
=== Task ID: IG1 ===
Type: COMPUTE - Calculate a specific numeric value
Goal: 삼각형의 넓이 계산 (헤론의 공식)

Known Values:
GIVEN_1 (GIVEN): 5
GIVEN_2 (GIVEN): 7
GIVEN_3 (GIVEN): 6

Historical Context:
(No previous work)

Write Python code to COMPUTE the exact numeric value. Print ONLY the final result.
```

**FIND 타입**:
```
=== Task ID: IG2 ===
Type: FIND - Find values satisfying conditions
Goal: 모든 소수 찾기 (N 이하)

Known Values:
GIVEN_1 (GIVEN): N = 100

Write Python code to FIND all values satisfying the conditions. Print all solutions.
```

## 통합 워크플로우

```
┌─────────────────────────────────────────────────────────────┐
│                  Problem Solving Workflow                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │  • Computational / Geome
         │  1. Problem Classification           │tric /        │
         │    Complex                            │
         └──────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
         Simple │                       │ Complex
                ▼                       ▼
    ┌──────────────────┐    ┌────o────────────────────┐
    │  Standard Flow   │    │  Hybrid Reasning      │
    │  (TIR Pipeline)  │    │  Engine                │
    └──────────────────┘    └────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────┐
                        │  2. Graph Decomposition   │
                        │  (SmartDecomposer)        │
                        └───────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────┐
                        │  3. Topological Sort      │
                        │  (Dependency Order)       │
                        └───────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────┐
                        │  4. Node-by-Node Solving  │
                        │  • Generate Prompt        │
                        │  • LLM → Code             │
                        │  • Execute                │
                        │  • Update Chain Manager   │
                        └───────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────┐
                        │  5. Final Synthesis       │
                        │  (Extract FINAL node)     │
                        └───────────────────────────┘
```

## 핵심 클래스 구조

### 1. ReasoningChainManager
- **역할**: 긴 추론 체인의 메모리 관리
- **특징**: Long-term (압축) + Working (상세) 메모리
- **복잡도**: O(n)

### 2. ProblemGraph
- **역할**: 문제의 구조화된 표현
- **특징**: 노드(서브 문제) + 엣지(의존성)
- **알고리즘**: Kahn's Topological Sort

### 3. SmartDecomposer
- **역할**: 문제를 그래프로 분해
- **특징**: 명시적 타입 시스템 + JSON 구조화
- **출력**: ProblemGraph

### 4. HybridReasoningEngine
- **역할**: 전체 워크플로우 통합
- **특징**: Decomposer + ChainManager + Solver + Executor 조합

## 사용 예시

### 기존 방식 (Hierarchical)
```python
# problem_decomposer.py의 solve_hierarchically
result = decomposer.solve_hierarchically(problem_text, solver, executor)
# → LLM이 자유롭게 서브 문제를 텍스트로 생성
# → 구조가 불명확할 수 있음
```

### 새로운 방식 (Graph-based)
```python
# hybrid_reasoning_engine.py
hybrid_engine = HybridReasoningEngine(solver, executor)
result = hybrid_engine.solve_with_graph(problem_text)
# → 명확한 그래프 구조 (노드 + 의존성)
# → 타입별 특화 프롬프트
# → 체크포인트 기반 메모리 관리
```

### Orchestrator에서의 자동 라우팅
```python
# orchestrator.py
if problem_type == 'complex':
    try:
        # 먼저 Hybrid Engine 시도
        result = self.hybrid_engine.solve_with_graph(problem_text)
        if result and "Error" not in result:
            return result
    except:
        # 실패 시 기존 Hierarchical로 폴백
        return self.decomposer.solve_hierarchically(...)
```

## 성능 비교 예측

| 특성 | 기존 (Hierarchical) | 새로운 (Graph-based) |
|------|-------------------|---------------------|
| 구조 명확성 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| LLM 이해도 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 메모리 효율 | ⭐⭐⭐ (최근 3개) | ⭐⭐⭐⭐⭐ (압축) |
| 긴 체인 처리 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 디버깅 | ⭐⭐ | ⭐⭐⭐⭐⭐ (그래프 시각화) |
| 타입 안정성 | ⭐⭐ | ⭐⭐⭐⭐⭐ (명시적) |

## 다음 단계

1. **테스트**: 복잡한 문제로 Hybrid Engine 검증
2. **최적화**: 
   - 압축 알고리즘 개선 (더 효율적인 요약)
   - Topological Sort 최적화 (병렬 실행 가능한 노드 탐지)
3. **확장**:
   - Majority Voting을 그래프 노드 단위로 적용
   - 각 노드에 verification layer 추가
4. **실제 Mamba 통합**: 
   - 현재는 Mamba "스타일"의 메모리 관리
   - 향후 실제 Mamba 모델 통합 가능

## 참고 자료

- [Mamba Paper](https://arxiv.org/abs/2312.00752) - Selective State Space Models
- [Transformer Paper](https://arxiv.org/abs/1706.03762) - Attention is All You Need
- [NuminaMath Strategy](https://github.com/project-numina/aimo-progress-prize) - Tool-Integrated Reasoning
- 현재 프로젝트: `MathCodeOrchestrator3_Project/src/pipeline/`

---

**작성일**: 2025-11-23  
**버전**: 1.0  
**상태**: 구현 완료, 테스트 대기
