"""
최종 정리: 남은 파일들 정리 및 import 경로 수정
"""

import os
import shutil
import re
from pathlib import Path

ROOT = Path(__file__).parent

# 추가로 이동할 파일들
ADDITIONAL_MOVES = {
    # 데이터/결과 파일 → data/ 또는 삭제 대상
    "eval_data.jsonl": "data/eval_data.jsonl",
    "evaluation_output.txt": None,  # 삭제 (gitignore)
    "evaluation_results.csv": None,  # 삭제 (gitignore)
    "generated_problems.csv": None,  # 삭제 (gitignore)
    "mcp_results.json": None,  # 삭제 (gitignore)
    "mock_eval_results.json": None,  # 삭제 (gitignore)
    "test.csv": None,  # 삭제 (gitignore)
    
    # 문서 → docs/
    "cleanup_plan.md": "docs/cleanup_plan.md",
    "CLEANUP_SUMMARY.md": "docs/CLEANUP_SUMMARY.md",
    "project_cleanup_analysis.md": "docs/project_cleanup_analysis.md",
    "TODO.md": "docs/TODO.md",
    
    # 스크립트 → scripts/
    "setup_numina_dataset.py": "scripts/setup_numina_dataset.py",
}

def fix_import_paths():
    """이동된 파일들의 import 경로 수정"""
    fixes = []
    
    # examples/quick_eval.py 경로 수정
    quick_eval_path = ROOT / "examples" / "quick_eval.py"
    if quick_eval_path.exists():
        content = quick_eval_path.read_text(encoding='utf-8')
        original = content
        
        # project_root 경로 수정 (examples/에서 상위로)
        content = re.sub(
            r'project_root = os\.path\.dirname\(__file__\)',
            "project_root = os.path.dirname(os.path.dirname(__file__))",
            content
        )
        
        if content != original:
            quick_eval_path.write_text(content, encoding='utf-8')
            fixes.append("examples/quick_eval.py")
    
    # examples/run_*.py 파일들도 수정
    for example_file in ["run_aime_evaluation.py", "run_numina_evaluation.py", "run_simple_eval.py"]:
        example_path = ROOT / "examples" / example_file
        if example_path.exists():
            content = example_path.read_text(encoding='utf-8')
            original = content
            
            # sys.path.append('src') → sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
            content = re.sub(
                r"sys\.path\.append\('src'\)",
                "sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))",
                content
            )
            content = re.sub(
                r"sys\.path\.insert\(0, os\.path\.join\(os\.path\.dirname\(__file__\), 'src'\)\)",
                "sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))",
                content
            )
            
            if content != original:
                example_path.write_text(content, encoding='utf-8')
                fixes.append(f"examples/{example_file}")
    
    # tests/ 파일들 경로 수정
    for test_file in ["test_evaluation_utils.py", "test_evaluation_scripts.py", "test_quick_eval.py"]:
        test_path = ROOT / "tests" / test_file
        if test_path.exists():
            content = test_path.read_text(encoding='utf-8')
            original = content
            
            # 경로 수정
            content = re.sub(
                r"sys\.path\.insert\(0, os\.path\.join\(os\.path\.dirname\(__file__\), 'src'\)\)",
                "sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))",
                content
            )
            content = re.sub(
                r"sys\.path\.insert\(0, os\.path\.dirname\(__file__\)\)",
                "sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))",
                content
            )
            
            if content != original:
                test_path.write_text(content, encoding='utf-8')
                fixes.append(f"tests/{test_file}")
    
    return fixes

def move_additional_files():
    """추가 파일들 이동 또는 삭제"""
    moved = []
    deleted = []
    
    for src, dst in ADDITIONAL_MOVES.items():
        src_path = ROOT / src
        
        if not src_path.exists():
            continue
        
        if dst is None:
            # 삭제
            try:
                src_path.unlink()
                deleted.append(src)
                print(f"[DELETED] {src}")
            except Exception as e:
                print(f"[ERROR] Failed to delete {src}: {e}")
        else:
            # 이동
            dst_path = ROOT / dst
            try:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src_path), str(dst_path))
                moved.append((src, dst))
                print(f"[MOVED] {src} → {dst}")
            except Exception as e:
                print(f"[ERROR] Failed to move {src} to {dst}: {e}")
    
    return moved, deleted

def create_data_dir():
    """data/ 디렉토리 생성"""
    data_dir = ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    print(f"[OK] Created/verified data/ directory")

def update_gitignore_final():
    """최종 .gitignore 업데이트"""
    gitignore_path = ROOT / ".gitignore"
    
    additions = [
        "",
        "# Data and result files",
        "*.csv",
        "*.jsonl",
        "*.json",
        "!requirements.txt",
        "!package.json",
        "evaluation_output.txt",
        "mcp_results.json",
        "mock_eval_results.json",
        "test.csv",
    ]
    
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding='utf-8')
        if "evaluation_output.txt" not in content:
            content += "\n" + "\n".join(additions)
            gitignore_path.write_text(content, encoding='utf-8')
            print("[UPDATED] .gitignore with data files")
        else:
            print("[SKIP] .gitignore already updated")

def main():
    """메인 실행"""
    print("="*70)
    print("최종 정리 작업")
    print("="*70)
    
    # 1. data/ 디렉토리 생성
    print("\n[1/4] Creating data directory...")
    create_data_dir()
    
    # 2. 추가 파일 이동/삭제
    print("\n[2/4] Moving/deleting additional files...")
    moved, deleted = move_additional_files()
    
    # 3. Import 경로 수정
    print("\n[3/4] Fixing import paths...")
    fixes = fix_import_paths()
    
    # 4. .gitignore 최종 업데이트
    print("\n[4/4] Final .gitignore update...")
    update_gitignore_final()
    
    # 요약
    print("\n" + "="*70)
    print("최종 정리 완료!")
    print("="*70)
    print(f"이동된 파일: {len(moved)}개")
    print(f"삭제된 파일: {len(deleted)}개")
    print(f"수정된 파일: {len(fixes)}개")
    if fixes:
        print("\n수정된 파일 목록:")
        for f in fixes:
            print(f"  - {f}")

if __name__ == "__main__":
    main()
