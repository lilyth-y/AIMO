# AIMO 3 및 Math Corpus 전략: 뉴로-심볼릭 추론과 역공학적 데이터 생성의 통합 아키텍처 연구

## 1. 서론: 수학적 AI의 패러다임 전환과 AIMO 3의 과제

인공지능(AI)의 발달사에서 수학적 추론(Mathematical Reasoning)은 단순한 계산 능력을 넘어선 '일반 지능(General Intelligence)'의 핵심 척도로 간주되어 왔다. 특히 최근 거대 언어 모델(LLM)의 급격한 발전에도 불구하고, 복잡한 논리적 단계와 정밀한 계산이 요구되는 국제수학올림피아드(IMO) 수준의 문제는 여전히 난공불락의 영역으로 남아 있었다. 이러한 배경 속에서 개최되는 AI Mathematical Olympiad (AIMO) Progress Prize 3는 기존의 경진대회와는 질적으로 다른 기술적 도약을 요구한다. AIMO 1과 2가 상대적으로 제한적인 AIME(American Invitational Mathematics Examination) 수준의 문제에 집중했다면, AIMO 3는 IMO 수준의 킬러 문항을 포함하며, 모델의 추론 능력과 정답의 정확성을 극한으로 시험한다.

본 연구 보고서는 AIMO Progress Prize 3의 상위권 진입과 동시에 진행되는 Math Corpus Prize의 수상을 목표로 하는 통합적인 전략 및 시스템 아키텍처를 제안한다. 우리는 기존의 LLM 기반 접근법인 "문제만 보고 코드를 생성하는(Just Code)" 방식이 가진 한계를 분석하고, 이를 극복하기 위해 **"계획 후 실행(Plan & Code)"**이라는 새로운 철학을 제시한다. 이는 문제를 즉시 해결하려 들지 않고, 문제의 본질(시뮬레이션 가능 여부, 수론적 특징 등)을 먼저 파악하는 전략적 사고 단계를 시스템적으로 구현하는 것을 의미한다.

또한, 본 보고서는 Math Corpus Prize의 평가 기준인 데이터의 참신성(Novelty), 형식(Format), **성능(Performance)**을 충족시키기 위해, 기존의 데이터를 수집하는 방식이 아닌 정답으로부터 문제를 생성하는 역공학(Reverse Engineering) 기반의 데이터 생성 전략을 상세히 기술한다. 이는 DeepMind의 AlphaGeometry가 보여준 합성 데이터 생성의 성공 사례를 대수학 및 정수론 영역으로 확장한 것으로, 데이터 오염(Contamination) 위험을 원천적으로 배제하고 논리적 완결성이 보장된 고품질의 학습 데이터를 확보하는 유일한 길임을 입증할 것이다.

## 2. AIMO 3 경쟁 환경 및 제약 조건의 심층 분석

### 2.1 AIMO 3 규칙의 변화와 그 함의

AIMO 3는 이전 대회들과 비교하여 몇 가지 결정적인 규칙 변경을 도입하였으며, 이는 참가자들에게 단순한 모델 튜닝을 넘어선 시스템적 혁신을 요구한다.

**표 1: AIMO 2와 AIMO 3의 주요 규칙 비교 및 기술적 함의**

| 구분 | AIMO 2 (이전) | AIMO 3 (현재) | 기술적 함의 |
| :--- | :--- | :--- | :--- |
| **문제 난이도** | AIME / 국가 올림피아드 수준 | IMO (국제 올림피아드) 수준 포함 | 단순 패턴 매칭 불가능. 심층적인 다단계 추론 및 창의적 발상 필요. |
| **정답 형식** | 3자리 정수 (0-999) | 5자리 정수 (0-99999) | 확률적 추측(Guessing)의 효용성 소멸. 정확한 연산 및 검증 로직 필수. |
| **하드웨어** | T4 GPU x 2 | L4 GPU x 4 또는 H100 | 더 큰 모델(32B 이상) 및 고성능 추론(Batch Processing) 가능. |
| **데이터 제약** | 외부 데이터 허용 | 공개 데이터셋(Math Corpus) 제출 권장 | 모델 성능뿐만 아니라 데이터 파이프라인의 우수성이 경쟁력의 핵심. |

#### 2.1.1 5자리 정수 제약과 추측 방지 메커니즘

