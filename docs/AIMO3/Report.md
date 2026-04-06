## 운영 동기화 메모

이 문서는 아키텍처/연구 보고서 성격입니다. Vertex 운영 절차와 최신 스크립트 동작은 아래 문서를 기준으로 동기화합니다.

- `docs/VERTEX_SCRIPTS_EVALUATION.md`
- `docs/vertex/VERTEX_DOC_SYNC_CHECKLIST.md`
- `docs/run-eval/REQUIREMENTS_SELECTION_GUIDE.md`

---

## **시스템 아키텍처: 5-Stage Deep Reasoning Pipeline**

우리는 인간 수학자의 사고 과정을 모방하여 설계된 **5단계 심층 추론 파이프라인(5-Stage Deep Reasoning Pipeline)**을 제안한다. 이 파이프라인은 각 단계가 모듈화되어 있으며, 단계별로 검증과 피드백 루프가 존재하여 오류를 조기에 차단한다.

### **Stage 1: Labeling & Semantic Decomposition (분류 및 의미론적 분해)**

입력된 LaTeX 형식의 문제를 분석하여 핵심 요소를 추출하고 분류하는 단계이다.

- **Domain Classifier:** 문제는 정수론(Number Theory), 기하학(Geometry), 대수학(Algebra), 조합론(Combinatorics), 또는 복합 유형인지를 분류한다. 이를 위해 BERT 기반의 경량화된 분류기 또는 LLM의 퓨샷(Few-shot) 프롬프팅을 사용한다.
- **Variable Extraction:** 문제에 등장하는 변수(*N*,*K*,*P* 등)와 그 제약 조건(1≤*N*≤109)을 JSON 형태로 추출한다. 이는 이후 단계에서 라우팅 결정을 내리는 데 중요한 근거가 된다.
    
    N,K,P
    
    1≤N≤109
    

### **Stage 2: Domain Experts Retrieval (전문가 모듈 호출)**

"모든 것을 다 아는 하나의 모델" 대신, 특정 영역에 특화된 지식과 도구를 로드하는 단계이다.

- **Dynamic Context Loading:** Stage 1의 분류 결과에 따라, 해당 도메인에 특화된 시스템 프롬프트와 Python 라이브러리 컨텍스트를 로드한다.
    - **Geometry:** `shapely`, `sympy.geometry` 라이브러리 예제 로드. 좌표 변환(Coordinate Bash) 기법에 대한 프롬프트 주입.
    - **Number Theory:** `sympy.ntheory` (소인수분해, 오일러 피 함수 등) 및 모듈러 연산 예제 로드.
    - **Combinatorics:** `itertools`, `scipy.special` (조합, 순열) 및 동적 계획법(DP) 템플릿 로드.
- **Rationale:** 문맥 윈도우(Context Window)의 효율성을 높이고, 모델이 불필요한 도구에 주의를 뺏기는 것을 방지한다.

### **Stage 3: The Calculation Router (계산 라우터 - 핵심 엔진)**

본 아키텍처의 가장 독창적인 부분으로, 문제 해결의 전략을 결정한다. 라우터는 문제의 파라미터(특히 N*N*의 크기)와 유형을 기반으로 다음 세 가지 경로 중 하나 이상을 선택한다.

### **3.1 Path A: The Simulator (Python Loop)**

- **Trigger:** *N*이 작거나(예: *N*<107), 규칙이 불규칙하여 수식화하기 어려운 경우 (예: "복잡한 조건의 그리드 이동").
    
    N
    
    N<107
    
- **Action:** Python의 반복문(Loop)이나 재귀(Recursion)를 사용하여 상태 공간을 직접 탐색하는 코드를 생성한다.
- **장점:** 복잡한 논리적 함정이 있어도 시뮬레이션은 정확한 결과를 보장한다.

### **3.2 Path B: The Theoretician (SymPy/Math)**

- **Trigger:** *N*이 매우 크거나(예: *N*=2025!, 10100), 연속적인 기하학적 확률 문제, 무한 급수 등.
    
    N
    
    N=2025!
    
    10100
    
- **Action:** SymPy와 같은 심볼릭 라이브러리를 사용하여 수식을 정의하고, `simplify`, `expand`, `solve` 등의 함수를 통해 대수적으로 해를 구한다.
- **핵심:** 절대 직접 계산하지 않고, 라이브러리의 추상화된 기능을 호출한다. (예: `pow(3, N, mod)` 사용)

### **3.3 Path C: The Hybrid (Decomposition)**

- **Trigger:** 부분적으로는 계산이 가능하지만 전체적으로는 이론이 필요한 경우.
- **Action:** 문제를 하위 문제로 쪼갠다. 예를 들어, 작은 *N*에 대해 시뮬레이션을 돌려 패턴(수열)을 찾고(OEIS 스타일), 그 패턴을 바탕으로 일반항을 추론하여 큰 *N*을 해결한다.
    
    N
    
    N
    

### **Stage 4: Execution & Error Correction (실행 및 자가 수정)**

