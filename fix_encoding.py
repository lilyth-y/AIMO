"""인코딩 문제 수정 스크립트"""
import re

with open('src/pipeline/orchestrator.py', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')

# 338줄의 깨진 문자 수정
content = re.sub(
    r'print\("   -> \?\?\? Self-Refine Attempt\.\.\."\)',
    'print("   -> [INFO] Self-Refine Attempt...")',
    content
)

# 다른 깨진 문자들도 확인
content = re.sub(r'\?\?\?', '[INFO]', content)

with open('src/pipeline/orchestrator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed encoding issues in orchestrator.py")