가장 주목할 만한 변화는 정답의 범위가 0에서 99,999로 확장되었다는 점이다. AIMO 2에서는 0-999 범위의 답이 요구되었기에, 일부 팀들은 문제의 맥락만으로 답을 좁히거나, 빈도수가 높은 답(예: 0, 1, 2)을 찍는 전략으로 점수를 얻을 수 있었다. 그러나 100,000개의 가능성을 가진 5자리 정수 포맷은 이러한 "운에 기댄(Luck-based)" 접근을 통계적으로 무력화시킨다. 주최 측은 $10^5$의 검색 공간이 LLM이 산술 연산을 수행할 수 있는지 확인하면서도 무작위 추측이 통하지 않는 균형점이라고 명시했다. 이는 우리의 시스템이 최종 단계에서 **강력한 검증 라우터(Verification Router)**를 통해 답의 무결성을 확인해야 함을 시사한다.

#### 2.1.2 IMO 수준의 킬러 문항과 계산 복잡도

IMO 수준의 문제는 단순히 계산이 복잡한 것이 아니라, 발상의 전환을 요구한다. 예를 들어, $3^{2025!}$과 같은 거대 수의 특정 자릿수를 구하는 문제는 Python의 기본 `pow()` 함수로 단순히 계산하려 하면 시간 초과(Time Limit Exceeded)나 메모리 초과(Memory Overflow)가 발생한다. 이는 오일러 정리(Euler's Theorem)나 중국인의 나머지 정리(Chinese Remainder Theorem)와 같은 수론적 도구를 사용해야만 해결 가능하다. 따라서 모델은 단순히 코드를 짜는 것(Just Code)을 넘어, 이 문제가 **"시뮬레이션 가능한가, 아니면 이론적 접근이 필요한가?"**를 판단하는 메타인지 능력을 갖춰야 한다.

### 2.2 하드웨어 환경의 진화: H100과 L4의 활용 전략

AIMO 3는 참가자들에게 NVIDIA H100 또는 L4 GPU를 제공한다. 이는 기존 T4 GPU 대비 연산 능력이 비약적으로 향상된 것으로, 다음과 같은 전략적 선택을 가능하게 한다.

*   **모델 크기의 확장:** T4 환경에서는 7B 모델을 겨우 구동하거나 양자화(Quantization)가 필수적이었으나, H100 환경에서는 32B 또는 70B 모델을 4-bit 또는 8-bit 양자화 상태로 로드하여 더 깊은 추론 능력을 활용할 수 있다. 특히 최근 공개된 Qwen-2.5-32B나 DeepSeek-R1-Distill 모델은 코딩 및 수학 성능에서 획기적인 향상을 보여주었으며, 이를 온전히 활용하는 것이 승부처가 될 것이다.
*   **테스트 타임 컴퓨팅(Test-Time Compute)의 증대:** GPU 메모리의 여유는 추론 시 더 많은 샘플을 생성하고(Self-Consistency), 더 복잡한 탐색 알고리즘(Tree of Thoughts)을 실행할 수 있음을 의미한다. 5시간의 런타임 제약 내에서 H100의 빠른 처리 속도를 활용해 수천 개의 후보 해를 생성하고 검증하는 대규모 병렬 처리 전략이 유효할 것이다.

## 3. 선행 연구 및 경쟁작 심층 분석: AIMO 2 승자들의 교훈

AIMO 3 전략을 수립하기 위해서는 AIMO 1과 2의 우승 솔루션, 특히 NuminaMath와 NVIDIA의 NemoSkills 팀의 접근 방식을 철저히 분석하고, 그들의 한계를 넘어서는 혁신이 필요하다.

### 3.1 NuminaMath: 도구 통합 추론(TIR)의 정립

AIMO 1의 우승팀인 Project Numina는 **도구 통합 추론(Tool-Integrated Reasoning, TIR)**이라는 개념을 대중화했다. 그들의 핵심 전략은 LLM이 자연어(CoT)와 Python 코드를 번갈아 가며 생성하는 것이었다.

*   **성공 요인:** NuminaMath-7B 모델은 DeepSeekMath-Base를 기반으로 하여, 수학 문제를 작은 단계로 분해하고 각 단계를 Python 코드로 실행하여 결과를 얻은 뒤 다시 추론을 이어가는 방식을 취했다. 이는 LLM의 고질적인 약점인 '산술 연산 오류'를 Python 인터프리터에 위임함으로써 해결했다.
*   **한계점:** AIMO 2의 상위권 경쟁에서 드러난 Numina 방식의 한계는 "코드 의존성"이었다. 모든 문제를 코드로 풀려고 시도하다 보니, 코드로 구현하기 난해한 기하학적 증명이나, 효율적인 알고리즘이 필요한 조합론 문제에서 모델이 비효율적인 브루트 포스(Brute-force) 코드를 작성하다 타임아웃에 걸리는 경우가 빈번했다.

### 3.2 NVIDIA NemoSkills: 생성적 해답 선택(GenSelect)

AIMO 2의 우승팀인 NVIDIA NemoSkills는 OpenMathReasoning 데이터셋을 구축하고 Generative Solution Selection (GenSelect) 기술을 도입했다.

*   **데이터의 규모:** 그들은 540k개의 고품질 문제와 3.2M개의 CoT 솔루션, 1.7M개의 TIR 솔루션을 포함하는 방대한 데이터셋을 구축했다. 이는 데이터의 양이 모델의 추론 성능과 직결됨을 보여주었다.
*   **GenSelect:** 단순히 다수결(Majority Voting)로 답을 선택하는 것을 넘어, 모델이 생성된 여러 솔루션(CoT, TIR 등)을 읽고 "어떤 솔루션이 가장 논리적으로 타당한가?"를 판단하는 별도의 검증 모델(Verifier)을 학습시켰다. 이는 정답률을 획기적으로 높이는 결과를 가져왔다.
*   **교훈:** AIMO 3에서는 단순한 생성 능력뿐만 아니라, 자신의 생성을 평가하고 선별하는 능력이 필수적이다. 우리는 이를 **"Verification Router"**라는 명시적 모듈로 시스템화할 것이다.

### 3.3 AlphaGeometry: 뉴로-심볼릭의 가능성

DeepMind의 AlphaGeometry는 순수 기하학 문제에서 IMO 금메달리스트 수준의 성능을 보여주었다.

*   **핵심 메커니즘:** AlphaGeometry는 언어 모델이 직관적인 보조선(Auxiliary Construction)을 제안하고, 심볼릭 엔진(Symbolic Engine)이 엄밀한 논리적 증명을 수행하는 뉴로-심볼릭(Neuro-Symbolic) 구조를 취했다.
*   **데이터 생성:** 가장 중요한 점은 1억 개의 합성 데이터(Synthetic Data)를 생성한 방식이다. 그들은 무작위로 기하학적 다이어그램을 생성하고, 그 안에서 성립하는 정리를 역으로 추출하는 "Traceback" 방식을 사용했다.
*   **AIMO 3 적용:** 우리는 이 "Traceback" 방식을 기하학뿐만 아니라 대수학과 정수론으로 확장하여, Math Corpus Prize를 위한 **"역공학 데이터 생성 엔진"**을 구축할 것이다.

## 4. 핵심 철학: "Just Code"에서 "Plan & Code"로의 진화

기존의 LLM 기반 수학 문제 해결 방식은 대부분 "문제를 입력받으면 즉시 코드를 작성하여 답을 구한다"는 선형적 프로세스에 의존해왔다. 그러나 IMO 수준의 문제에서는 이러한 접근이 필연적으로 실패한다. 우리는 이를 극복하기 위해 **"Plan & Code"**라는 새로운 패러다임을 제안한다.

### 4.1 전략적 사고(Strategic Analysis) 단계의 도입

문제를 해결하기 전, 시스템은 반드시 전략적 사고(Step 2) 단계를 거쳐야 한다. 이 단계에서는 코드를 생성하지 않고, 문제의 유형(Type), 규모(Scale), **복잡도(Complexity)**를 분석한다.

*   **질문:** "이 문제는 $N$이 작아서($N < 10^6$) 시뮬레이션으로 풀 수 있는가? 아니면 $N$이 너무 커서($N > 10^{18}$) 수식적 유도(Derivation)가 필요한가?"
*   **질문:** "이 문제는 기하학적 라이브러리(shapely)가 필요한가, 아니면 좌표계 설정 없이 유클리드 기하학 공리(sympy.geometry)로 풀어야 하는가?"

이러한 메타인지적 판단은 **계산 라우터(Calculation Router)**에 의해 수행되며, 이는 전체 시스템의 효율성을 결정짓는 뇌 역할을 한다.

### 4.2 확률적 접근(Probabilistic Approach)과 다중 경로 탐색

단 하나의 해결 방법만을 고집하는 결정론적(Deterministic) 방식은 위험하다. 우리의 시스템은 확률적 접근을 취한다.

*   동일한 문제에 대해 시뮬레이션(Simulation) 경로와 수학적 증명(Symbolic) 경로를 동시에 고려한다.
*   각 경로의 성공 확률을 예측하고, 자원이 허락하는 한 두 경로를 모두 실행하여 결과를 교차 검증(Cross-Verification)한다.
*   예를 들어, 조합론 문제에서 $N=5$일 때의 답을 시뮬레이션으로 구하고, 이를 바탕으로 유도된 일반항 공식이 $N=100$일 때도 성립하는지 검증하는 식이다.

## 5. 시스템 아키텍처: 5-Stage Deep Reasoning Pipeline

우리는 인간 수학자의 사고 과정을 모방하여 설계된 **5단계 심층 추론 파이프라인(5-Stage Deep Reasoning Pipeline)**을 제안한다. 이 파이프라인은 각 단계가 모듈화되어 있으며, 단계별로 검증과 피드백 루프가 존재하여 오류를 조기에 차단한다.

### Stage 1: Labeling & Semantic Decomposition (분류 및 의미론적 분해)

입력된 LaTeX 형식의 문제를 분석하여 핵심 요소를 추출하고 분류하는 단계이다.

*   **Domain Classifier:** 문제는 정수론(Number Theory), 기하학(Geometry), 대수학(Algebra), 조합론(Combinatorics), 또는 복합 유형인지를 분류한다. 이를 위해 BERT 기반의 경량화된 분류기 또는 LLM의 퓨샷(Few-shot) 프롬프팅을 사용한다.
*   **Variable Extraction:** 문제에 등장하는 변수($N, K, P$ 등)와 그 제약 조건($1 \le N \le 10^9$)을 JSON 형태로 추출한다. 이는 이후 단계에서 라우팅 결정을 내리는 데 중요한 근거가 된다.

### Stage 2: Domain Experts Retrieval (전문가 모듈 호출)

"모든 것을 다 아는 하나의 모델" 대신, 특정 영역에 특화된 지식과 도구를 로드하는 단계이다.

*   **Dynamic Context Loading:** Stage 1의 분류 결과에 따라, 해당 도메인에 특화된 시스템 프롬프트와 Python 라이브러리 컨텍스트를 로드한다.
    *   **Geometry:** `shapely`, `sympy.geometry` 라이브러리 예제 로드. 좌표 변환(Coordinate Bash) 기법에 대한 프롬프트 주입.
    *   **Number Theory:** `sympy.ntheory` (소인수분해, 오일러 피 함수 등) 및 모듈러 연산 예제 로드.
    *   **Combinatorics:** `itertools`, `scipy.special` (조합, 순열) 및 동적 계획법(DP) 템플릿 로드.
*   **Rationale:** 문맥 윈도우(Context Window)의 효율성을 높이고, 모델이 불필요한 도구에 주의를 뺏기는 것을 방지한다.

### Stage 3: The Calculation Router (계산 라우터 - 핵심 엔진)

본 아키텍처의 가장 독창적인 부분으로, 문제 해결의 전략을 결정한다. 라우터는 문제의 파라미터(특히 $N$의 크기)와 유형을 기반으로 다음 세 가지 경로 중 하나 이상을 선택한다.

#### 3.1 Path A: The Simulator (Python Loop)
*   **Trigger:** $N$이 작거나(예: $N < 10^7$), 규칙이 불규칙하여 수식화하기 어려운 경우 (예: "복잡한 조건의 그리드 이동").
*   **Action:** Python의 반복문(Loop)이나 재귀(Recursion)를 사용하여 상태 공간을 직접 탐색하는 코드를 생성한다.
*   **장점:** 복잡한 논리적 함정이 있어도 시뮬레이션은 정확한 결과를 보장한다.

#### 3.2 Path B: The Theoretician (SymPy/Math)
*   **Trigger:** $N$이 매우 크거나(예: $N=2025!$, $10^{100}$), 연속적인 기하학적 확률 문제, 무한 급수 등.
*   **Action:** SymPy와 같은 심볼릭 라이브러리를 사용하여 수식을 정의하고, `simplify`, `expand`, `solve` 등의 함수를 통해 대수적으로 해를 구한다.
*   **핵심:** 절대 직접 계산하지 않고, 라이브러리의 추상화된 기능을 호출한다. (예: `pow(3, N, mod)` 사용)

#### 3.3 Path C: The Hybrid (Decomposition)
*   **Trigger:** 부분적으로는 계산이 가능하지만 전체적으로는 이론이 필요한 경우.
*   **Action:** 문제를 하위 문제로 쪼갠다. 예를 들어, 작은 $N$에 대해 시뮬레이션을 돌려 패턴(수열)을 찾고(OEIS 스타일), 그 패턴을 바탕으로 일반항을 추론하여 큰 $N$을 해결한다.

### Stage 4: Execution & Error Correction (실행 및 자가 수정)

선택된 경로에 따라 코드를 생성하고, Kaggle의 샌드박스 환경에서 실행한다.

*   **Iterative Refinement:** 실행 중 `TimeoutError`나 `OverflowError`가 발생하면, 에러 메시지를 모델에 피드백하여 전략을 수정한다.
    *   **Scenario:** 시뮬레이션 경로로 진입했으나 타임아웃 발생 $\rightarrow$ 모델은 " $N$이 너무 커서 시뮬레이션이 불가능합니다. 수식적 접근으로 전환합니다."라고 판단하고 Path B로 전환한다.
*   **Sandboxing:** 외부 인터넷 접근이 차단된 환경이므로, 사전에 허용된 라이브러리(NumPy, Pandas, SymPy, SciPy 등)만 사용하도록 엄격히 제한한다.

### Stage 5: The Verification Router (검증 라우터 - 최종 관문)

답안 제출 전, 환각(Hallucination)을 방지하기 위한 최후의 방어선이다.

*   **Scale-Down Test:** 문제의 $N$을 매우 작은 값(예: $N=1, 2, 3$)으로 변경하여 시뮬레이션을 돌리고, 이론적 해가 이 작은 값들에 대해서도 성립하는지 검증한다.
*   **Reverse Check (역산):** 구해진 답 $X$를 문제의 조건에 대입하여 모순이 없는지 확인한다. 예를 들어 방정식의 해라면, 대입했을 때 0이 되는지 확인한다.
*   **Format Compliance:** 최종 답안이 0-99999 사이의 정수인지 확인하고, 범위를 벗어날 경우 모듈러 연산이나 포맷팅을 강제 적용한다.

## 6. 데이터 생성 전략: "Reverse Engineering" (역공학) 엔진

Math Corpus Prize($30,000) 수상과 모델 성능 향상을 위해, 우리는 기존 데이터를 수집하는 것이 아니라 "정답으로부터 문제를 생성하는" 역방향 생성 전략을 채택한다. 이는 데이터의 **참신성(Novelty)**과 **무결성(Integrity)**을 100% 보장한다.

### 6.1 역방향 생성의 원리 (Backward Problem Generation)

일반적인 LLM 학습 데이터 생성은 "문제를 주고 풀어라"는 방식이지만, 이는 LLM이 잘못된 풀이를 생성할 위험이 있다. 반면, 역방향 생성은 다음과 같이 진행된다.

1.  **정답(Target Answer) 설정:** 임의의 5자리 정수 $A$를 선택한다.
2.  **수학적 구조(Core Structure) 생성:** 정답 $A$가 도출될 수밖에 없는 수학적 구조(방정식, 수열, 기하학적 배치)를 무작위 파라미터로 생성한다.
3.  **문제화(Problemification):** 생성된 구조를 자연어 문제로 변환하고, 정보의 일부를 숨겨(Masking) 난이도를 조절한다.
4.  **검증:** 생성된 문제를 다시 풀어보아 정답이 유일한지 확인한다.

### 6.2 도메인별 생성 알고리즘

#### 6.2.1 Domain A: 합성 정수론 (Diophantine Construction)
*   **목표:** 선형 디오판토스 방정식 $ax + by = c$ 형태의 문제를 생성하되, 해가 유일하거나 특정 조건을 만족하도록 한다.
*   **알고리즘:**
    1.  목표 해 $x_0, y_0$를 랜덤 생성.
    2.  서로소인 계수 $a, b$를 생성.
    3.  $c = ax_0 + by_0$ 계산.
    4.  **Traceback:** "147원짜리 사과와 258원짜리 배를 합쳐서 369원을 만들 때..."와 같은 문장제(Word Problem)로 변환하거나, "$147x \equiv 369 \pmod{258}$" 형태의 합동식 문제로 변환.
    5.  `sympy.solvers.diophantine`을 사용하여 해의 유일성 검증.

#### 6.2.2 Domain B: 합성 다항식 (Polynomial Root Obfuscation)
*   **목표:** 정수근을 가지는 고차 다항식 문제를 생성.
*   **알고리즘:**
    1.  정수근 $r_1, r_2, r_3$ 선택.
    2.  다항식 $P(x) = (x-r_1)(x-r_2)(x-r_3)$ 구성 및 전개하여 $ax^3 + bx^2 + cx + d = 0$ 형태의 계수 도출.
    3.  **Obfuscation:** 변수 치환(예: $t = x^2$)을 적용하거나, "세 근의 합과 곱의 관계"를 묻는 근과 계수의 관계 문제로 변형.
    4.  Python `hypothesis` 라이브러리를 사용하여 다양한 입력값에 대해 다항식의 성질이 유지되는지 테스트.

#### 6.2.3 Domain C: 기하학적 "Traceback" (Geometric Construction)
*   **목표:** AlphaGeometry의 방식을 차용하여 좌표 기반의 기하 문제 생성.
*   **알고리즘:**
    1.  좌표평면 위에 정수 좌표를 갖는 점 $A, B, C$를 무작위 배치.
    2.  거리, 넓이, 무게중심, 외심 등의 속성을 계산 (Ground Truth).
    3.  **Task Generation:** "세 변의 길이가 각각 $L_1, L_2, L_3$인 삼각형의 넓이를 구하시오"와 같이 좌표를 숨기고 속성값만 제시.
    4.  **Novelty:** 좌표가 무작위로 생성되므로, 기존 교과서나 인터넷에 존재하지 않는 완전히 새로운 문제(Unique Geometry)가 됨.

### 6.3 Schema v4.0: "사고의 지도"를 담은 데이터셋

Math Corpus Prize의 "Format" 점수를 극대화하기 위해, 단순한 (질문, 정답) 쌍이 아닌, 문제 해결의 전 과정을 담은 고밀도 스키마를 정의한다.

**표 2: Open-Reverse-Math 데이터셋 스키마 (v4.0)**

| 필드명 (Field) | 설명 (Description) | 생성 방법 (Source) |
| :--- | :--- | :--- |
| `problem_id` | 고유 식별자 (UUID) | System Generation |
| `topic_tag` | 세부 주제 (예: "Modular Arithmetic") | Generator Metadata |
| `difficulty_level` | 1-10 난이도 척도 | 내부 표현(Internal Rep.) 기반 예측 |
| `problem_text` | LaTeX 포맷의 문제 텍스트 | LLM Rewriting of Symbolic Core |
| `strategic_analysis` | **핵심:** 문제를 풀기 전의 전략 분석 (도구 선택, $N$ 크기 분석 등) | Teacher Model (DeepSeek-R1) Inference |
| `reasoning_trace` | 텍스트 사고 과정과 Python 코드가 혼합된 CoT | 생성 당시의 Traceback 로직 역서술 |
| `python_code` | 정답을 도출하는 실행 가능한 Python 코드 | SymPy/Simulator 기반 생성 |
| `verification_logic` | 답을 검증하는 별도의 코드 (PBT) | 역산 로직 (Inverse Check) |
| `final_answer` | 0-99999 사이의 정수 | Generation Seed (Ground Truth) |

이 스키마는 모델이 단순히 답을 맞히는 것이 아니라, `strategic_analysis`를 통해 계획을 세우고, `verification_logic`을 통해 검토하는 "메타인지"를 학습할 수 있도록 설계되었다.

## 7. 구현 기술 및 엔지니어링 스택

### 7.1 모델 선정 및 최적화

*   **Base Model:** 우리는 Qwen-2.5-32B-Instruct 또는 DeepSeek-R1-Distill-Llama-70B를 주 모델로 선정한다. 이들은 코딩 능력(HumanEval)과 수학 능력(MATH)에서 탁월한 성능을 보이며, 4-bit 양자화(AWQ/GPTQ) 적용 시 H100 또는 4xL4 환경 메모리에 적재 가능하다.
*   **Inference Engine:** vLLM을 사용하여 추론 속도를 극대화한다. vLLM의 PagedAttention 기술은 긴 문맥(Long Context) 처리 시 메모리 효율을 높여주며, 이는 다단계 추론(CoT) 과정에서 필수적이다.

### 7.2 Python 샌드박스 및 라이브러리 관리

*   **Security:** Kaggle 환경은 인터넷이 차단되므로, 필요한 모든 라이브러리(`sympy`, `scipy`, `numpy`, `networkx`, `hypothesis`)를 사전에 휠(Wheel) 파일로 다운로드하여 데이터셋 형태로 업로드 및 설치한다.
*   **Timeout Guard:** 무한 루프를 방지하기 위해 모든 사용자 코드 실행에는 `signal.alarm` 또는 `multiprocessing`을 이용한 타임아웃 래퍼(Wrapper)를 적용한다. 이는 대회 제한 시간(5시간) 내에 최대한 많은 문제를 풀기 위한 필수 안전장치이다.

### 7.3 검증 라우터의 PBT(Property-Based Testing) 구현

우리는 Python의 `hypothesis` 라이브러리를 활용하여 수학적 가설을 검증한다.

*   **적용 예시:** 모델이 "임의의 정수 $n$에 대해 $n^3 - n$은 6의 배수이다"라는 정리를 증명하려 할 때, `hypothesis`를 통해 수천 개의 $n$을 무작위로 생성하여 `n^3 - n % 6 == 0` 조건을 고속으로 테스트한다.
*   **이점:** 이는 복잡한 정리 증명기(Coq, Lean)를 사용하는 것보다 훨씬 가볍고 빠르며, AIMO 대회의 제한된 컴퓨팅 자원 내에서 실용적인 검증력을 제공한다.

## 8. 결론 및 기대 효과

본 보고서에서 제안한 AIMO 3 & Math Corpus 통합 전략은 기존의 확률적 생성 모델이 가진 한계를 시스템적 아키텍처와 데이터 공학으로 극복하려는 시도이다.

*   **경쟁 우위:** 5-Stage Pipeline은 "Calculation Router"를 통해 계산 복잡도에 따른 최적의 풀이 경로(Simulation vs Theory)를 선택함으로써, IMO 수준의 킬러 문항에 대응한다. 이는 AIMO 2 우승팀들의 전략을 계승하면서도, "Plan & Code"라는 상위 레벨의 인지 과정을 추가하여 견고함을 더했다.
*   **데이터 가치:** "역공학(Reverse Engineering)" 기반의 데이터 생성 전략은 Math Corpus Prize의 핵심 평가 기준인 참신성과 무결성을 완벽하게 충족한다. 우리는 오염되지 않은 500,000개의 고품질 데이터를 생성하여 공개함으로써, 커뮤니티에 기여하고 데이터셋 상을 확보할 것이다.
*   **안전망:** 검증 라우터(Verification Router)와 PBT 기반의 안전장치는 5자리 정수 정답 형식에서 발생할 수 있는 환각 오류를 최소화하여, 리더보드에서의 점수 안정성을 보장한다.

결론적으로, 본 전략은 단순한 코딩 대회를 넘어, "스스로 문제를 분석하고, 도구를 선택하며, 결과를 검증하는" 차세대 수학적 AI 에이전트의 청사진을 제시한다. 이는 AIMO 3에서의 우승뿐만 아니라, 향후 수학적 추론 모델 연구의 중요한 이정표가 될 것이다.

## 부록: 주요 기술 용어 정의

*   **TIR (Tool-Integrated Reasoning):** 자연어 추론 과정에 Python 코드 실행이나 계산기 등의 도구 사용을 통합하는 기법.
*   **CoT (Chain of Thought):** 문제를 해결하기 위해 일련의 중간 추론 단계를 생성하는 프롬프팅 기법.
*   **PBT (Property-Based Testing):** 특정 입력값 대신, 입력값이 가져야 할 속성(Property)을 정의하고 무작위 데이터를 대량으로 생성하여 코드를 테스트하는 기법.
*   **GenSelect (Generative Solution Selection):** 여러 개의 후보 해를 생성한 후, 이를 평가하는 모델을 통해 가장 우수한 해를 선택하는 기법.
*   **Reverse Engineering (in Math Data):** 정답과 수학적 구조를 먼저 정의하고, 이를 바탕으로 문제를 역으로 생성하는 합성 데이터 구축 방식.
