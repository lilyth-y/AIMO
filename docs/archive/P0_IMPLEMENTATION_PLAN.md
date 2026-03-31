# P0 작업 계획 및 이행 현황

**작성일**: 2026-02-02  
**목표**: 평가 보고서 기반 P0 작업 완료 및 전체 권장사항 적용  
**상태**: 진행 중

---

## 📋 P0 작업 개요

P0는 **Core Correctness & Safety** 영역의 즉시 영향 작업입니다.
총 4개의 메인 항목이 있습니다.

| ID | 작업 | 현황 | 목표 | 담당 |
|-----|------|------|------|------|
| P0-1 | Advanced Verification Module | 진행 중 | 90%+ 정확도 | Phase 1 |
| P0-2 | Reasoning-Answer Reconciliation | 진행 중 | 완전 구현 | Phase 1 |
| P0-3 | Self-Refine Loop | 진행 중 | 10-20% 복구율 | Phase 1 |
| P0-4 | Execution Resource Limits | 진행 중 | 타임아웃 100% 감지 | Phase 1 |

---

## 📝 상세 작업 계획

### P0-1: Advanced Verification Module 강화

**현황**: 기본 구현 완료, 고급 기능 추가 필요

**위치**: `src/pipeline/stage5_verification.py`

**작업 항목**:
```
[ ] 1.1 Rational Simplification
    - 분수 정규화 (최소공배수 적용)
    - 교차검증: candidate/expected 모두 simplify 후 비교
    
[ ] 1.2 Symbolic Equality 강화
    - sympy.simplify() → sympy.expand() → sympy.factor() 순차 적용
    - trigsimp, ratsimp, cancel 추가
    - 표현식 정규화 비교
    
[ ] 1.3 Numeric Tolerance 개선
    - 상대 오차 (relative error): < 1e-6
    - 절대 오차 (absolute error): < 1e-8
    - 부동소수점 안전 비교
    
[ ] 1.4 Collection 비교 강화
    - Set/List 다중집합 비교
    - Counter 기반 정확한 비교
    
[ ] 1.5 Context 역검증
    - 원래 방정식 템플릿에 해 재대입
    - 수렴성 검증 (optimization 문제)
    
[ ] 1.6 테스트
    - simple_algebra_tests.py 작성
    - 100개 케이스 검증
```

**수용 기준**: 90%+ 정확도로 간단한 대수 문제 검증/거부

---

### P0-2: Reasoning-Answer Reconciliation

**현황**: 기본 구조 완료 (`reconciliation.py`), 분류 정확도 개선 필요

**위치**: `src/pipeline/reconciliation.py`

**작업 항목**:
```
[ ] 2.1 ANS 추출 개선
    - <ANS>태그에서 값 추출 로직 강화
    - 여러 형식 지원 (수식, 리스트, LaTeX)
    
[ ] 2.2 분류 정확도
    - MISMATCH_ARITHMETIC: 산술 오류만 정확히 분류
    - MISMATCH_LOGIC: 논리 오류 명확히 구분
    - ERROR_PARSING: 파싱 불가 경우
    
[ ] 2.3 Canonicalization
    - sympy 기반 정규화
    - 기호 변수 일관성 확인
    
[ ] 2.4 로깅
    - 모든 불일치 분류 기록
    - 거짓 불일치 감소 추적
    
[ ] 2.5 테스트
    - reconciliation_test.py 작성
    - 1000개 샘플 검증
```

**수용 기준**: 거짓 불일치(false positive) 50% 이상 감소

---

### P0-3: Self-Refine Loop

**현황**: 단일 재시도 구조 있음, 프롬프트 최적화 필요

**위치**: `src/pipeline/orchestrator.py` (Stage 3-4 통합)

**작업 항목**:
```
[ ] 3.1 Targeted Refine Prompt
    - 에러 카테고리 포함 (MISMATCH_ARITHMETIC 등)
    - 이전 시도 반영
    - 수정 방향 명시
    
[ ] 3.2 한 번 재시도 제한
    - 전략별 최대 1회 재시도
    - 타임아웃 고려
    
[ ] 3.3 로깅
    - 첫 시도 결과
    - 재시도 결과
    - 복구 여부
    
[ ] 3.4 테스트
    - refine_loop_test.py 작성
    - 100개 실패 케이스에서 복구율 측정
```

