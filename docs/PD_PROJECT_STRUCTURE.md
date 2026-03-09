# PD 학기제 프로젝트 구조

## 프로젝트 개요
이 프로젝트는 MathCodeOrchestrator (AI Math Olympiad) 문제 해결을 위한 AI 시스템입니다.

## 디렉토리 구조

### 메인 소스 코드
- `src/` - 메인 소스 코드
  - `pipeline/` - 5-Stage 파이프라인
  - `evaluation/` - 평가 유틸리티
  - `data/` - 데이터 로더
  - `kaggle/` - Kaggle 평가 관련 코드

### 예제 및 테스트
- `examples/` - 예제 스크립트
- `tests/` - 테스트 파일
- `scripts/` - 유틸리티 스크립트

### 문서
- `docs/` - 프로젝트 문서
  - `MathCodeOrchestrator3/` - MathCodeOrchestrator3 프로젝트 리포트 및 문서

### 데이터 및 결과
- `data/` - 데이터 파일
- `logs/` - 로그 파일 (gitignore)
- `results/` - 결과 파일 (gitignore)

### 아카이브
- `archive/` - 아카이브된 레거시 코드
  - `legacy/MathCodeOrchestrator_core/` - 초기 코어 프로젝트

## 주요 파일

### 실행 스크립트
- `examples/quick_eval.py` - 빠른 평가
- `examples/run_aime_evaluation.py` - AIME 평가
- `examples/run_numina_evaluation.py` - NuminaMath 평가

### 문서
- `docs/MathCodeOrchestrator3/Report.md` - MathCodeOrchestrator3 프로젝트 리포트
- `docs/PROJECT_STRUCTURE.md` - 상세 프로젝트 구조
- `README.md` - 메인 README

## 사용 방법

### 빠른 시작
```bash
# 의존성 설치
pip install -r requirements.txt

# 데이터셋 설정
python scripts/setup_numina_dataset.py

# 빠른 평가
python examples/quick_eval.py
```

자세한 내용은 [README.md](../README.md)를 참조하세요.
