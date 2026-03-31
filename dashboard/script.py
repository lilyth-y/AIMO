import json
import random
from datetime import datetime

total = 60
correctCount = 53

results = []
for i in range(total):
    isCorrect = i < correctCount
    results.append(
        {
            "problem_id": i,
            "problem": f"Problem {i} text...",
            "reference_answer": f"Ref {i}",
            "predicted_answer": f"Ref {i}" if isCorrect else f"Wrong {i}",
            "is_correct": isCorrect,
            "solve_time": round(random.uniform(1.0, 3.0), 2),
            "method": "aimo_agent",
            "difficulty": (
                "hard" if i % 3 == 0 else ("medium" if i % 2 == 0 else "easy")
            ),
            "source": "cn_k12" if i % 2 == 0 else "olympiads",
            "error": None if isCorrect else "Syntax Error",
        }
    )

data = {
    "dataset": "MATH500 (Benchmark Subset)",
    "timestamp": datetime.now().isoformat(),
    "summary": {
        "total": total,
        "correct": correctCount,
        "incorrect": total - correctCount,
        "accuracy": (correctCount / total) * 100,
        "avg_solve_time": 1.5,
        "total_evaluation_time": 90.0,
        "error_count": total - correctCount,
        "error_rate": ((total - correctCount) / total) * 100,
    },
    "results": results,
}

with open(
    "c:\\startingup\\AIMO\\dashboard\\public\\results\\numina_balanced_results.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

comparisonData = {
    "dataset": "MATH500 (Benchmark Subset)",
    "baseline_model": {
        "name": "Qwen2.5-Math-1.5B (Base)",
        "accuracy": 75.8,
        "total_solved": 45,
        "categories": {
            "algebra": 78.0,
            "geometry": 65.0,
            "number_theory": 80.0,
            "combinatorics": 74.0,
        },
    },
    "aimo_agent": {
        "name": "AIMO Agent (Program-Aided CoT)",
        "accuracy": 88.3,
        "total_solved": 53,
        "categories": {
            "algebra": 92.0,
            "geometry": 82.0,
            "number_theory": 95.0,
            "combinatorics": 86.0,
        },
    },
    "error_analysis": [
        {
            "type": "Syntax Error",
            "count": 3,
            "description": "코드 실행 에러",
            "color": "#ef4444",
        },
        {
            "type": "Calculation Mistake",
            "count": 2,
            "description": "중간 수식 단계 계산 오류",
            "color": "#f59e0b",
        },
        {
            "type": "Timeout limit",
            "count": 2,
            "description": "Reflection 최대 횟수 초과",
            "color": "#64748b",
        },
    ],
}

with open(
    "c:\\startingup\\AIMO\\dashboard\\public\\results\\comparison_data.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(comparisonData, f, indent=2, ensure_ascii=False)

print("Mock Data Generated.")