**수용 기준**: 10-20% 복구율 달성

---

### P0-4: Execution Resource Limits

**현황**: 기본 구현 완료 (`stage4_execution.py`), 엣지 케이스 처리 필요

**위치**: `src/pipeline/stage4_execution.py`

**작업 항목**:
```
[ ] 4.1 타임아웃 감시
    - Wall time 모니터링 (multiprocessing)
    - CPU time 모니터링 (psutil)
    - 100% 감지율 달성
    
[ ] 4.2 메모리 제한
    - 환경변수: AIMO_EXECUTOR_MEMORY_MB
    - 기본값: 768MB
    - 누수 방지
    
[ ] 4.3 금지 패턴 확장
    - 파일 I/O: open(), pathlib 차단
    - 네트워크: socket, urllib 차단
    - 프로세스: subprocess, multiprocessing 차단
    
[ ] 4.4 무한 루프 방지
    - 복잡도 분석 (루프 깊이, 반복 횟수)
    - 조기 감지
    
[ ] 4.5 테스트
    - resource_limits_test.py 작성
    - 무한 루프 100개 감시
    - 메모리 폭발 50개 감시
```

**수용 기준**: 모든 타임아웃/메모리 초과 일관되게 감지

---

## 🔧 구현 순서

### Phase 1 (이번): 메인 P0 작업
1. **P0-2 먼저 (1-2일)**
   - 기존 코드가 있어서 개선만 하면 됨
   - ANS 추출 강화 (다른 모듈에 영향 최소)

2. **P0-1 (2-3일)**
   - Reconciliation 완료 후 테스트 케이스 충분
   - 검증 정확도 직결

3. **P0-3 (1-2일)**
   - P0-1, P0-2 완료 후 통합

4. **P0-4 (1일)**
   - 이미 기본 구현 있음
   - 엣지 케이스만 보강

---

## 📊 성과 측정

### P0-1 Advanced Verification
```
메트릭: 
- 간단 대수 문제 100개 정확도
- 현재: N/A
- 목표: 90%+
- 성공: PASS
```

### P0-2 Reconciliation
```
메트릭:
- 거짓 불일치 감소율
- 현재: N/A
- 목표: 50%+ 감소
- 성공: PASS
```

### P0-3 Self-Refine
```
메트릭:
- 복구율 (재시도 후 정답)
- 현재: N/A
- 목표: 10-20%
- 성공: PASS
```

### P0-4 Resource Limits
```
메트릭:
- 타임아웃 감지율
- 현재: ~95%
- 목표: 100%
- 성공: PASS
```

---

## 🔄 진행상황 추적

### 체크리스트

- [ ] P0-1 구현 완료
- [ ] P0-1 테스트 (100 케이스, 90%+ 통과)
- [ ] P0-2 구현 완료
- [ ] P0-2 테스트 (1000 샘플, 거짓 불일치 50% 감소)
- [ ] P0-3 구현 완료
- [ ] P0-3 테스트 (100 케이스, 10-20% 복구)
- [ ] P0-4 보강 완료
- [ ] P0-4 테스트 (타임아웃/메모리 100% 감지)
- [ ] 통합 테스트 (전체 파이프라인)
- [ ] 성과 보고서 작성

---

## 📌 주의사항

- **기존 테스트 유지**: 현재 94% 정확도 유지 필수
- **성능 저하 방지**: 검증 단계의 과도한 연산 회피
- **Windows 호환성**: multiprocessing 테스트 필수
- **문서화**: 각 단계마다 변경사항 기록

---

## 다음 단계

P0 완료 후:
1. P1: Strategy Selection Features (머신러닝 기반)
2. P1: Log Analytics Pipeline
3. P2: Candidate Voting Ensemble
4. 평가 재실행 (94% → 95%+ 달성 확인)
