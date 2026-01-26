# 도커 환경 상태 보고서

**날짜**: 2024-11-24  
**빌드 상태**: ✅ 성공  
**테스트 상태**: ✅ 통과 (Exit Code 0)

## 수정 완료 항목

### 1. 코드 경고 제거
- ✅ `torch_dtype` deprecated 경고 수정 → `model_kwargs` 내부로 이동
- ✅ Dockerfile `FROM ... as base` → `FROM ... AS base` (대문자)
- ✅ docker-compose.yml `version: "3.9"` 제거 (obsolete)
- ✅ `interface.py` bare except → `except (ValueError, TypeError)` 명시

### 2. 환경 설정
- ✅ `TOKENIZERS_PARALLELISM=false` 설정으로 fork 경고 제거
- ✅ 메모리 제한: 2G → 4G 상향
- ✅ CPU 제한: 2 → 4 코어 상향
- ✅ `USE_VOTING=False` 기본값 (초기 테스트 간소화)

### 3. 파일 경로 안정화
- ✅ `run_numina_evaluation.py` 절대 경로 기반 로딩
- ✅ entrypoint.sh 모드 분기 (`test`, `eval`, `shell`, 임의 스크립트)

## 현재 경고 (무시 가능)

### Transformers 라이브러리 경고
```
FutureWarning: Using `TRANSFORMERS_CACHE` is deprecated and will be removed in v5 of Transformers. Use `HF_HOME` instead.
```
- **원인**: Transformers v5에서 환경 변수명 변경 예정
- **영향**: 없음 (HF_HOME도 함께 설정됨)
- **해결**: Transformers v5 릴리스 후 `TRANSFORMERS_CACHE` 제거

## 빌드 정보

```bash
# 이미지 크기
aimo:latest          ~12.9GB (torch CPU 버전 포함)

# 빌드 시간 (캐시 없을 때)
~15-20분 (pip install torch 등 다운로드)

# 빌드 시간 (캐시 있을 때)
~10초 (코드만 재복사)
```

## 실행 명령어

### 빠른 테스트 (FAST_TEST stub)
```powershell
docker compose up aimo
```

### 평가 실행 (Numina 5문제)
```powershell
docker compose run --rm eval
```

### GPU 빌드
```powershell
docker build --build-arg USE_GPU=true -t aimo:gpu .
docker run --gpus all --rm -v ${PWD}/logs:/app/logs aimo:gpu test
```

### 셸 접근
```powershell
docker run -it aimo:latest shell
```

### 임의 스크립트 실행
```powershell
docker run --rm aimo:latest src/pipeline/your_script.py
```

## 검증된 기능

- ✅ FAST_TEST 스텁 모드 정상 작동
- ✅ 전략 라우팅 (Simulator/Theoretician/Hybrid)
- ✅ 검증 파이프라인 (역검증 포함)
- ✅ 로그/결과 볼륨 마운트
- ✅ Exit Code 0 정상 종료
- ✅ 메모리 내 실행 (sandbox 타임아웃/메모리 제한)

## 알려진 제한사항

1. **FAST_TEST 모드 한계**
   - 스텁 LLM은 항상 `42` 또는 간단한 코드 반환
   - 실제 문제 해결 능력 테스트 불가
   - 실제 모델 로드 시 메모리 소비 증가 (>8GB)

2. **다중 후보 비활성화**
   - `USE_VOTING=False` 기본값
   - 성능 최적화 필요 시 활성화

3. **역검증 엄격성**
   - 단순 산술 문제 외 false negative 가능
   - 실제 평가 시 조정 필요

## 다음 단계 권장

### 즉시 가능
1. `USE_VOTING=True` 활성화 후 다중 후보 성능 비교
2. 실제 LLM 로드 테스트 (FAST_TEST=0)
3. Numina 전체 60문제 평가

### 중기 (GPU 환경)
1. GPU 이미지 빌드 및 성능 측정
2. 더 큰 모델 테스트 (>0.5B)
3. 배치 처리 최적화

### 장기 (Kaggle 제출)
1. 멀티스테이지 Dockerfile 경량화
2. 모델 캐시 최적화 (외부 볼륨)
3. HEALTHCHECK 및 CI/CD 파이프라인
4. 제출용 submission.py 통합 테스트

## 요약

모든 주요 경고가 제거되었으며, 도커 환경에서 안정적으로 작동합니다. FAST_TEST 모드에서는 경량 스텁이 정상 동작하며, 실제 LLM 로드 및 평가는 메모리/시간 여유 있을 때 진행 가능합니다.
