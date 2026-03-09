"""
테스트 실행 스크립트
모든 테스트를 실행하고 커버리지를 측정합니다.
"""

import sys
import os
import subprocess
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests():
    """모든 테스트 실행"""
    print("=" * 70)
    print("테스트 실행 및 커버리지 측정")
    print("=" * 70)
    
    # 테스트 디렉토리
    test_dir = Path(__file__).parent
    
    # pytest 명령어 구성
    cmd = [
        "pytest",
        str(test_dir),
        "-v",  # verbose
        "--tb=short",  # 짧은 traceback
        "--cov=src",  # src 디렉토리 커버리지
        "--cov-report=term-missing",  # 터미널에 누락된 라인 표시
        "--cov-report=html",  # HTML 리포트 생성
        "--cov-report=xml",  # XML 리포트 생성
    ]
    
    # 특정 테스트 파일만 실행하려면
    if len(sys.argv) > 1:
        test_files = sys.argv[1:]
        cmd.extend(test_files)
    
    print(f"\n실행 명령: {' '.join(cmd)}\n")
    
    # 테스트 실행
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ 모든 테스트 통과!")
        print("=" * 70)
        print("\n커버리지 리포트:")
        print(f"  - HTML: {project_root / 'htmlcov' / 'index.html'}")
        print(f"  - XML: {project_root / 'coverage.xml'}")
    else:
        print("\n" + "=" * 70)
        print("❌ 일부 테스트 실패")
        print("=" * 70)
    
    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
