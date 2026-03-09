
import json
import evaluate
from sklearn.metrics import f1_score, accuracy_score

# numina_training_5k.jsonl에서 문제-정답 추출
problems = []
refs = []
with open('data/numina_training_5k.jsonl', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        # 문제와 정답(정답이 없는 경우는 건너뜀)
        if obj.get('answer') and obj.get('problem'):
            problems.append(obj['problem'].strip())
            refs.append(obj['answer'].strip())

# 예시: predictions는 실제 모델 답변 리스트로 대체 필요
# 여기서는 정답과 동일하게 넣어 예시(BLEU=1.0)
predictions = [r for r in refs]

# BLEU (문장 단위로 리스트 필요)
bleu = evaluate.load('bleu')
bleu_result = bleu.compute(predictions=predictions, references=[[r] for r in refs])
print('BLEU:', bleu_result)

# F1 (macro average, 문자열 일치 기준)
f1 = f1_score(refs, predictions, average='macro')
print('F1:', f1)

# Accuracy (정확히 일치하는 비율)
acc = accuracy_score(refs, predictions)
print('Accuracy:', acc)
