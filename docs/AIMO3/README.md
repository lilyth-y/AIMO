# MathCodeOrchestrator3 프로젝트

## MathCodeOrchestrator3란?

**MathCodeOrchestrator** = **AI Mathematical Olympiad** (AI 수학 올림피아드)

**MathCodeOrchestrator3** = **MathCodeOrchestrator Progress Prize 3** (AI 수학 올림피아드 진행상 상 3회 대회)

## 대회 개요

MathCodeOrchestrator는 AI가 수학 올림피아드 문제를 해결하는 능력을 평가하는 경진대회입니다.

### 대회 버전별 비교

| 버전 | 난이도 | 정답 형식 | 하드웨어 | 특징 |
|------|--------|----------|----------|------|
| **MathCodeOrchestrator 1** | AIME 수준 | 3자리 정수 (0-999) | T4 GPU x 2 | 초기 대회 |
| **MathCodeOrchestrator 2** | AIME/국가 올림피아드 | 3자리 정수 (0-999) | T4 GPU x 2 | 규칙 정립 |
| **MathCodeOrchestrator 3** | **IMO 수준** | **5자리 정수 (0-99999)** | **L4 x 4 또는 H100** | **최고 난이도** |

### MathCodeOrchestrator3의 특징

1. **최고 난이도**: IMO (국제수학올림피아드) 수준의 킬러 문항 포함
2. **5자리 정수**: 추측 불가능한 정답 범위 (0-99,999)
3. **강력한 하드웨어**: H100 또는 L4 GPU 제공
4. **Math Corpus Prize**: 데이터셋 제출 경쟁 병행

## 이 프로젝트의 목표

이 프로젝트는 **MathCodeOrchestrator Progress Prize 3** 참가를 위한 시스템입니다.

### 주요 전략

1. **"Plan & Code"** 철학
   - 기존 "Just Code" 방식의 한계 극복
   - 문제 분석 → 전략 선택 → 실행 → 검증

2. **5-Stage Pipeline**
   - Stage 1: 문제 분류 및 라벨링
   - Stage 2: 관련 문제/해법 검색
   - Stage 3: 전략 라우팅 (Simulator/Theoretician/Hybrid)
   - Stage 4: 코드 실행
   - Stage 5: 답변 검증

3. **역공학 데이터 생성**
   - Math Corpus Prize를 위한 데이터셋 생성
   - 정답으로부터 문제를 역으로 생성

## 관련 문서

- [Report.md](Report.md) - MathCodeOrchestrator3 프로젝트 상세 리포트 (15,000단어)
- [TODO.md](TODO.md) - MathCodeOrchestrator3 프로젝트 TODO

## 참고

- **AIME**: American Invitational Mathematics Examination
- **IMO**: International Mathematical Olympiad (국제수학올림피아드)
- **Progress Prize**: 진행상 상 (대회가 진행되면서 성과를 보여주는 팀에게 주는 상)
