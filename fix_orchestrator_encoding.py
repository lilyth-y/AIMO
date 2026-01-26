"""orchestrator.py 인코딩 문제 수정"""
import re

# 파일 읽기
with open('src/pipeline/orchestrator.py', 'rb') as f:
    content_bytes = f.read()

# UTF-8로 디코딩 (에러는 대체 문자로)
content = content_bytes.decode('utf-8', errors='replace')

# 338줄의 깨진 문자 찾아서 수정
# "   -> ? Self-Refine Attempt..." 패턴 찾기
pattern = r'print\("   -> [^\"]*Self-Refine Attempt\.\.\."\)'
replacement = 'print("   -> [INFO] Self-Refine Attempt...")'

# 모든 매칭되는 부분 수정
content = re.sub(pattern, replacement, content)

# 다른 깨진 특수 문자들도 확인
# "Retrying with Fixed Code..." 같은 부분도 확인
pattern2 = r'print\("   -> [^\"]*Retrying with Fixed Code\.\.\."\)'
replacement2 = 'print("   -> [INFO] Retrying with Fixed Code...")'
content = re.sub(pattern2, replacement2, content)

# 파일 쓰기
with open('src/pipeline/orchestrator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed encoding issues in orchestrator.py")
print("Checked and fixed:")
print("  - Self-Refine Attempt line")
print("  - Retrying with Fixed Code line")
