# 프로젝트 개선 로드맵 (종합)

**작성일**: 2026-02-02  
**기반**: 종합 평가 보고서  
**목표**: 94% → 95%+ 정확도 달성 및 시스템 안정화

---

## 🎯 전략 요약

| 단계 | 기간 | 초점 | 성과 |
|------|------|------|------|
| **P0** | 1-2주 | Core Correctness & Safety | 기반 다지기 |
| **P1** | 2-3주 | Learning & Strategy Optimization | 성능 최적화 |
| **P2** | 3-4주 | Quality & Ensemble Robustness | 견고성 강화 |
| **P3** | 지속 | Polish & Research | 선택 개선 |

---

## 🔴 P0: Core Correctness & Safety (1-2주)

### P0-1: Advanced Verification Module
**파일**: `src/pipeline/stage5_verification.py`  
**목표**: 90%+ 정확도

```python
# 개선 사항:
1. Rational Simplification
   - gcd 기반 분수 정규화
   - 교차검증 비교

2. Symbolic Equality 강화
   - sympy.simplify() 순차 적용
   - trigsimp, ratsimp, cancel 포함

3. Numeric Tolerance
   - 상대 오차: < 1e-6
   - 절대 오차: < 1e-8

4. Collection 비교
   - Set/List 다중집합
   - Counter 기반

5. Context 역검증
   - 원 방정식 재대입
   - 수렴성 검증

테스트: simple_algebra_tests.py (100 케이스)
```

**수용 기준**: 
- 간단 대수 문제 90%+ 정확도
- 거짓 양성 < 5%

---

### P0-2: Reasoning-Answer Reconciliation
**파일**: `src/pipeline/reconciliation.py`  
**목표**: 거짓 불일치 50%+ 감소

```python
# 개선 사항:
1. ANS 추출 강화
   - LaTeX 형식 지원
   - 다중 형식 처리

2. 분류 정확도
   - MISMATCH_ARITHMETIC (산술 오류)
   - MISMATCH_LOGIC (논리 오류)
   - ERROR_PARSING (파싱 불가)

3. Canonicalization
   - sympy 기반
   - 기호 일관성

테스트: reconciliation_test.py (1000 샘플)
```

**수용 기준**:
- 거짓 불일치 감소: 50%+
- 분류 정확도: 85%+

---

### P0-3: Self-Refine Loop
**파일**: `src/pipeline/orchestrator.py` + 신규 모듈  
**목표**: 10-20% 복구율

```python
# 개선 사항:
1. Targeted Refine Prompt
   - 에러 카테고리 포함
   - 이전 시도 반영
   - 수정 방향 명시

2. 한 번 재시도 제한
   - 전략별 최대 1회
   - 타임아웃 고려

3. 상세 로깅
   - 첫 시도/재시도 결과
   - 복구 여부 추적

테스트: refine_loop_test.py (100 실패 케이스)
```

**수용 기준**:
- 복구율: 10-20%
- 타임아웃 추가 없음

---

### P0-4: Execution Resource Limits
**파일**: `src/pipeline/stage4_execution.py`  
**목표**: 100% 타임아웃/메모리 감지

```python
# 개선 사항:
1. 타임아웃 감시
   - Wall time (multiprocessing)
   - CPU time (psutil)
   - 감지율: 100%

2. 메모리 제한
   - AIMO_EXECUTOR_MEMORY_MB (기본: 768MB)
   - 누수 방지

3. 금지 패턴 확장
   - 파일 I/O
   - 네트워크
   - 프로세스 생성

4. 무한 루프 방지
   - 복잡도 분석
   - 조기 감지

테스트: resource_limits_test.py (150 케이스)
```

**수용 기준**:
- 모든 초과상황 감지율: 100%
- 거짓 긍정: < 1%

---

### 📊 P0 성과 지표
```
| 지표 | 현재 | 목표 | 성공 기준 |
|------|------|------|---------|
| 전체 정확도 | 94% | 94%+ (유지) | PASS |
| 검증 정확도 | N/A | 90%+ | PASS |
| 거짓 불일치 | N/A | 50% 감소 | PASS |
| 복구율 | N/A | 10-20% | PASS |
| 리소스 감시 | 95% | 100% | PASS |
```

---

## 🟠 P1: Learning & Strategy Optimization (2-3주)

### P1-5: Strategy Selection Features
**파일**: `src/pipeline/stage3_router.py` + 신규 모듈  
**목표**: 첫 시도 검증 성공률 향상

```python
# 구현:
1. Feature Extractor
   - 문제 길이, 복잡도 점수
   - 키워드 수 (기하학/수론/확률)
   - 연산자 다양성
   - 과거 성공률 버킷

2. Strategy Selection
   - 엡실론-그리디 밴딧 (epsilon-greedy)
   - 또는 로지스틱 분류기

3. 오프라인 재현 (Offline Replay)
   - 기존 평가 로그 사용
   - 새로운 선택 방식 검증

테스트: 기존 평가 로그 (10k+ 엔트리)
```

