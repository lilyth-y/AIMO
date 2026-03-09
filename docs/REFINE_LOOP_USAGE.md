# Self-Refine Loop 사용 가이드

## 개요

Self-Refine Loop는 검증 실패 시 자동으로 코드를 개선하는 시스템입니다. 기존의 단일 시도 방식에서 여러 번 반복하여 개선할 수 있는 루프 시스템으로 업그레이드되었습니다.

## 주요 기능

1. **다중 반복 지원**: 최대 3회까지 자동으로 refine 시도
2. **에러 타입별 맞춤 개선**: 에러 유형에 따라 다른 프롬프트 사용
3. **상태 추적**: 각 반복의 상태를 추적하고 로깅
4. **설정 가능**: 환경 변수로 최대 반복 횟수 및 활성화 여부 제어

## 사용 방법

### 1. 기본 사용 (Orchestrator에 통합)

`orchestrator.py`에서 기존 refine 로직을 `RefineLoop`로 교체:

```python
from .refine_loop import RefineLoop
from .settings import settings

class PipelineOrchestrator:
    def __init__(self):
        # ... 기존 초기화 코드 ...
        
        # RefineLoop 초기화
        self.refine_loop = RefineLoop(
            max_iterations=settings.refine_max_iterations,
            enable_loop=settings.refine_enabled
        )
    
    def solve_problem(self, ...):
        # ... 기존 코드 ...
        
        # 검증 실패 시
        if not verified:
            # RefineLoop 사용
            if self.refine_loop.should_refine(
                structured_used=structured_used,
                verified=verified,
                refine_used=getattr(self, '_refine_used', False)
            ):
                result, success = self.refine_loop.refine_attempt(
                    solver=self.solver,
                    executor=self.executor,
                    verifier=self.verifier,
                    reconciler=self.reconciler,
                    problem_text=problem_text,
                    previous_reasoning=self.solver.last_reasoning,
                    previous_code=code,
                    execution_result=cleaned_result,
                    extracted_answer=extracted,
                    mismatch_type=mismatch_type,
                    variables=variables,
                    strategy=strategy
                )
                
                if success:
                    return result
                
                # 실패 시 다음 반복 시도
                while self.refine_loop.can_continue():
                    result, success = self.refine_loop.refine_attempt(...)
                    if success:
                        return result
                
                # 모든 반복 실패 시 루프 리셋
                self.refine_loop.reset()
```

### 2. 환경 변수 설정

```bash
# 최대 반복 횟수 설정 (기본값: 3)
export OMI_REFINE_MAX_ITERATIONS=5

# Refine 루프 비활성화
export OMI_REFINE_ENABLED=false
```

### 3. 직접 사용

```python
from src.pipeline.refine_loop import RefineLoop

# RefineLoop 생성
refine_loop = RefineLoop(max_iterations=3, enable_loop=True)

# Refine 시도
if refine_loop.should_refine(structured_used=True, verified=False):
    result, success = refine_loop.refine_attempt(
        solver=solver,
        executor=executor,
        verifier=verifier,
        reconciler=reconciler,
        problem_text=problem_text,
        previous_reasoning=reasoning,
        previous_code=code,
        execution_result=result,
        extracted_answer=extracted,
        mismatch_type=mismatch_type,
        variables=variables,
        strategy=strategy
    )
    
    if success:
        print(f"Refine 성공: {result['answer']}")
    else:
        print("Refine 실패, 다음 시도...")
```

## 설정 옵션

### RefineLoop 파라미터

- `max_iterations` (int): 최대 반복 횟수 (기본값: 3)
- `enable_loop` (bool): 루프 활성화 여부 (기본값: True)

### 환경 변수

- `OMI_REFINE_MAX_ITERATIONS`: 최대 반복 횟수
- `OMI_REFINE_ENABLED`: 루프 활성화 여부 (true/false)

## 에러 타입별 개선 전략

RefineLoop는 에러 타입에 따라 다른 개선 전략을 사용합니다:

- **format**: 형식 불일치 - 출력 형식만 조정
- **arithmetic**: 산술 오류 - 잘못된 계산 단계 수정
- **logic**: 논리 오류 - PLAN/DERIVATION 수정
- **verification_fail**: 검증 실패 - 최종 계산 수정
- **mismatch**: 불일치 - <ANS>와 실행 결과 정렬
- **other**: 일반 오류 - 최소한의 수정

## 로깅

각 refine 시도는 다음 정보를 로깅합니다:

- `refine`: True
- `refine_iteration`: 반복 횟수
- `strategy`: 전략명 (예: "Path A: The Simulator_refine_1")
- `mismatch_type`: 불일치 타입
- `resource_usage`: 리소스 사용량

## 주의사항

1. **시간 제약**: 각 반복마다 시간이 소요되므로 `time_budget`을 고려해야 합니다.
2. **메모리 사용**: 여러 번의 코드 생성으로 메모리 사용량이 증가할 수 있습니다.
3. **무한 루프 방지**: `max_iterations`로 최대 반복 횟수를 제한합니다.

## 예제

### 예제 1: 기본 사용

```python
from src.pipeline.refine_loop import create_refine_loop

# RefineLoop 생성
refine_loop = create_refine_loop(max_iterations=3)

# 문제 해결 중 검증 실패
if not verified:
    # Refine 시도
    result, success = refine_loop.refine_attempt(...)
    if success:
        return result
```

### 예제 2: 여러 번 시도

```python
refine_loop = RefineLoop(max_iterations=5)

while refine_loop.can_continue():
    result, success = refine_loop.refine_attempt(...)
    if success:
        return result

# 모든 시도 실패
refine_loop.reset()
```

## TODO: Orchestrator 통합

현재 `orchestrator.py`에는 기존의 단일 refine 로직이 있습니다. 
다음 단계로 이를 `RefineLoop`로 교체해야 합니다:

1. `PipelineOrchestrator.__init__()`에 `RefineLoop` 초기화 추가
2. `solve_problem()` 메서드의 refine 로직을 `RefineLoop` 사용으로 교체
3. 테스트 및 검증

## 참고

- `src/pipeline/refine_loop.py`: RefineLoop 구현
- `src/pipeline/reasoning_utils.py`: `build_refine_prompt()` 함수
- `src/pipeline/settings.py`: 설정 관리
