# P0 작업 종합 요약 및 구현 계획

**작성일**: 2026-02-02  
**프로젝트**: AIMO (OMI)  
**버전**: P0 Phase  
**상태**: 이행 중

---

## 📌 핵심 요약

### 배경
AIMO 프로젝트의 평가 결과:
- **현재 정확도**: 94%
- **목표 정확도**: 95%+
- **주요 약점**: CRT 문제 (66.7%), Level 4 (66.7%)
- **전략**: P0 → P1 → P2 순차 개선

### P0 작업의 목표
**Core Correctness & Safety** - 기본기 다지기
1. 검증 시스템 강화
2. ANS 추출 정확화
3. 재시도 로직 추가
4. 리소스 제한 완성

### 기대 효과
```
P0 완료 후:
- 거짓 불일치 50% 감소
- 검증 정확도 90%+
- 복구율 10-20% 추가
→ 94% 정확도 유지 + 내구성 향상
```

---

## 📁 작업 파일 구조

### 신규 생성 파일

#### 1. 구현 파일
```
src/pipeline/
├── answer_extraction.py          # P0-2: ANS 추출 강화
│   ├── AnswerExtractor (INT, FLOAT, LATEX, LIST, SET, SYMPY)
│   ├── ExtractionResult (dataclass)
│   └── 전역 함수
│
├── verification_enhancements.py   # P0-1: 검증 강화
│   ├── RationalSimplifier (gcd 기반)
│   ├── SymbolicEqualityChecker (순차 simplify)
│   ├── ReverseVerifier (역검증)
│   ├── ConstraintValidator (제약 조건)
│   └── AdvancedVerificationHelper (통합)
│
├── refine_loop.py                 # P0-3: 재시도 (예정)
│   ├── RefineLoopManager
│   └── 타겟된 프롬프트 생성
└── (추가될 수 있음)
```

#### 2. 개선 파일
```
src/pipeline/
├── stage5_verification.py         # P0-1: 문서 개선
├── reconciliation.py              # P0-2: 통합 개선
└── stage4_execution.py            # P0-4: 보강 (미완)
```

#### 3. 테스트 파일
```
tests/
├── test_reconciliation_p0.py       # P0-2: 10개 시나리오
├── test_verification_p0.py         # P0-1: 100개 케이스 (예정)
├── test_refine_loop_p0.py          # P0-3: 복구율 측정 (예정)
└── test_resource_limits_p0.py      # P0-4: 150개 케이스 (예정)
```

#### 4. 문서 파일
```
docs/
├── P0_IMPLEMENTATION_PLAN.md       # P0 상세 계획
├── IMPROVEMENT_ROADMAP.md          # 전체 로드맵 (P0-P3)
├── P0_WEEKLY_PROGRESS.md           # 주간 진행 상황 (이 파일)
├── PROJECT_EVALUATION_REPORT.md    # 평가 보고서 (기존)
└── (추가될 예정)
```

---

## 🔄 P0 4단계 상세 계획

### Phase 1: P0-2 (ANS 추출 & Reconciliation) - 1-2일

**왜 먼저?**
- 다른 모듈에 영향 최소
- 기존 코드 기반에서 개선만
- 테스트 용이

**파일**:
- `src/pipeline/answer_extraction.py` ✅ 완료
- `src/pipeline/reconciliation.py` 개선
- `tests/test_reconciliation_p0.py` ✅ 완료

**작업**:
```
1. ANS 추출 강화 (완료)
   - 정수, 부동소수점, LaTeX 분수
   - 리스트, 집합, SymPy 표현식
   
2. Reconciliation 통합
   - answer_extraction 연동
   - 분류 정확도 향상
   
3. 테스트
   - 1000개 샘플 평가
   - 거짓 불일치 50% 감소 확인
```

**성과 기준**:
- 거짓 불일치: 50%+ 감소
- 분류 정확도: 85%+

---

### Phase 2: P0-1 (검증 강화) - 2-3일

**왜 두 번째?**
- P0-2의 정규화 결과로 검증 정확도 향상
- 검증 정확도는 전체 시스템의 정확도에 직결
- 간단한 대수 문제부터 테스트

**파일**:
- `src/pipeline/verification_enhancements.py` ✅ 완료
- `src/pipeline/stage5_verification.py` 통합
- `tests/test_verification_p0.py` 작성

**작업**:
```
1. Rational Simplification (완료)
   - gcd 기반 분수 정규화
   
2. Symbolic Equality (완료)
   - 8가지 메서드 순차 적용
   
3. Context 역검증 (완료)
   - 방정식 재대입
   - 수렴성 검증
   
4. 통합 & 테스트
   - 100개 간단 대수 문제
   - 90%+ 정확도 달성
```

**성과 기준**:
- 검증 정확도: 90%+
- 거짓 양성: < 5%

---

### Phase 3: P0-3 (재시도 로직) - 1-2일

**왜 세 번째?**
- P0-1, P0-2 완료 후 에러 분류가 명확함
- 타겟된 프롬프트 생성 가능

**파일**:
- `src/pipeline/refine_loop.py` (예정)
- `src/pipeline/orchestrator.py` 개선
- `tests/test_refine_loop_p0.py` 작성

