# AIMO 3 개발 계획 및 LLM 한계 분석 보고서

## 1. 심층 분석: 왜 기존 LLM은 IMO 수준의 문제를 풀지 못했는가?

국제수학올림피아드(IMO) 수준의 문제는 단순한 지식 검색이나 패턴 매칭으로는 해결할 수 없습니다. 기존 LLM(GPT-4, Claude 3 등)이 실패한 근본적인 원인은 다음과 같습니다.

### 1.1 확률적 생성의 한계 (Probabilistic vs. Deterministic)
*   **원인:** LLM은 "다음 토큰을 예측"하는 확률적 모델입니다. $2025 \times 2024$를 계산할 때, 실제 연산을 수행하는 것이 아니라 학습 데이터에서 가장 그럴듯한 숫자를 내뱉습니다.
*   **결과:** 복잡한 산술 연산이나 논리 전개 과정에서 단 하나의 토큰만 틀려도 전체 증명이 무너지는 "Snowball Effect"가 발생합니다. IMO 문제는 100%의 논리적 엄밀함을 요구하므로, 99%의 정확도를 가진 모델도 0점 처리됩니다.

### 1.2 "계획 부재"와 선형적 사고 (Lack of Planning)
*   **원인:** 기존 모델은 문제를 읽자마자 답을 쓰기 시작합니다(Left-to-Right Generation).
*   **결과:** IMO 문제는 "보조선 긋기"나 "귀류법 가정"처럼, 답을 쓰기 전에 전체적인 전략(Global Plan)을 세워야 합니다. 막다른 길에 다다랐을 때 되돌아가는(Backtracking) 능력이 부족하여, 잘못된 접근법을 끝까지 고집하다 실패합니다.

### 1.3 데이터의 질적 차이 (Data Gap)
*   **원인:** 대부분의 학습 데이터(GSM8K, MATH)는 AIME 수준 이하의 정형화된 문제입니다.
*   **결과:** IMO 수준의 "창의적 발상"이나 "새로운 정의(New Definition)"를 요구하는 문제에 대한 학습 데이터가 전무합니다. 모델은 본 적 없는 유형의 문제 앞에서 환각(Hallucination)을 일으킵니다.

### 1.4 검증 능력의 부재 (Lack of Verification)
*   **원인:** 모델은 자신이 생성한 답이 맞는지 틀린지 스스로 판단하지 못합니다.
*   **결과:** 엉터리 논리로 그럴듯한 오답을 내놓고도 확신을 가집니다. (Self-Confidence Illusion)

---

## 2. 기술 검토: 수학 연산자의 파라미터화 (Parameterizing Operators)

**질문:** "지금 파라미터로 수학 연산자 처리가 가능한가?"

**답변:** **네, 가능합니다.** 그리고 이것이 우리 "역공학(Reverse Engineering)" 전략의 핵심입니다.

### 2.1 구현 원리
Python은 함수형 프로그래밍을 지원하므로, 연산자(Operator) 자체를 변수처럼 취급할 수 있습니다.

1.  **Python `operator` 모듈:** `+`, `-`, `*`, `/` 등을 함수 객체로 다룰 수 있습니다.
2.  **SymPy Expression Tree:** 수식을 트리 구조로 다루며, 노드(Node)의 연산자를 프로그래밍 방식으로 교체할 수 있습니다.
3.  **Custom Operators:** $a \oplus b = a^2 + b - ab$ 와 같은 새로운 연산자를 정의하고 이를 파라미터로 넘길 수 있습니다.

### 2.2 활용 예시 (데이터 생성 시)
우리는 정답 $X=42$를 고정해두고, 연산자를 무작위로 선택하여 문제를 생성할 수 있습니다.

```python
import operator
import random

# 연산자 풀(Pool) 정의
ops = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    'custom_op': lambda a, b: a**2 + b  # 사용자 정의 연산
}

# 랜덤하게 연산자 선택하여 문제 생성
selected_op_name = random.choice(list(ops.keys()))
selected_op_func = ops[selected_op_name]

# 문제: 3 [OP] 5 = ?
result = selected_op_func(3, 5)
print(f"문제: 3 {selected_op_name} 5 = {result}")
```

이 방식을 통해 **"구조는 같지만 연산자가 다른"** 수만 가지의 변형 문제를 생성하여 모델의 일반화 능력을 극대화할 수 있습니다.

---

## 3. 순차적 개발 계획 (Sequential Development Plan)

위 분석을 바탕으로, 리스크를 최소화하고 성공 확률을 높이는 단계별 개발 계획을 수립했습니다.

### Phase 1: 핵심 엔진 고도화 (Core Engine Refinement) - [현재 우선순위]
가장 큰 리스크인 "추론 실패"를 막기 위한 안전장치를 먼저 만듭니다.
1.  **Fallback Logic 구현 (Stage 3):** 시뮬레이션 실패 시 이론적 접근으로, 이론 실패 시 브루트 포스로 전환하는 로직 구현.
2.  **Verification Router 구현 (Stage 5):** 5자리 정수 포맷 검증 및 역산(Reverse Check) 모듈 구현.
3.  **기본 Docker 환경 구성:** Windows/Linux 호환성 확보를 위한 베이스 이미지 생성.

### Phase 2: 데이터 파이프라인 구축 (Data Pipeline)
모델을 학습시키고 검증할 "연료"를 준비합니다.
1.  **역공학 생성기 (Reverse Engineering Generator) 개발:**
    *   정수론(Number Theory) 모듈: 디오판토스 방정식 생성기.
    *   대수학(Algebra) 모듈: 다항식 및 수열 문제 생성기.
    *   **연산자 파라미터화 적용:** 다양한 연산자를 조합하는 로직 추가.
2.  **SQLite Bulk Load 구현:** CSV/JSONL 대량 적재 스크립트 작성.

### Phase 3: 통합 및 최적화 (Integration & Optimization)
실전 대회 환경에 맞게 시스템을 튜닝합니다.
1.  **Time Budgeting 알고리즘:** 난이도에 따른 시간 배분 로직.
2.  **Kaggle 환경 시뮬레이션:** 오프라인 인터넷 차단 환경에서의 라이브러리 로딩 테스트.
3.  **최종 리허설:** AIMO 2 기출문제를 대상으로 전체 파이프라인 벤치마크.

---

## 4. 결론

기존 LLM의 실패는 **"계획 없는 생성"**과 **"검증 없는 확신"** 때문이었습니다.
우리의 **"Plan & Code"** 전략은 이를 구조적으로 해결하며, **"연산자 파라미터화"**를 통한 데이터 생성은 모델에게 전례 없는 다양한 훈련 데이터를 제공할 것입니다.

**다음 행동:** Phase 1의 첫 번째 과제인 **"Fallback Logic 구현"**을 시작하는 것을 추천합니다.
