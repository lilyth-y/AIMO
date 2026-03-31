# AIMO Progress Prize 참조 문제 평가 (개요)

AIMO Progress Prize 3 **참조(reference) 문제 5개**를 다루는 문서이다. 로컬 경로·도커 명은 현재 레포의 [`compose.yml`](../../compose.yml)·[`entrypoint.sh`](../../entrypoint.sh) 와 맞춘다.

## 문제 목록 (reference.csv 기준)

5개의 IMO 수준 문제:

1. **0e644e**: 기하학 - 삼각형의 원과 교점 문제 (답: 336)
2. **26de63**: 수론 - 합 함수와 나머지 문제 (답: 32951)
3. **424e18**: 조합론 - 토너먼트 순위 경우의 수 (답: 21818)
4. **42d360**: 수론 - 진법 변환 최대 이동 횟수 (답: 32193)
5. **641659**: 기하학 - 복잡한 삼각형 원 구성 (답: 57447)

## 실행 방법

### 일반 평가 (Numina 균형 세트 등)

모델·양자화는 [`README_MODELS.md`](README_MODELS.md) 와 `src/pipeline/settings.py` 기준이다.

```powershell
python examples/run_numina_evaluation.py
```

### 참조 5문항 전용 스크립트와 Docker

프로젝트 루트의 [`run_aimo_evaluation.py`](../../run_aimo_evaluation.py)가 JSONL(`archive/legacy/AIMO_core/data/aimo_problems.jsonl`, 또는 `AIMO_REFERENCE_JSONL`)을 읽어 평가한다. `entrypoint.sh`의 `aimo` 모드가 이 파일을 호출한다.

### 도커 실행 (FAST_TEST 모드)

`AIMO_FAST_TEST=1`: 스텁·빠른 파이프라인 검증 등 (`settings.fast_test`). Compose 예시는 `compose.yml`의 `aimo` 서비스를 본다.

```powershell
docker compose run --rm -e AIMO_FAST_TEST=1 aimo_reference
```

### 도커 실행 (실제 LLM)

메모리·캐시는 `compose.yml`의 볼륨 설정을 따른다.

```powershell
docker compose run --rm aimo_reference
```

### GPU 실행

```powershell
docker build --build-arg USE_GPU=true -t aimo:gpu .

docker run --gpus all --rm `
  -v ${PWD}/logs:/app/logs `
  -v ${PWD}/results:/app/results `
  aimo:gpu aimo
```

## 결과 파일

- `results/` 아래 JSON 등 (스크립트별 상이)
  - 각 문제별 예측 답, 시간, 방법론 등

## 예상 실행 시간

- **FAST_TEST 모드**: 매우 짧음 (스텁·최소 경로)
- **CPU / 소형 모델**: 문제당 수 분~수십 분
- **GPU**: 상대적으로 단축

## 참고사항

### 난이도

- 문제는 IMO 수준
- 소형 모델로는 정확한 해법이 어려울 수 있으며, **파이프라인·안정성 검증** 목적에 가깝다

### 개선 방향

1. 더 큰 수학 특화 모델 (`README_MODELS.md` 참고)
2. IMO 특화 프롬프트·라우팅
3. 다중 후보·투표 (`OMI_USE_VOTING` 등, `settings.py`)
4. 외부 도구(SymPy 등) 연동
5. Self-refine (`OMI_REFINE_*`, `refine_loop.py`)

## 데이터 소스

- 과거 레이아웃: `data/aimo_problems.jsonl` (일부는 `archive/` 참고)
- 원본 대회: `reference.csv` (Kaggle 데이터 패키지)

## 제출 준비

AIMO Progress Prize 3 제출 형식 예:

```csv
id,answer
0e644e,336
26de63,32951
...
```

- 답 범위: **0–99999** (5자리 정수)
- 형식: `submission.csv` 또는 `submission.parquet`
- 평가: 정확 일치
