# AIMO Reference Problem Evaluation

AIMO Progress Prize 3 참조 문제 5개를 평가하는 스크립트입니다.

## 문제 목록 (reference.csv 기준)

5개의 IMO 수준 문제:

1. **0e644e**: 기하학 - 삼각형의 원과 교점 문제 (답: 336)
2. **26de63**: 수론 - 합 함수와 나머지 문제 (답: 32951)
3. **424e18**: 조합론 - 토너먼트 순위 경우의 수 (답: 21818)
4. **42d360**: 수론 - 진법 변환 최대 이동 횟수 (답: 32193)
5. **641659**: 기하학 - 복잡한 삼각형 원 구성 (답: 57447)

## 실행 방법

### 로컬 실행
```powershell
python run_aimo_evaluation.py
```

### 도커 실행 (FAST_TEST 모드)
```powershell
# FAST_TEST=1: 스텁 LLM, 빠른 파이프라인 검증만
docker compose run --rm -e AIMO_FAST_TEST=1 aimo_reference
```

### 도커 실행 (실제 LLM)
```powershell
# 실제 Qwen2.5-Coder-0.5B 모델 로드 (메모리 16GB 필요)
docker compose run --rm aimo_reference
```

### GPU 실행
```powershell
# GPU 이미지 빌드
docker build --build-arg USE_GPU=true -t aimo:gpu .

# GPU로 실행 (nvidia-docker 필요)
docker run --gpus all --rm \
  -v ${PWD}/logs:/app/logs \
  -v ${PWD}/results:/app/results \
  aimo:gpu aimo
```

## 결과 파일

- `results/aimo_evaluation_results.json`: 상세 결과 JSON
  - 각 문제별 예상/예측 답, 정확도, 시간, 방법론
  - 전체 정확도 통계

## 예상 실행 시간

- **FAST_TEST 모드**: ~10초 (스텁 LLM, 검증 파이프라인만)
- **CPU 모드 (0.5B)**: ~5-10분/문제 (총 25-50분)
- **GPU 모드 (0.5B)**: ~1-2분/문제 (총 5-10분)

## 참고사항

### 난이도
- 모든 문제가 IMO(국제수학올림피아드) 수준
- 현재 파이프라인(0.5B 모델)로는 정확한 해결이 어려움
- 주로 **파이프라인 안정성 테스트** 목적

### 목표
- ✅ 에러 없이 완료 (Exit Code 0)
- ✅ 검증 라우터 정상 작동
- ✅ 로그 생성 확인
- ⚠️ 정확도는 낮을 것으로 예상 (0-20%)

### 개선 방향
1. **더 큰 모델**: 7B+ 모델 (DeepSeekMath, Qwen2.5-Math)
2. **프롬프트 최적화**: IMO 특화 전략 프롬프트
3. **다중 후보 투표**: `USE_VOTING=True` + 더 많은 후보
4. **외부 도구**: SymPy, WolframAlpha API 통합
5. **자가 개선**: Self-refine 루프 활성화

## 데이터 소스

- `data/aimo_problems.jsonl`: 5개 문제 JSONL 형식
- 원본: `C:\Users\USER\Downloads\ai-mathematical-olympiad-progress-prize-3\reference.csv`

## 제출 준비

AIMO 3 Kaggle 제출 형식:
```csv
id,answer
0e644e,336
26de63,32951
...
```

- 답 범위: **0-99999** (5자리 정수)
- 형식: `submission.csv` 또는 `submission.parquet`
- 평가 지표: **정확한 일치** (오차 허용 없음)