**수용 기준**:
- 오프라인 재현에서 첫 시도 성공률 5%+ 향상

---

### P1-6: Log Analytics Pipeline
**파일**: `scripts/analyze_logs.py`  
**목표**: 성능 메트릭 자동 생성

```python
# 구현:
1. JSONL → Parquet 변환
   - logs/eval_log.jsonl → results/eval_metrics.parquet

2. 분석 쿼리
   - 전략별 성공률
   - 불일치 유형 분포
   - 평균 복잡도별 성과

3. 시각화
   - 통계 테이블
   - 추세 그래프
   - 문제 분포

성능: < 5초 (10k 엔트리)
```

**수용 기준**:
- 실행 시간: < 5초
- 요약 테이블: 자동 생성

---

### P1-7: Decomposition vs Direct Classifier
**파일**: `src/pipeline/stage2_retrieval.py` + 신규 모듈  
**목표**: 불필요한 decomposition 호출 감소

```python
# 구현:
1. 분류 데이터셋
   - 성공/실패 레이블링된 문제들
   - 특징: 길이, 유형, 복잡도

2. 휴리스틱 또는 간단 모델
   - Decomposition 게이팅
   - 가중치 기반 선택

3. 평가
   - Decomposition 호출 감소
   - 정확도 동일 이상 유지

테스트: 평가 재실행
```

**수용 기준**:
- Decomposition 호출 20%+ 감소
- 정확도 유지 또는 향상

---

### P1-8: Lemma / Pattern Cache
**파일**: `src/pipeline/lemma_cache.py` (기존) → 개선  
**목표**: 캐시 히트율 10%+

```python
# 구현:
1. 정규화 표현식 해싱
   - sympy 정규형
   - 해시 저장

2. 재사용 추적
   - 사용 횟수
   - 성공 결과

3. 검색 지원
   - 새 문제와 유사도 비교
   - 인수분해, 조합 항등식 재사용

테스트: 따뜻한 시작 (warm-up)
```

**수용 기준**:
- 캐시 히트율: 10%+
- 응답 속도: 5% 향상

---

### 📊 P1 성과 지표
```
| 지표 | 현재 | 목표 | 성공 기준 |
|------|------|------|---------|
| 첫 시도 성공률 | N/A | +5% | PASS |
| 불필요 호출 감소 | N/A | -20% | PASS |
| 캐시 히트율 | N/A | 10%+ | PASS |
| 로그 분석 속도 | N/A | <5s | PASS |
```

---

## 🟡 P2: Quality & Ensemble Robustness (3-4주)

### P2-9: Candidate Voting Ensemble
**파일**: 신규: `src/pipeline/ensemble.py`  
**목표**: 앙상블 정확도 > 단일 전략

```python
# 구현:
1. 다중 해법 생성
   - 전략 변경 (Simulator → Theoretician)
   - 온도 변경 (다양한 샘플)

2. SymPy 동등성 투표
   - 각 후보 비교
   - 빈도 기반 선택

3. 정규화 비교
   - Factor/Expand 동등성

테스트: 500 문제 기준
```

**수용 기준**:
- 앙상블 정확도 > 단일 전략
- 정확도 향상: 1-3%

---

### P2-10: Multi-Step Self-Refine (Chain Repair)
**파일**: `src/pipeline/orchestrator.py` + 신규 모듈  
**목표**: 반복적 계획 편집을 통한 복구

```python
# 구현:
1. PLAN/DERIVATION 블록만 수정 요청
   - 결과 재계산

2. 최대 3회 재시도
   - 타임아웃 조건 포함

3. 수렴 감지
   - 같은 오류 반복 시 중단

테스트: 복잡한 실패 케이스
```

**수용 기준**:
- 복구율: 15-25% (P0-3 대비 향상)

---

### P2-11: Complexity-Driven Strategy Routing
**파일**: `src/pipeline/stage3_router.py`  
**목표**: 문제 복잡도에 따른 최적 경로

```python
# 구현:
1. 복잡도 점수 계산
   - 수식 크기
   - 연산자 다양성
   - 구조적 깊이

2. 라우팅 규칙
   - Low: Direct (Simulator)
   - Medium: Try Both (Hybrid)
   - High: Theory First (Theoretician)

테스트: 복잡도별 분석
```

**수용 기준**:
- 복잡도별 성공률 균등화

---

### 📊 P2 성과 지표
```
| 지표 | 현재 | 목표 | 성공 기준 |
|------|------|------|---------|
| 앙상블 정확도 | N/A | >단일 | PASS |
| 다단계 복구율 | N/A | 15-25% | PASS |
| 복잡도별 균등성 | N/A | 향상 | PASS |
```

---

## 🟢 P3: Polish & Research (지속)

### P3-12: Code Refactoring
**파일**: `src/pipeline/orchestrator.py` (3086줄 → 모듈화)  
**목표**: 가독성 및 유지보수성 향상

