"""
PD 학기제 프로젝트 구조 정리
각 디렉토리의 목적을 명확히 하고 정리합니다.
"""

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent

def organize_pd_project():
    """PD 학기제 프로젝트 구조 정리"""
    
    print("="*70)
    print("PD 학기제 프로젝트 구조 정리")
    print("="*70)
    
    # 1. AIMO3_Project → docs/AIMO3/로 이동
    print("\n[1/5] AIMO3_Project 문서 이동...")
    aimo3_src = ROOT / "AIMO3_Project"
    aimo3_dst = ROOT / "docs" / "AIMO3"
    
    if aimo3_src.exists():
        aimo3_dst.mkdir(parents=True, exist_ok=True)
        for file in aimo3_src.iterdir():
            if file.is_file():
                shutil.move(str(file), str(aimo3_dst / file.name))
                print(f"  [MOVED] {file.name} → docs/AIMO3/")
        
        # 빈 디렉토리 삭제
        try:
            aimo3_src.rmdir()
            print("  [DELETED] AIMO3_Project/ (빈 디렉토리)")
        except:
            print("  [WARN] AIMO3_Project/ 디렉토리 삭제 실패")
    
    # 2. kaggle_evaluation → src/kaggle/로 이동
    print("\n[2/5] kaggle_evaluation 코드 이동...")
    kaggle_src = ROOT / "kaggle_evaluation"
    kaggle_dst = ROOT / "src" / "kaggle"
    
    if kaggle_src.exists():
        if kaggle_dst.exists():
            # 기존 파일과 병합
            for item in kaggle_src.iterdir():
                dst_item = kaggle_dst / item.name
                if item.is_file():
                    if not dst_item.exists():
                        shutil.move(str(item), str(dst_item))
                        print(f"  [MOVED] {item.name} → src/kaggle/")
                    else:
                        print(f"  [SKIP] {item.name} (이미 존재)")
                elif item.is_dir():
                    if not dst_item.exists():
                        shutil.move(str(item), str(dst_item))
                        print(f"  [MOVED] {item.name}/ → src/kaggle/")
                    else:
                        print(f"  [SKIP] {item.name}/ (이미 존재)")
        else:
            shutil.move(str(kaggle_src), str(kaggle_dst))
            print(f"  [MOVED] kaggle_evaluation/ → src/kaggle/")
        
        # 빈 디렉토리 삭제
        try:
            kaggle_src.rmdir()
        except:
            pass
    
    # 3. AIMO_core → archive/legacy/로 이동 (레거시로 보관)
    print("\n[3/5] AIMO_core 레거시 아카이브...")
    aimo_core_src = ROOT / "AIMO_core"
    aimo_core_dst = ROOT / "archive" / "legacy" / "AIMO_core"
    
    if aimo_core_src.exists():
        aimo_core_dst.parent.mkdir(parents=True, exist_ok=True)
        if not aimo_core_dst.exists():
            shutil.move(str(aimo_core_src), str(aimo_core_dst))
            print(f"  [MOVED] AIMO_core/ → archive/legacy/AIMO_core/")
        else:
            print(f"  [SKIP] AIMO_core/ (이미 archive에 존재)")
    
    # 4. README 업데이트를 위한 구조 문서 생성
    print("\n[4/5] 프로젝트 구조 문서 생성...")
    structure_doc = ROOT / "docs" / "PD_PROJECT_STRUCTURE.md"
    structure_doc.write_text("""# PD 학기제 프로젝트 구조

## 프로젝트 개요
이 프로젝트는 AIMO (AI Math Olympiad) 문제 해결을 위한 AI 시스템입니다.

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
  - `AIMO3/` - AIMO3 프로젝트 리포트 및 문서

### 데이터 및 결과
- `data/` - 데이터 파일
- `logs/` - 로그 파일 (gitignore)
- `results/` - 결과 파일 (gitignore)

### 아카이브
- `archive/` - 아카이브된 레거시 코드
  - `legacy/AIMO_core/` - 초기 코어 프로젝트

## 주요 파일

### 실행 스크립트
- `examples/quick_eval.py` - 빠른 평가
- `examples/run_aime_evaluation.py` - AIME 평가
- `examples/run_numina_evaluation.py` - NuminaMath 평가

### 문서
- `docs/AIMO3/Report.md` - AIMO3 프로젝트 리포트
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
""", encoding='utf-8')
    print(f"  [CREATED] docs/PD_PROJECT_STRUCTURE.md")
    
    # 5. 최종 상태 확인
    print("\n[5/5] 최종 구조 확인...")
    main_dirs = ['src', 'examples', 'tests', 'scripts', 'docs', 'data', 'archive']
    for dir_name in main_dirs:
        dir_path = ROOT / dir_name
        if dir_path.exists():
            file_count = len(list(dir_path.rglob('*.py'))) if dir_name != 'docs' else len(list(dir_path.glob('*.md')))
            print(f"  [OK] {dir_name}/ ({file_count} files)")
    
    print("\n" + "="*70)
    print("정리 완료!")
    print("="*70)
    print("\n정리된 구조:")
    print("  - AIMO3_Project/ → docs/AIMO3/")
    print("  - kaggle_evaluation/ → src/kaggle/")
    print("  - AIMO_core/ → archive/legacy/AIMO_core/")
    print("\n이제 프로젝트 구조가 명확해졌습니다!")

if __name__ == "__main__":
    organize_pd_project()
