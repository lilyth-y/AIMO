# 프로젝트 구조 정리 가이드 (PD 학기제)

## 현재 프로젝트 구조 분석

### 문제점

프로젝트에 여러 버전/목적의 디렉토리가 혼재되어 있어 혼란스러움:

- `MathCodeOrchestrator_core/` - 코어 프로젝트?
- `MathCodeOrchestrator3_Project/` - MathCodeOrchestrator3 프로젝트?
- `archive/` - 아카이브?
- `kaggle_evaluation/` - Kaggle 평가?
- `src/` - 메인 소스?

## 각 디렉토리 목적 파악

### 1. MathCodeOrchestrator_core/

**목적**: 초기 코어 프로젝트 또는 별도 버전
**내용**: 

- Kaggle 관련 스크립트
- 모델 다운로드 스크립트
- 별도의 파이프라인 구현

**권장 조치**:

- 메인 프로젝트와 통합 또는
- `archive/legacy/`로 이동

### 2. MathCodeOrchestrator3_Project/

**목적**: MathCodeOrchestrator3 관련 프로젝트 문서/리포트
**내용**:

- Report.md
- TODO.md

**권장 조치**:

- `docs/MathCodeOrchestrator3/`로 이동하여 문서화

### 3. archive/

**목적**: 아카이브된 파일들
**내용**: 확인 필요

**권장 조치**:

- 유지 (아카이브는 그대로)

### 4. kaggle_evaluation/

**목적**: Kaggle 평가 관련 코드
**내용**:

- gRPC 게이트웨이
- 평가 서버

**권장 조치**:

- `src/kaggle/`로 이동 또는
- `examples/kaggle/`로 이동

### 5. src/

**목적**: 메인 소스 코드
**내용**:

- pipeline/
- evaluation/
- data/

**권장 조치**:

- 메인 소스로 유지

## PD 학기제 프로젝트 구조 제안

### 옵션 1: 단일 프로젝트 구조 (권장)

```
MathCodeOrchestrator/
├── src/                    # 메인 소스 코드
├── examples/              # 예제
├── tests/                 # 테스트
├── scripts/               # 유틸리티
├── docs/                  # 문서
│   ├── MathCodeOrchestrator3/            # MathCodeOrchestrator3 프로젝트 문서
│   └── ...
├── data/                  # 데이터
├── archive/               # 아카이브 (유지)
└── legacy/                # 레거시 코드 (MathCodeOrchestrator_core 이동)
```

### 옵션 2: 버전별 분리

```
MathCodeOrchestrator/
├── core/                  # 현재 메인 (src/ 내용)
├── aimo3/                 # MathCodeOrchestrator3 프로젝트
│   ├── src/
│   └── docs/
├── legacy/                # MathCodeOrchestrator_core
└── archive/              # 아카이브
```

## 정리 방안

### 즉시 실행 가능한 정리

1. **MathCodeOrchestrator3_Project → docs/MathCodeOrchestrator3/**
  - Report.md, TODO.md를 docs/MathCodeOrchestrator3/로 이동
2. **MathCodeOrchestrator_core → archive/legacy/ 또는 삭제**
  - 사용하지 않는다면 archive로 이동
  - 사용 중이라면 src/와 통합
3. **kaggle_evaluation → src/kaggle/**
  - Kaggle 관련 코드를 src/ 하위로 이동
4. **문서화**
  - 각 디렉토리의 목적을 README에 명시

## 권장사항

**PD 학기제 프로젝트**이므로:

1. **명확한 구조**: 평가자가 쉽게 이해할 수 있도록
2. **문서화**: 각 디렉토리의 목적과 사용법 명시
3. **정리**: 불필요한 중복 제거
4. **일관성**: 하나의 메인 프로젝트 구조 유지

