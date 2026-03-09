"""
프로젝트 정리 스크립트
불필요한 파일 삭제 및 디렉토리 구조 정리
"""

import os
import shutil
from pathlib import Path

# 프로젝트 루트
ROOT = Path(__file__).parent

# 삭제할 파일 목록
FILES_TO_DELETE = [
    # 임시 수정 스크립트 (이미 수정 완료)
    "fix_all_encoding.py",
    "fix_encoding.py",
    "fix_line_1106.py",
    "fix_orchestrator_encoding.py",
    "test_list_error_fix.py",
    
    # 로그 파일
    "full_aimo_run.log",
    "run_math7b.log",
    
    # 결과 파일 (새로 생성되므로 삭제 가능)
    "results.jsonl",
    "results_orch.jsonl",
    "results_vanilla.jsonl",
    "generated_queries.json",
    "generated_responses.json",
    
    # 중복 시간 추정 스크립트 (estimate_eval_time.py로 통합)
    "estimate_time.py",
    
    # 중복 테스트 파일 (통합 후 삭제)
    "test_fast_eval.py",  # test_quick_eval.py로 통합
    "test_single_problem.py",  # test_quick_eval.py로 통합
    "test_imo_puzzle.py",  # test_real_imo_puzzle.py로 통합
    "test_puzzle.py",  # test_real_imo_puzzle.py로 통합
    "test_puzzle_prompt.py",  # test_real_imo_puzzle.py로 통합
]

# 이동할 파일 목록 (원본 → 목적지)
FILES_TO_MOVE = {
    # 테스트 파일 → tests/
    "test_evaluation_utils.py": "tests/test_evaluation_utils.py",
    "test_evaluation_scripts.py": "tests/test_evaluation_scripts.py",
    "test_evaluation_mock.py": "tests/test_evaluation_mock.py",
    "test_quick_eval.py": "tests/test_quick_eval.py",
    "test_real_imo_puzzle.py": "tests/test_real_imo_puzzle.py",
    "test_hybrid_engine.py": "tests/test_hybrid_engine.py",
    "test_solver.py": "tests/test_solver.py",
    "test_compromise_point.py": "tests/test_compromise_point.py",
    "system_test.py": "tests/system_test.py",
    "verify_tool_usage.py": "tests/verify_tool_usage.py",
    "kaggle_cred_test.py": "tests/kaggle_cred_test.py",
    
    # 예제 파일 → examples/
    "quick_eval.py": "examples/quick_eval.py",
    "run_aime_evaluation.py": "examples/run_aime_evaluation.py",
    "run_numina_evaluation.py": "examples/run_numina_evaluation.py",
    "run_simple_eval.py": "examples/run_simple_eval.py",
    "quick_test_gpu.py": "examples/quick_test_gpu.py",
    "test_single_problem.py": "examples/test_single_problem.py",
    "geometry_solver.py": "examples/geometry_solver.py",
    "quadratic_solver.py": "examples/quadratic_solver.py",
    "mcp_pipeline_example.py": "examples/mcp_pipeline_example.py",
    "hf_eval_example.py": "examples/hf_eval_example.py",
    "azure_evaluate.py": "examples/azure_evaluate.py",
    "mock_eval.py": "examples/mock_eval.py",
    "manual_evaluation.py": "examples/manual_evaluation.py",
    "evaluate_outputs.py": "examples/evaluate_outputs.py",
    
    # 유틸리티 → scripts/
    "estimate_eval_time.py": "scripts/estimate_eval_time.py",
    "realistic_time_estimate.py": "scripts/realistic_time_estimate.py",
    "convert_to_eval_jsonl.py": "scripts/convert_to_eval_jsonl.py",
    "check_bnb_cuda.py": "scripts/check_bnb_cuda.py",
    "collect_responses.py": "scripts/collect_responses.py",
    "debug_gateway.py": "scripts/debug_gateway.py",
    
    # 문서 → docs/
    "README_AIMO_EVAL.md": "docs/README_AIMO_EVAL.md",
    "README_DOCKER.md": "docs/README_DOCKER.md",
    "README_MODELS.md": "docs/README_MODELS.md",
    "Development_Plan_and_Analysis.md": "docs/Development_Plan_and_Analysis.md",
    "Plan_Review.md": "docs/Plan_Review.md",
    "Report.md": "docs/Report.md",
    "DOCKER_STATUS.md": "docs/DOCKER_STATUS.md",
    "evaluation_report_baseline.md": "docs/evaluation_report_baseline.md",
    "evaluation_report_llm.md": "docs/evaluation_report_llm.md",
    "evaluation_summary.md": "docs/evaluation_summary.md",
}