**작업**:
```
1. RefineLoopManager 설계
   - 에러 카테고리별 프롬프트
   - 한 번 재시도 제한
   
2. 프롬프트 최적화
   - MISMATCH_ARITHMETIC 맞춤형
   - MISMATCH_LOGIC 맞춤형
   - 이전 시도 반영
   
3. 테스트
   - 100개 실패 케이스
   - 10-20% 복구율 달성
```

**성과 기준**:
- 복구율: 10-20%
- 추가 타임아웃: < 1%

---

### Phase 4: P0-4 (리소스 제한) - 1일

**왜 마지막?**
- 이미 기본 구현이 95% 감시 중
- 엣지 케이스만 보강

**파일**:
- `src/pipeline/stage4_execution.py` 보강
- `tests/test_resource_limits_p0.py` 작성

**작업**:
```
1. 타임아웃 100% 감시
   - multiprocessing Wall time
   - psutil CPU time
   
2. 메모리 제한
   - 환경변수 설정
   - 누수 방지
   
3. 금지 패턴 확장
   - 파일 I/O
   - 네트워크
   - 프로세스
   
4. 테스트
   - 무한 루프 100개
   - 메모리 폭발 50개
   - 100% 감지 확인
```

**성과 기준**:
- 감지율: 100%
- 거짓 긍정: < 1%

---

## 📊 현재 구현 현황

### 완료 (100%)
- [x] Answer Extraction 모듈 (answer_extraction.py)
  - 9개 형식 지원
  - 10개 단위 테스트 작성
  
- [x] Verification Enhancements 모듈 (verification_enhancements.py)
  - 4개 검증기 클래스
  - 포괄적 constraint 시스템
  
- [x] Reconciliation 테스트 (test_reconciliation_p0.py)
  - 14개 테스트 시나리오
  - 성과 지표 추적

### 진행 중 (40%)
- [ ] Reconciliation 통합 (reconciliation.py)
  - 상태: 프레임워크 개선됨
  - 남은 작업: answer_extraction 연동
  
- [ ] 전체 통합 테스트
  - 상태: 개별 테스트만 완료
  - 남은 작업: 엔드-투-엔드 테스트

### 미시작 (0%)
- [ ] P0-3 Self-Refine Loop (refine_loop.py)
- [ ] P0-4 Resource Limits 보강

---

## 🧪 테스트 전략

### Unit Tests (개별)
```
1. Answer Extraction (완료)
   - 9개 형식 × 2회 = 18개
   - 통과율: 100% 예상

2. Verification Enhancements (작성 중)
   - 정규화: 5개
   - 검증: 10개
   - 제약: 15개
   - 통과율: 90%+ 목표

3. Reconciliation (완료)
   - 14개 시나리오
   - 통과율: 85%+ 목표
```

### Integration Tests (통합)
```
1. P0-1 + P0-2
   - 간단 대수 문제 100개
   - 정확도: 90%+ 목표

2. 전체 파이프라인
   - AIME 평가 재실행
   - 정확도: 94%+ 유지 목표

3. P0-3 (재시도)
   - 실패 케이스 복구
   - 복구율: 10-20% 목표
```

### Regression Tests (회귀)
```
- 기존 평가 데이터 (50개)
- 정확도 94% 유지 확인
- 일일 체크
```

---

## ⏰ 일정 계획

```
Week 1 (Feb 2-8)
├─ Mon 02   ✅ P0-2 구현 (answer_extraction.py)
├─ Mon 02   ✅ P0-1 구현 (verification_enhancements.py)
├─ Mon 02   ✅ 테스트 프레임워크 (test_reconciliation_p0.py)
├─ Tue 03   → P0-2 통합 & 테스트
├─ Tue 03   → P0-1 테스트 작성 (100 케이스)
├─ Wed 04   → P0-1 + P0-2 통합 테스트
├─ Thu 05   → P0-3 구현 시작
├─ Fri 06   → P0-3 + P0-4 마무리
├─ Sat 07   → 전체 P0 통합 테스트
└─ Sun 08   → 검수 & 정확도 확인

Week 2 (Feb 9-15)
├─ Mon 09   → P1 시작
├─ ...
└─ Fri 13   → 95%+ 정확도 달성 목표
```

---

## 📈 성과 추적 매트릭스

### P0-1: Advanced Verification
```
| 메트릭 | 현재 | 목표 | 달성 기준 |
|--------|------|------|---------|
| 간단 대수 정확도 | N/A | 90%+ | 100/110 |
| 거짓 양성 | N/A | <5% | 5/100 이하 |
| 컨텍스트 역검증 | N/A | 100% | 100/100 |
```

### P0-2: Reconciliation
```
| 메트릭 | 현재 | 목표 | 달성 기준 |
|--------|------|------|---------|
| 거짓 불일치 감소 | N/A | 50%+ | 개선 입증 |
| 분류 정확도 | N/A | 85%+ | 850/1000 |
| ANS 추출 정확도 | N/A | 95%+ | 950/1000 |
```

