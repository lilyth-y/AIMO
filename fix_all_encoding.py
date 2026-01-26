"""orchestrator.py의 모든 인코딩 문제 수정"""
import re

with open('src/pipeline/orchestrator.py', 'rb') as f:
    content_bytes = f.read()

content = content_bytes.decode('utf-8', errors='replace')

# 모든 깨진 특수 문자 패턴 찾아서 수정
patterns = [
    (r'print\("   -> \?\?\?.*?Self-Refine Attempt\.\.\."\)', 'print("   -> [INFO] Self-Refine Attempt...")'),
    (r'print\("   -> \?\?\?.*?Retrying with Fixed Code\.\.\."\)', 'print("   -> [INFO] Retrying with Fixed Code...")'),
    (r'print\("   -> \?\?\?.*?Analyzing Traceback.*?Self-Correction.*?\.\.\."\)', 'print("   -> [INFO] Analyzing Traceback (Self-Correction)...")'),
    (r'print\("   -> \?\?\?.*?Analyzing Traceback.*?\.\.\."\)', 'print("   -> [INFO] Analyzing Traceback...")'),
    # 일반적인 깨진 문자 패턴
    (r'\?\?\?', '[INFO]'),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

# 파일 쓰기
with open('src/pipeline/orchestrator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all encoding issues in orchestrator.py")
