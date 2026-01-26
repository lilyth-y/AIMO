# AIMO 3 프로젝트 계획 검토 및 MCP 서버 분석 보고서

## 1. AIMO 3 전략 성공 가능성 검토 (Success Probability Review)

귀하의 "Plan & Code" 및 "Reverse Engineering" 전략은 AIMO 3의 요구사항(IMO 수준 난이도, 5자리 정수 정답, 데이터 상)을 매우 정확하게 타격하고 있습니다. 그러나 몇 가지 **치명적인 리스크(Critical Risks)**가 존재하며, 이를 보완해야 성공 확률을 80% 이상으로 끌어올릴 수 있습니다.

### ✅ 강점 (Strengths)
1.  **접근 방식의 적합성:** "Just Code"의 한계를 인식하고 "Plan & Code"로 전환한 것은 IMO 수준 문제 해결의 필수 조건입니다.
2.  **데이터 전략의 우수성:** "역공학(Reverse Engineering)" 방식은 데이터의 무결성(정답 보장)과 참신성(Novelty)을 동시에 확보할 수 있는 유일한 방법입니다. Math Corpus Prize 수상 가능성이 매우 높습니다.
3.  **검증의 체계화:** 5자리 정수 포맷에 맞춰 `Verification Router`를 별도로 둔 것은 실전에서 점수 손실을 막는 핵심 장치입니다.

### ⚠️ 위험 요소 및 병목 (Risks & Bottlenecks)
1.  **라우터의 정확도 (The Router Accuracy Paradox):**
    *   **문제:** Stage 3의 `Calculation Router`가 잘못된 판단을 내릴 경우(예: 시뮬레이션으로 풀어야 할 문제를 이론으로 접근), 전체 파이프라인이 붕괴됩니다. 32B 모델조차도 메타인지 능력은 완벽하지 않습니다.
    *   **보완책:** **"Fast Fail & Fallback"** 메커니즘이 필요합니다. 한 경로가 30초 내에 유의미한 진전이 없으면 즉시 다른 경로로 전환하는 로직을 추가해야 합니다.
2.  **시간 제한 (Time Limit Constraints):**
    *   **문제:** 5단계 파이프라인은 단일 "Just Code" 방식보다 훨씬 많은 시간을 소모합니다. 5시간 내에 50~100문제를 풀어야 한다면, 문제당 할당 시간은 3~6분입니다. 복잡한 시뮬레이션이나 PBT(Property-Based Testing)는 이 시간을 초과할 수 있습니다.
    *   **보완책:** 난이도 예측(Difficulty Prediction)을 통해 쉬운 문제에 시간을 아끼고, 어려운 문제에 시간을 투자하는 **"Time Budgeting"** 알고리즘이 필요합니다.
3.  **Windows vs Linux 환경 차이:**
    *   **문제:** 현재 개발 환경은 Windows(`pwsh`)이지만, 대회 환경(Kaggle)은 Linux입니다. `signal.alarm` 등 OS 의존적인 코드는 호환성 문제를 일으킬 수 있습니다.
    *   **보완책:** 개발 초기부터 Docker 컨테이너를 사용하여 Linux 환경에서 테스트해야 합니다.

---

## 2. MCP 서버 병목 및 중복 체크 (MCP Server Analysis)

현재 감지된 MCP 서버(`sqlite-mcp-server`, `simplechecklist`, `arxiv-mcp-server`)를 분석한 결과입니다.

### 🔍 현황 분석
*   **sqlite-mcp-server:** 데이터 저장, 벡터 검색, 분석용. (핵심 인프라)
*   **simplechecklist:** 프로젝트 태스크 관리용. (매니지먼트 도구)
*   **arxiv-mcp-server:** 논문 검색 및 다운로드용. (연구 보조 도구)

### 🛠️ 중복성 (Redundancy)
*   **결과:** **중복 없음 (Clean).**
*   각 서버의 역할이 명확하게 분리되어 있습니다. (데이터베이스 vs 일정 관리 vs 외부 지식 탐색)

### 🚀 병목 구간 (Bottlenecks) 및 최적화 제안

#### 1. 데이터 생성 파이프라인의 병목 (Data Generation Bottleneck)
*   **상황:** 500,000개의 합성 데이터를 생성하여 `sqlite-mcp-server`에 저장해야 합니다.
*   **병목:** MCP 프로토콜을 통해 데이터를 **한 건씩(Row-by-Row)** INSERT하면 통신 오버헤드로 인해 속도가 매우 느려질 것입니다.
*   **해결책:**
    *   데이터 생성 스크립트(`reverse_engineering.py`)가 CSV나 JSONL 파일로 대량의 데이터를 먼저 생성하게 하십시오.
    *   그 후 `sqlite-mcp-server`의 **"Smart CSV/JSON import"** 기능을 사용하여 **일괄 적재(Bulk Load)** 하십시오.

#### 2. 지식 검색의 병목 (Knowledge Retrieval Bottleneck)
*   **상황:** `arxiv-mcp-server`를 통해 관련 논문을 찾고 지식을 추출하려 합니다.
*   **병목:** 논문 전문(PDF/Markdown)을 매번 LLM 컨텍스트에 올리면 토큰 비용과 처리 시간이 급증합니다.
*   **해결책:**
    *   `arxiv-mcp-server`로 다운로드한 논문을 `sqlite-mcp-server`의 **"Vector Search"** 기능과 연동하십시오.
    *   논문을 청크(Chunk)로 나누어 임베딩하고 SQLite에 저장한 뒤, 필요한 부분만 검색하여 가져오는 **RAG(Retrieval-Augmented Generation)** 파이프라인을 구축해야 합니다.

#### 3. 실행 환경의 병목 (Execution Environment)
*   **상황:** 현재 `stage4_execution.py`는 단순한 `exec()` 래퍼입니다.
*   **병목:** 상태(State)가 유지되지 않아, 이전 단계의 계산 결과를 재사용하기 어렵습니다.
*   **해결책:** `sqlite-mcp-server`를 **"Execution Cache"**로 활용하십시오. 중간 계산 결과나 성공한 코드 스니펫을 DB에 저장하여, 유사한 하위 문제가 나왔을 때 재연산 없이 결과를 가져오도록 하십시오.

## 3. 종합 제언 (Conclusion)

현재 계획은 **"High Risk, High Return"** 전략입니다. 성공 가능성을 높이기 위해 다음 두 가지 작업을 우선적으로 수행할 것을 권장합니다.

1.  **Fallback Logic 구현:** `stage3_router.py`에 경로 실패 시 대안 경로로 자동 전환하는 로직 추가.
2.  **Bulk Data Pipeline 구축:** `sqlite-mcp-server`를 활용한 대량 데이터 생성 및 적재 테스트.