def create_directories():
    """필요한 디렉토리 생성"""
    dirs = ["tests", "examples", "scripts", "docs", "logs", "results"]
    for dir_name in dirs:
        dir_path = ROOT / dir_name
        dir_path.mkdir(exist_ok=True)
        # __init__.py 파일 생성 (Python 패키지로 인식)
        if dir_name in ["tests", "examples"]:
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text("# Auto-generated\n")
        print(f"[OK] Created directory: {dir_name}/")

def delete_files():
    """불필요한 파일 삭제"""
    deleted = []
    not_found = []
    
    for filename in FILES_TO_DELETE:
        filepath = ROOT / filename
        if filepath.exists():
            try:
                filepath.unlink()
                deleted.append(filename)
                print(f"[DELETED] {filename}")
            except Exception as e:
                print(f"[ERROR] Failed to delete {filename}: {e}")
        else:
            not_found.append(filename)
    
    print(f"\n[SUMMARY] Deleted: {len(deleted)} files")
    if not_found:
        print(f"[INFO] Not found (already deleted?): {len(not_found)} files")
    return deleted

def move_files():
    """파일 이동"""
    moved = []
    not_found = []
    
    for src, dst in FILES_TO_MOVE.items():
        src_path = ROOT / src
        dst_path = ROOT / dst
        
        if src_path.exists():
            try:
                # 목적지 디렉토리 생성
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                # 파일 이동
                shutil.move(str(src_path), str(dst_path))
                moved.append((src, dst))
                print(f"[MOVED] {src} → {dst}")
            except Exception as e:
                print(f"[ERROR] Failed to move {src} to {dst}: {e}")
        else:
            not_found.append(src)
    
    print(f"\n[SUMMARY] Moved: {len(moved)} files")
    if not_found:
        print(f"[INFO] Not found: {len(not_found)} files")
    return moved

def update_gitignore():
    """.gitignore 업데이트"""
    gitignore_path = ROOT / ".gitignore"
    
    additions = [
        "",
        "# Logs and results",
        "*.log",
        "results.jsonl",
        "results_*.jsonl",
        "generated_*.json",
        "",
        "# Temporary files",
        "fix_*.py",
        "*_temp.py",
        "*_backup.py",
    ]
    
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding='utf-8')
        # 이미 추가된 내용인지 확인
        if "*.log" not in content:
            content += "\n" + "\n".join(additions)
            gitignore_path.write_text(content, encoding='utf-8')
            print("[UPDATED] .gitignore")
        else:
            print("[SKIP] .gitignore already updated")
    else:
        print("[WARN] .gitignore not found")

def main():
    """메인 실행 함수"""
    print("="*70)
    print("프로젝트 정리 시작")
    print("="*70)
    
    # 1. 디렉토리 생성
    print("\n[1/4] Creating directories...")
    create_directories()
    
    # 2. 파일 삭제
    print("\n[2/4] Deleting unnecessary files...")
    deleted = delete_files()
    
    # 3. 파일 이동
    print("\n[3/4] Moving files to appropriate directories...")
    moved = move_files()
    
    # 4. .gitignore 업데이트
    print("\n[4/4] Updating .gitignore...")
    update_gitignore()
    
    # 요약
    print("\n" + "="*70)
    print("정리 완료!")
    print("="*70)
    print(f"삭제된 파일: {len(deleted)}개")
    print(f"이동된 파일: {len(moved)}개")
    print("\n다음 단계:")
    print("1. git status로 변경사항 확인")
    print("2. 필요한 경우 import 경로 수정")
    print("3. 테스트 실행하여 정상 작동 확인")

if __name__ == "__main__":
    import sys
    # 명령줄 인자로 --yes가 있으면 자동 실행
    if len(sys.argv) > 1 and sys.argv[1] == '--yes':
        main()
    else:
        print("프로젝트 정리 스크립트")
        print("실행하려면: python cleanup_project.py --yes")
        print("\n또는 직접 확인 후 실행:")
        print("1. project_cleanup_analysis.md 파일 확인")
        print("2. cleanup_plan.md 파일 확인")
        print("3. python cleanup_project.py --yes 실행")
