"""
PD 학기제 프로젝트 구조 정리 (한 번 실행용)
각 디렉토리의 목적을 명확히 하고 정리합니다.
실행: 프로젝트 루트에서 python scripts/organize_pd_project.py
"""

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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
        
        try:
            aimo3_src.rmdir()
            print("  [DELETED] AIMO3_Project/ (빈 디렉토리)")
        except Exception:
            print("  [WARN] AIMO3_Project/ 디렉토리 삭제 실패")
    
    # 2. kaggle_evaluation → src/kaggle/로 이동
    print("\n[2/5] kaggle_evaluation 코드 이동...")
    kaggle_src = ROOT / "kaggle_evaluation"
    kaggle_dst = ROOT / "src" / "kaggle"
    
    if kaggle_src.exists():
        if kaggle_dst.exists():
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
        try:
            kaggle_src.rmdir()
        except Exception:
            pass
    
    # 3. AIMO_core → archive/legacy/로 이동
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
    
    # 4. 구조 문서는 docs/README.md 기준으로 이미 정리됨
    print("\n[4/5] 프로젝트 구조 문서는 docs/README.md 참고.")
    
    # 5. 최종 상태 확인
    print("\n[5/5] 최종 구조 확인...")
    main_dirs = ['src', 'examples', 'tests', 'scripts', 'docs', 'data', 'archive']
    for dir_name in main_dirs:
        dir_path = ROOT / dir_name
        if dir_path.exists():
            print(f"  [OK] {dir_name}/")
    
    print("\n" + "="*70)
    print("정리 완료!")
    print("="*70)

if __name__ == "__main__":
    organize_pd_project()