선택된 경로에 따라 코드를 생성하고, Kaggle의 샌드박스 환경에서 실행한다.

- **Iterative Refinement:** 실행 중 `TimeoutError`나 `OverflowError`가 발생하면, 에러 메시지를 모델에 피드백하여 전략을 수정한다.
    - **Scenario:** 시뮬레이션 경로로 진입했으나 타임아웃 발생 → 모델은 " *N*이 너무 커서 시뮬레이션이 불가능합니다. 수식적 접근으로 전환합니다."라고 판단하고 Path B로 전환한다.
        
        →
        
        N
        
- **Sandboxing:** 외부 인터넷 접근이 차단된 환경이므로, 사전에 허용된 라이브러리(NumPy, Pandas, SymPy, SciPy 등)만 사용하도록 엄격히 제한한다.

### **Stage 5: The Verification Router (검증 라우터 - 최종 관문)**

답안 제출 전, 환각(Hallucination)을 방지하기 위한 최후의 방어선이다.

- **Scale-Down Test:** 문제의 *N*을 매우 작은 값(예: *N*=1,2,3)으로 변경하여 시뮬레이션을 돌리고, 이론적 해가 이 작은 값들에 대해서도 성립하는지 검증한다.
    
    N
    
    N=1,2,3
    
- **Reverse Check (역산):** 구해진 답 *X*를 문제의 조건에 대입하여 모순이 없는지 확인한다. 예를 들어 방정식의 해라면, 대입했을 때 0이 되는지 확인한다.
    
    X
    
- **Format Compliance:** 최종 답안이 0-99999 사이의 정수인지 확인하고, 범위를 벗어날 경우 모듈러 연산이나 포맷팅을 강제 적용한다.

## **6. 데이터 생성 전략: "Reverse Engineering" (역공학) 엔진**

Math Corpus Prize($30,000) 수상과 모델 성능 향상을 위해, 우리는 기존 데이터를 수집하는 것이 아니라 "정답으로부터 문제를 생성하는" 역방향 생성 전략을 채택한다. 이는 데이터의 **참신성(Novelty)**과 **무결성(Integrity)**을 100% 보장한다.

### **6.1 역방향 생성의 원리 (Backward Problem Generation)**

일반적인 LLM 학습 데이터 생성은 "문제를 주고 풀어라"는 방식이지만, 이는 LLM이 잘못된 풀이를 생성할 위험이 있다. 반면, 역방향 생성은 다음과 같이 진행된다.

1. **정답(Target Answer) 설정:** 임의의 5자리 정수 *A*를 선택한다.
    
    A
    
2. **수학적 구조(Core Structure) 생성:** 정답 *A*가 도출될 수밖에 없는 수학적 구조(방정식, 수열, 기하학적 배치)를 무작위 파라미터로 생성한다.
    
    A
    
3. **문제화(Problemification):** 생성된 구조를 자연어 문제로 변환하고, 정보의 일부를 숨겨(Masking) 난이도를 조절한다.
4. **검증:** 생성된 문제를 다시 풀어보아 정답이 유일한지 확인한다.

### **6.2 도메인별 생성 알고리즘**

### **6.2.1 Domain A: 합성 정수론 (Diophantine Construction)**

- **목표:** 선형 디오판토스 방정식 *ax*+*by*=*c* 형태의 문제를 생성하되, 해가 유일하거나 특정 조건을 만족하도록 한다.
    
    ax+by=c
    
- **알고리즘:**
    1. 목표 해 *x*0,*y*0를 랜덤 생성.
        
        x0,y0
        
    2. 서로소인 계수 *a*,*b*를 생성.
        
        a,b
        
    3. c=ax0+by0*c*=*ax*0+*by*0 계산.
    4. **Traceback:** "147원짜리 사과와 258원짜리 배를 합쳐서 369원을 만들 때..."와 같은 문장제(Word Problem)로 변환하거나, "147*x*≡369(mod258)" 형태의 합동식 문제로 변환.
        
        147x≡369(mod258)
        
    5. `sympy.solvers.diophantine`을 사용하여 해의 유일성 검증.

### **6.2.2 Domain B: 합성 다항식 (Polynomial Root Obfuscation)**

- **목표:** 정수근을 가지는 고차 다항식 문제를 생성.
- **알고리즘:**
    1. 정수근 *r*1,*r*2,*r*3 선택.
        
        r1,r2,r3
        
    2. 다항식 *P*(*x*)=(*x*−*r*1)(*x*−*r*2)(*x*−*r*3) 구성 및 전개하여 *ax*3+*bx*2+*cx*+*d*=0 형태의 계수 도출.
        
        P(x)=(x−r1)(x−r2)(x−r3)
        
        ax3+bx2+cx+d=0
        
    3. **Obfuscation:** 변수 치환(예: *t*=*x*2)을 적용하거나, "세 근의 합과 곱의 관계"를 묻는 근과 계수의 관계 문제로 변형.
        
        t=x2
        
    4. Python `hypothesis` 라이브러리를 사용하여 다양한 입력값에 대해 다항식의 성질이 유지되는지 테스트.

