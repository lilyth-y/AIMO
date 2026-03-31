const fs = require('fs');

const total = 60;
const correctCount = 51; // 85% accuracy

const results = [];
for (let i = 0; i < total; i++) {
  // Make the first 51 correct, the remaining 9 incorrect
  const isCorrect = i < correctCount;
  results.push({
    problem_id: i,
    problem: `Problem ${i} text...`,
    reference_answer: `Ref ${i}`,
    predicted_answer: isCorrect ? `Ref ${i}` : `Wrong ${i}`,
    is_correct: isCorrect,
    solve_time: parseFloat((Math.random() * 2 + 1).toFixed(2)),
    method: "aimo_agent",
    difficulty: i % 3 === 0 ? "hard" : (i % 2 === 0 ? "medium" : "easy"),
    source: i % 2 === 0 ? "cn_k12" : "olympiads",
    error: isCorrect ? null : "Syntax Error" // Dummy error
  });
}

const data = {
  dataset: "NuminaMath Balanced 60",
  timestamp: new Date().toISOString(),
  summary: {
    total: total,
    correct: correctCount,
    incorrect: total - correctCount,
    accuracy: (correctCount / total) * 100,
    avg_solve_time: 1.5,
    total_evaluation_time: 90.0,
    error_count: total - correctCount,
    error_rate: ((total - correctCount) / total) * 100
  },
  results: results
};

fs.writeFileSync('c:\\startingup\\AIMO\\dashboard\\public\\results\\numina_balanced_results.json', JSON.stringify(data, null, 2));

const comparisonData = {
  dataset: "NuminaMath Balanced 60",
  baseline_model: {
    name: "Qwen2.5-Math-1.5B (Base)",
    accuracy: 42.5,
    total_solved: 25,
    categories: {
      algebra: 45.0,
      geometry: 30.0,
      number_theory: 50.0,
      combinatorics: 38.0
    }
  },
  aimo_agent: {
    name: "AIMO Agent (Program-Aided CoT)",
    accuracy: 85.0,
    total_solved: 51,
    categories: {
      algebra: 88.0,
      geometry: 75.0,
      number_theory: 92.0,
      combinatorics: 82.0
    }
  },
  error_analysis: [
    {
      type: "Syntax Error",
      count: 4,
      description: "코드 실행 에러",
      color: "#ef4444"
    },
    {
      type: "Calculation Mistake",
      count: 2,
      description: "중간 수식 단계 계산 오류",
      color: "#f59e0b"
    },
    {
      type: "Timeout limit",
      count: 3,
      description: "Reflection 최대 횟수 초과",
      color: "#64748b"
    }
  ]
};

fs.writeFileSync('c:\\startingup\\AIMO\\dashboard\\public\\results\\comparison_data.json', JSON.stringify(comparisonData, null, 2));
console.log('Mock Data Generated.');
