"""
프로젝트 이름 변경 스크립트 (한 번 실행용)
AIMO → OMI 등. 실행: 프로젝트 루트에서 python scripts/rename_project.py
"""

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 새 프로젝트 이름 설정
NEW_NAME = "OMI"
FULL_NAME = "Orchestrated Math Interpreter"
OLD_NAME = "AIMO"
OLD_NAME_LOWER = "aimo"
RENAME_ENV_VARS = True

def rename_in_file(file_path, old_text, new_text):
    try:
        content = file_path.read_text(encoding='utf-8')
        if old_text in content:
            file_path.write_text(content.replace(old_text, new_text), encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"  [ERROR] {file_path}: {e}")
        return False

def rename_files_and_content():
    changes = []
    readme_path = ROOT / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding='utf-8')
        new_content = content.replace(f"# {OLD_NAME}", f"# {NEW_NAME}").replace(f"{OLD_NAME}는", f"{NEW_NAME}는").replace(f"{OLD_NAME}/", f"{NEW_NAME}/")
        readme_path.write_text(new_content, encoding='utf-8')
        changes.append("README.md")
    for doc_file in ROOT.glob("docs/**/*.md"):
        if rename_in_file(doc_file, OLD_NAME, NEW_NAME):
            changes.append(str(doc_file.relative_to(ROOT)))
    if RENAME_ENV_VARS:
        for py_file in ROOT.rglob("*.py"):
            if rename_in_file(py_file, "OMI_MODEL", f"{NEW_NAME}_MODEL") or rename_in_file(py_file, "OMI_QUANTIZATION", f"{NEW_NAME}_QUANTIZATION"):
                changes.append(str(py_file.relative_to(ROOT)))
    return changes

def main():
    print("="*70)
    print(f"프로젝트 이름 변경: {OLD_NAME} → {NEW_NAME}")
    print("="*70)
    changes = rename_files_and_content()
    print(f"  변경된 파일: {len(changes)}개")
    print("="*70)

if __name__ == "__main__":
    main()
