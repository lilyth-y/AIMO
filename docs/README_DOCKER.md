# Docker 실행 가이드

## 1. 빌드

CPU 기본:

```bash
docker build -t aimo:cpu .
```

GPU (CUDA 12.1 기반 Torch 설치):

```bash
docker build --build-arg USE_GPU=true -t aimo:gpu .
```

## 2. 실행 (단일 컨테이너)

```bash
docker run --rm -it -v $(pwd)/logs:/app/logs -v $(pwd)/results:/app/results aimo:cpu python test_solver.py
```

## 3. docker-compose

```bash
docker compose up --build aimo
```

평가 실행:

```bash
docker compose run --rm eval
```

## 4. 캐시/성능

모델/토크나이저 캐시는 `/app/.cache/huggingface` 에 저장되며 볼륨 마운트로 재사용 가능:

```bash
docker run -v $(pwd)/hf_cache:/app/.cache/huggingface aimo:cpu python test_solver.py
```

## 5. 주의 사항

- `requirements.txt` 에 torch CPU 설치 플래그가 있으므로 GPU 빌드 시 Dockerfile ARG로 덮어씁니다.
- 추후 대형 모델 사용 시 이미지 크기 증가 방지를 위해 모델을 런타임 다운로드 후 외부 캐시 볼륨 사용 권장.
- `MathCodeOrchestrator_FAST_TEST=1` 환경변수는 빠른 개발 모드를 활성화.

## 6. 향후 개선

- 멀티스테이지 경량화 (빌드 의존성 제거)
- HEALTHCHECK 추가
- 평가 스케줄러 서비스 분리
- 프라이빗 레지스트리 푸시 자동화 (CI/CD)
