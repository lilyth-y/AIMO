"""
Manual Evaluation of Agent Responses
"""
import json

# Load data
with open('generated_queries.json', 'r', encoding='utf-8') as f:
    queries = json.load(f)

with open('generated_responses.json', 'r', encoding='utf-8') as f:
    responses = json.load(f)

# Ground truth answers
ground_truth = {
    "Find the integer x such that 3x + 5 = 20.": "5",  # 3x = 15, x = 5
    "What is the remainder when 2^10 is divided by 7?": "2",  # 1024 mod 7 = 2
    "Find the roots of x^2 - 5x + 6 = 0.": "2,3",  # (x-2)(x-3) = 0
    "Solve the system: x = 2 mod 3, x = 3 mod 5.": "8",  # x = 8 (8 mod 3 = 2, 8 mod 5 = 3)
    "If a_1 = 1 and a_n = 2a_{n-1} + 1, find a_5.": "31"  # 1, 3, 7, 15, 31
}

print("=" * 80)
print("수동 평가 결과")
print("=" * 80)

correct = 0
total = len(responses)

for i, resp in enumerate(responses):
    query = resp['query']
    agent_answer = resp['response']
    expected = ground_truth.get(query, "N/A")
    
    # Check correctness
    is_correct = agent_answer == expected
    if is_correct:
        correct += 1
        status = "✅ 정답"
    else:
        status = "❌ 오답"
    
    print(f"\n[문제 {i+1}]")
    print(f"질문: {query}")
    print(f"에이전트 답변: {agent_answer}")
    print(f"정답: {expected}")
    print(f"결과: {status}")

print("\n" + "=" * 80)
print(f"최종 점수: {correct}/{total} = {100*correct/total:.1f}%")
print("=" * 80)

# Detailed analysis
print("\n[상세 분석]")
print(f"✅ 정답: {correct}개")
print(f"❌ 오답: {total - correct}개")
print(f"📊 정확도: {100*correct/total:.1f}%")

if total - correct > 0:
    print(f"\n[오답 문제 분석]")
    for i, resp in enumerate(responses):
        query = resp['query']
        agent_answer = resp['response']
        expected = ground_truth.get(query, "N/A")
        if agent_answer != expected:
            print(f"  • 문제 {i+1}: {query[:50]}...")
            print(f"    답변: {agent_answer}, 정답: {expected}")