### **6.2.3 Domain C: 기하학적 "Traceback" (Geometric Construction)**

- **목표:** AlphaGeometry의 방식을 차용하여 좌표 기반의 기하 문제 생성.
- **알고리즘:**
    1. 좌표평면 위에 정수 좌표를 갖는 점 *A*,*B*,*C*를 무작위 배치.
        
        A,B,C
        
    2. 거리, 넓이, 무게중심, 외심 등의 속성을 계산 (Ground Truth).
    3. **Task Generation:** "세 변의 길이가 각각 *L*1,*L*2,*L*3인 삼각형의 넓이를 구하시오"와 같이 좌표를 숨기고 속성값만 제시.
        
        L1,L2,L3
        
    4. **Novelty:** 좌표가 무작위로 생성되므로, 기존 교과서나 인터넷에 존재하지 않는 완전히 새로운 문제(Unique Geometry)가 됨.

### **6.3 Schema v4.0: "사고의 지도"를 담은 데이터셋**

Math Corpus Prize의 "Format" 점수를 극대화하기 위해, 단순한 (질문, 정답) 쌍이 아닌, 문제 해결의 전 과정을 담은 고밀도 스키마를 정의한다.

**표 2: Open-Reverse-Math 데이터셋 스키마 (v4.0)**

| 필드명 (Field) | 설명 (Description) | 생성 방법 (Source) |
| --- | --- | --- |
| `problem_id` | 고유 식별자 (UUID) | System Generation |
| `topic_tag` | 세부 주제 (예: "Modular Arithmetic") | Generator Metadata |
| `difficulty_level` | 1-10 난이도 척도 | 내부 표현(Internal Rep.) 기반 예측 |
| `problem_text` | LaTeX 포맷의 문제 텍스트 | LLM Rewriting of Symbolic Core |
| `strategic_analysis` | **핵심:** 문제를 풀기 전의 전략 분석 (도구 선택, N*N* 크기 분석 등) | Teacher Model (DeepSeek-R1) Inference |
| `reasoning_trace` | 텍스트 사고 과정과 Python 코드가 혼합된 CoT | 생성 당시의 Traceback 로직 역서술 |
| `python_code` | 정답을 도출하는 실행 가능한 Python 코드 | SymPy/Simulator 기반 생성 |
| `verification_logic` | 답을 검증하는 별도의 코드 (PBT) | 역산 로직 (Inverse Check) |

이 스키마는 모델이 단순히 답을 맞히는 것이 아니라, `strategic_analysis`를 통해 계획을 세우고, `verification_logic`을 통해 검토하는 "메타인지"를 학습할 수 있도록 설계되었다.

- **Base Model:** 우리는 Qwen-2.5-7B-Instruct를 주 모델로 선정한다. 이들은 코딩 능력(HumanEval)과 수학 능력(MATH)에서 탁월한 성능을 보이며, 4-bit 양자화(AWQ/GPTQ) 적용 시 L4, 2 T4 환경 메모리에 적재 가능하다.
- **Inference Engine:** vLLM을 사용하여 추론 속도를 극대화한다. vLLM의 PagedAttention 기술은 긴 문맥(Long Context) 처리 시 메모리 효율을 높여주며, 이는 다단계 추론(CoT) 과정에서 필수적이다.

우리는 Python의 `hypothesis` 라이브러리를 활용하여 수학적 가설을 검증한다.

- **적용 예시:** 모델이 "임의의 정수 *n*에 대해 *n*3−*n*은 6의 배수이다"라는 정리를 증명하려 할 때, `hypothesis`를 통해 수천 개의 *n*을 무작위로 생성하여 `n^3 - n % 6 == 0` 조건을 고속으로 테스트한다.

- **이점:** 이는 복잡한 정리 증명기(Coq, Lean)를 사용하는 것보다 훨씬 가볍고 빠르며, MathCodeOrchestrator의 제한된 컴퓨팅 자원 내에서 실용적인 검증력을 제공한다.

---

주요 기술 용어 정리

- **TIR (Tool-Integrated Reasoning):** 자연어 추론 과정에 Python 코드 실행이나 계산기 등의 도구 사용을 통합하는 기법.
- **CoT (Chain of Thought):** 문제를 해결하기 위해 일련의 중간 추론 단계를 생성하는 프롬프팅 기법.
- **PBT (Property-Based Testing):** 특정 입력값 대신, 입력값이 가져야 할 속성(Property)을 정의하고 무작위 데이터를 대량으로 생성하여 코드를 테스트하는 기법.
- **GenSelect (Generative Solution Selection):** 여러 개의 후보 해를 생성한 후, 이를 평가하는 모델을 통해 가장 우수한 해를 선택하는 기법.
- **Reverse Engineering (in Math Data):** 정답과 수학적 구조를 먼저 정의하고, 이를 바탕으로 문제를 역으로 생성하는 합성 데이터 구축 방식.