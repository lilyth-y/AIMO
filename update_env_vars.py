"""
환경 변수 이름 변경: AIMO_* → OMI_*
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent

# 변경할 환경 변수
ENV_VAR_MAPPING = {
    "OMI_MODEL": "OMI_MODEL",
    "OMI_QUANTIZATION": "OMI_QUANTIZATION",
}

def update_file(file_path):
    """파일에서 환경 변수 이름 변경"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        for old_var, new_var in ENV_VAR_MAPPING.items():
            # 다양한 패턴으로 변경
            patterns = [
                (rf'\b{old_var}\b', new_var),  # 단독 사용
                (rf'os\.environ\[[\'"]{old_var}[\'"]\]', f'os.environ["{new_var}"]'),
                (rf'os\.environ\.get\([\'"]{old_var}[\'"]', f'os.environ.get("{new_var}"'),
                (rf'os\.environ\.setdefault\([\'"]{old_var}[\'"]', f'os.environ.setdefault("{new_var}"'),
                (rf'export {old_var}=', f'export {new_var}='),
                (rf'\${old_var}', f'${new_var}'),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"  [ERROR] {file_path}: {e}")
        return False

def main():
    """메인 실행"""
    print("="*70)
    print("환경 변수 이름 변경: AIMO_* → OMI_*")
    print("="*70)
    
    updated_files = []
    
    # Python 파일들 검색
    for py_file in ROOT.rglob("*.py"):
        if update_file(py_file):
            updated_files.append(str(py_file.relative_to(ROOT)))
            print(f"  [UPDATED] {py_file.relative_to(ROOT)}")
    
    # README 및 문서 파일들도 업데이트
    for md_file in ROOT.glob("**/*.md"):
        if update_file(md_file):
            updated_files.append(str(md_file.relative_to(ROOT)))
            print(f"  [UPDATED] {md_file.relative_to(ROOT)}")
    
    print(f"\n[SUMMARY] 업데이트된 파일: {len(updated_files)}개")
    
    if updated_files:
        print("\n변경된 환경 변수:")
        for old_var, new_var in ENV_VAR_MAPPING.items():
            print(f"  {old_var} → {new_var}")

if __name__ == "__main__":
    main()