### P0-3: Self-Refine
```
| 메트릭 | 현재 | 목표 | 달성 기준 |
|--------|------|------|---------|
| 복구율 | N/A | 10-20% | 10-20/100 |
| 추가 타임아웃 | N/A | <1% | <1/100 |
| 프롬프트 정확도 | N/A | 90%+ | 90/100 |
```

### P0-4: Resource Limits
```
| 메트릭 | 현재 | 목표 | 달성 기준 |
|--------|------|------|---------|
| 타임아웃 감지율 | 95% | 100% | 150/150 |
| 메모리 감지율 | ~80% | 100% | 50/50 |
| 거짓 긍정 | N/A | <1% | <1.5/150 |
```

### 전체 P0
```
| 메트릭 | 현재 | 목표 | 달성 기준 |
|--------|------|------|---------|
| 정확도 (AIME) | 94% | 94%+ | PASS |
| 정확도 (NuminaMath) | 94% | 94%+ | PASS |
| 통합 테스트 | N/A | PASS | 모든 P0 항목 |
```

---

## 🎯 성공 기준 (Pass/Fail)

### P0 전체 완료 조건
```
✅ 모두 만족해야 PASS

1. P0-1: 간단 대수 90%+ 정확도
2. P0-2: 거짓 불일치 50%+ 감소
3. P0-3: 복구율 10-20%
4. P0-4: 타임아웃 감지 100%
5. 회귀: 정확도 94%+ 유지
6. 모든 테스트: 통과
```

### 각 단계 Go/No-Go
```
P0-1 완료 후:
→ 검증 정확도 90%+인가? YES → 진행, NO → 개선

P0-2 완료 후:
→ 거짓 불일치 50% 감소인가? YES → 진행, NO → 개선

P0-3 완료 후:
→ 복구율 10-20%인가? YES → 진행, NO → 개선

P0-4 완료 후:
→ 전체 정확도 94%+인가? YES → P1 시작, NO → 재검토
```

---

## 📝 문서화 체계

### 이미 작성된 문서
- [x] PROJECT_EVALUATION_REPORT.md - 평가 보고서
- [x] P0_IMPLEMENTATION_PLAN.md - P0 상세 계획
- [x] IMPROVEMENT_ROADMAP.md - 전체 로드맵
- [x] P0_WEEKLY_PROGRESS.md - 주간 진행

### 추가 작성 예정
- [ ] P0_PHASE_1_REPORT.md (P0-2 완료 후)
- [ ] P0_PHASE_2_REPORT.md (P0-1 완료 후)
- [ ] P0_FINAL_REPORT.md (P0 전체 완료 후)
- [ ] P1_STRATEGY_SELECTION.md (P1 시작 시)

---

## 🚀 실행 체크리스트

### 오늘 (2026-02-02)
- [x] P0 평가 보고서 작성
- [x] P0 계획 문서 작성
- [x] 로드맵 문서 작성
- [x] answer_extraction.py 구현
- [x] verification_enhancements.py 구현
- [x] 테스트 프레임워크 작성
- [ ] 현재 정확도 확인 (94% 유지)

### 명일 (2026-02-03)
- [ ] P0-2 reconciliation.py 통합
- [ ] test_reconciliation_p0.py 실행
- [ ] 거짓 불일치 측정
- [ ] P0-1 테스트 작성

### 추가 (2026-02-04~)
- [ ] P0-1 + P0-2 통합 테스트
- [ ] 간단 대수 100개 테스트
- [ ] P0-3 구현
- [ ] P0-4 보강
- [ ] 전체 평가 재실행

---

## 💡 주요 인사이트

### 왜 이 순서인가?
1. **P0-2 먼저**: 문제 추출 정확화 → 검증도 정확화
2. **P0-1 두 번째**: 정확한 검증으로 성능 향상
3. **P0-3 세 번째**: 명확한 에러 분류로 재시도 가능
4. **P0-4 마지막**: 기본 구현 있어서 보강만 하면 됨

### 위험 관리
```
🟢 낮은 위험: ANS 추출, 분수 정규화
🟡 중간 위험: SymPy 성능, 부동소수점 오차
🔴 높은 위험: 94% 정확도 유지
   → 해결책: 일일 회귀 테스트
```

### 학습 포인트
```
1. 검증: SymPy 강력하지만 느림 → 캐싱 필요
2. 추출: 다양한 형식 지원 필수 → 확장성 고려
3. 재시도: 타겟된 프롬프트 중요 → 분류 정확도 필수
4. 리소스: 100% 감시는 어려움 → 중복 메커니즘
```

---

## 📞 연락처 및 지원

### 문제 발생 시
1. 해당 문서 (P0_IMPLEMENTATION_PLAN.md) 참조
2. 관련 테스트 실행 (tests/test_*.py)
3. 로그 분석 (logs/eval_log.jsonl)
4. 주간 진행 문서 업데이트

### 변경 기록
- 2026-02-02 초안 작성
- (추가될 예정)

---

**문서 상태**: 활성 (Active)  
**마지막 업데이트**: 2026-02-02 16:30 KST  
**다음 업데이트**: 2026-02-03 18:00 KST