```
1. orchestrator.py 분해
   - stage_orchestrator_base.py
   - strategy_executor.py
   - result_aggregator.py

2. 테스트 가능성 개선
   - 단위 테스트 추가
   - Mock 지원

3. 문서화
   - 클래스 다이어그램
   - 상호작용 명시
```

---

### P3-13: Geometry Problem Specialization
**파일**: 신규: `src/pipeline/geometry_engine.py`  
**목표**: 기하학 문제 특화 처리

```
1. AlphaGeometry 스타일 접근
   - 뉴로-심볼릭 아키텍처
   - 보조선 생성

2. Sympy.geometry 통합
   - 좌표 설정
   - 정리 증명

테스트: IMO 기하 문제
```

---

### P3-14: Synthetic Data Generation
**파일**: 신규: `scripts/generate_synthetic_problems.py`  
**목표**: AlphaGeometry 역공학 방식

```
1. Traceback 방식
   - 임의 답 생성
   - 문제 역공학

2. 데이터 품질
   - 논리적 완결성 보장
   - 오염 위험 제거

3. 다양성
   - 대수학
   - 정수론
   - 기하학 확장
```

---

### P3-15: Performance Optimization
**파일**: `src/pipeline/` (전체)  
**목표**: 평가 시간 20% 단축

```
1. 캐싱 강화
   - 토크나이저 출력
   - 복잡도 계산

2. 병렬 처리
   - 다중 전략 동시 실행
   - 조기 종료

3. 메모리 최적화
   - 모델 언로드
   - 가비지 컬렉션
```

---

## 📈 전체 성과 지표

### 최종 목표
```
| 지표 | 현재 | 목표 | 달성 일정 |
|------|------|------|---------|
| 전체 정확도 | 94% | 95%+ | P0/P1 완료 후 |
| Level 4 정확도 | 66.7% | 85%+ | P1/P2 완료 후 |
| CRT 정확도 | 66.7% | 90%+ | P0-1 완료 후 |
| 평가 시간 | ~5h | ~4h | P3 완료 후 |
| 테스트 커버리지 | 21 files | 35+ files | 지속 |
| 코드 복잡도 | 높음 | 중간 | P3 완료 후 |
```

---

## 🔄 타임라인

```
Week 1 (Feb 2-8)
├─ P0-1: Advanced Verification (Mon-Tue)
├─ P0-2: Reconciliation (Wed)
├─ P0-3: Self-Refine (Thu)
└─ P0-4: Resource Limits (Fri)

Week 2 (Feb 9-15)
├─ P0 테스트 & 통합 (Mon-Tue)
├─ P1-5, P1-6: ML Selection & Analytics (Wed-Thu)
└─ P1-7, P1-8: Decomposition & Cache (Fri)

Week 3 (Feb 16-22)
├─ P1 테스트 & 성능 재평가 (Mon-Tue)
├─ P2-9: Ensemble (Wed)
├─ P2-10, P2-11: Multi-Refine & Routing (Thu-Fri)

Week 4+ (Feb 23+)
├─ P2 테스트 (Mon-Tue)
├─ 최종 평가 (95%+ 달성 확인)
└─ P3 점진적 진행
```

---

## 📝 문서화 계획

### 작성할 문서
1. **P0_IMPLEMENTATION_PLAN.md** (이미 작성) ✓
2. **IMPROVEMENT_ROADMAP.md** (이 파일) ✓
3. **P0_WEEKLY_PROGRESS.md** (매주 업데이트)
4. **P1_STRATEGY_SELECTION.md** (P1 시작 시)
5. **P2_ENSEMBLE_DESIGN.md** (P2 시작 시)
6. **REFACTORING_GUIDE.md** (P3 시작 시)

### 각 단계별 보고서
- [ ] P0 완료 보고서
- [ ] P1 완료 보고서
- [ ] P2 완료 보고서
- [ ] 최종 평가 보고서 (95%+ 달성)

---

## ✅ 체크리스트

### P0 Phase
- [ ] P0-1 구현 완료
- [ ] P0-2 구현 완료
- [ ] P0-3 구현 완료
- [ ] P0-4 보강 완료
- [ ] 통합 테스트 PASS (94% 유지)

### P1 Phase
- [ ] P1-5 구현 완료
- [ ] P1-6 구현 완료
- [ ] P1-7 구현 완료
- [ ] P1-8 구현 완료
- [ ] 성능 재평가 (95%+ 달성)

### P2 Phase
- [ ] P2-9 구현 완료
- [ ] P2-10 구현 완료
- [ ] P2-11 구현 완료
- [ ] 최종 평가

### P3 Phase
- [ ] 코드 리팩토링
- [ ] 기하학 특화
- [ ] 데이터 생성
- [ ] 성능 최적화

---

## 📞 지원 및 문제 해결

### 문제 발생 시
1. 해당 P단계 계획 문서 확인
2. 테스트 케이스 검토
3. 로그 분석
4. 문서 업데이트

### 커뮤니케이션
- 주간 진행상황 업데이트
- 블로커 이슈 우선 처리
- 성과 지표 주기적 확인
