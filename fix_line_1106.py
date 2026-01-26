"""1106줄 수정"""
with open('src/pipeline/orchestrator.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# 1106줄 수정 (0-based index이므로 1105)
if len(lines) > 1105:
    lines[1105] = '                    print("   -> [INFO] Analyzing Traceback (Self-Correction)...")' + '\n'

with open('src/pipeline/orchestrator.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed line 1106')
