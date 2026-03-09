"""
프로젝트 이름 변경 스크립트
AIMO → MathCodeOrchestrator (또는 다른 이름)
"""

import os
import re
from pathlib import Path

ROOT = Path(__file__).parent

# 새 프로젝트 이름 설정
NEW_NAME = "OMI"  # Orchestrated Math Interpreter
FULL_NAME = "Orchestrated Math Interpreter"  # 전체 이름
OLD_NAME = "AIMO"
OLD_NAME_LOWER = "aimo"

# 환경 변수 이름도 변경할지 결정
RENAME_ENV_VARS = True  # MATHCODEORCHESTRATOR_MODEL → MCO_MODEL 등

def rename_in_file(file_path, old_text, new_text):
    """파일 내용에서 텍스트 교체"""
    try:
        content = file_path.read_text(encoding='utf-8')
        if old_text in content:
            new_content = content.replace(old_text, new_text)
            file_path.write_text(new_content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"  [ERROR] {file_path}: {e}")
        return False

def rename_files_and_content():
    """파일 이름과 내용 변경"""
    changes = []
    
    # 1. README.md 업데이트
    readme_path = ROOT / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding='utf-8')
        new_content = content.replace(f"# {OLD_NAME}", f"# {NEW_NAME}")
        new_content = new_content.replace(f"{OLD_NAME}는", f"{NEW_NAME}는")
        new_content = new_content.replace(f"{OLD_NAME}/", f"{NEW_NAME}/")
        readme_path.write_text(new_content, encoding='utf-8')
        changes.append("README.md")
        print(f"[UPDATED] README.md")
    
    # 2. 문서 파일들 업데이트
    doc_files = list(ROOT.glob("docs/**/*.md"))
    for doc_file in doc_files:
        if rename_in_file(doc_file, OLD_NAME, NEW_NAME):
            changes.append(str(doc_file.relative_to(ROOT)))
    
    # 3. 환경 변수 이름 변경 (선택적)
    if RENAME_ENV_VARS:
        env_var_mapping = {
            "OMI_MODEL": f"{NEW_NAME}_MODEL",  # OMI_MODEL
            "OMI_QUANTIZATION": f"{NEW_NAME}_QUANTIZATION",  # OMI_QUANTIZATION
        }
        
        for old_var, new_var in env_var_mapping.items():
            # Python 파일들에서 환경 변수 이름 변경
            for py_file in ROOT.rglob("*.py"):
                if rename_in_file(py_file, old_var, new_var):
                    changes.append(f"{py_file.relative_to(ROOT)} (env var)")
    
    return changes

def update_project_description():
    """프로젝트 설명 업데이트"""
    readme_path = ROOT / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding='utf-8')
        
        # 프로젝트 설명 업데이트
        new_description = f"""{FULL_NAME} (OMI)는 수학 문제를 체계적으로 오케스트레이션하고 코드로 해석하여 실행하는 AI 시스템입니다.

## 핵심 개념

- **Math Orchestration**: 수학 문제를 단계별로 분석하고 최적의 해결 전략을 조율
- **Code Interpreter**: 생성된 Python 코드를 실행하여 정확한 답을 도출

## 주요 특징

- 5-Stage Pipeline을 통한 체계적인 문제 해결
- 다중 전략 지원 (Simulator, Theoretician, Hybrid)
- 코드 생성 및 실행을 통한 정확한 계산
"""
        
        # 기존 설명 부분 찾아서 교체
        content = re.sub(
            r'# .*?\n\n\*\*PD 학기제 프로젝트\*\*\n\n.*?수학 올림피아드 문제를 해결하기 위한 AI 시스템입니다\.',
            f'# {NEW_NAME}\n\n**PD 학기제 프로젝트**\n\n{new_description.strip()}',
            content,
            flags=re.DOTALL
        )
        
        readme_path.write_text(content, encoding='utf-8')
        print(f"[UPDATED] 프로젝트 설명")

def main():
    """메인 실행"""
    print("="*70)
    print(f"프로젝트 이름 변경: {OLD_NAME} → {NEW_NAME}")
    print("="*70)
    
    print(f"\n새 이름: {NEW_NAME} ({FULL_NAME})")
    print(f"의미: Math Orchestration + Code Interpreter")
    print(f"\n변경할 내용:")
    print(f"  - README.md")
    print(f"  - 문서 파일들")
    if RENAME_ENV_VARS:
        print(f"  - 환경 변수 이름 (AIMO_* → {NEW_NAME}_*)")
    
    # 자동 실행 (--yes 옵션 또는 직접 실행)
    import sys
    if len(sys.argv) > 1 and sys.argv[1] != '--yes':
        response = input("\n계속하시겠습니까? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("취소되었습니다.")
            return
    
    # 1. 파일 내용 변경
    print("\n[1/2] 파일 내용 변경 중...")
    changes = rename_files_and_content()
    print(f"  변경된 파일: {len(changes)}개")
    
    # 2. 프로젝트 설명 업데이트
    print("\n[2/2] 프로젝트 설명 업데이트 중...")
    update_project_description()
    
    print("\n" + "="*70)
    print("이름 변경 완료!")
    print("="*70)
    print(f"\n새 프로젝트 이름: {NEW_NAME} ({FULL_NAME})")
    print(f"의미: Math Orchestration + Code Interpreter")
    print("\n참고:")
    print("  - 디렉토리 이름은 수동으로 변경해야 할 수 있습니다")
    print("  - Git 저장소 이름도 변경을 고려하세요")

if __name__ == "__main__":
    main()
