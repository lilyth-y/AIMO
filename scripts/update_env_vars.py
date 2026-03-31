"""
환경 변수 이름 일괄 변경 (한 번 실행용)
실행: 프로젝트 루트에서 python scripts/update_env_vars.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ENV_VAR_MAPPING = {
    "OMI_MODEL": "OMI_MODEL",
    "OMI_QUANTIZATION": "OMI_QUANTIZATION",
}

def update_file(file_path):
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        for old_var, new_var in ENV_VAR_MAPPING.items():
            content = re.sub(rf'\b{old_var}\b', new_var, content)
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"  [ERROR] {file_path}: {e}")
        return False

def main():
    print("="*70)
    print("환경 변수 이름 변경")
    print("="*70)
    updated = []
    for py_file in ROOT.rglob("*.py"):
        if update_file(py_file):
            updated.append(str(py_file.relative_to(ROOT)))
    for md_file in ROOT.glob("**/*.md"):
        if update_file(md_file):
            updated.append(str(md_file.relative_to(ROOT)))
    print(f"  업데이트된 파일: {len(updated)}개")
    print("="*70)

if __name__ == "__main__":
    main()
