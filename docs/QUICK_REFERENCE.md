# Quick Reference: Mathematical Solution & Revolving Resolution

**Quick access guide for developers**

---

## 🎯 Quick Start

### 1. Run Comprehensive Evaluation
```bash
cd C:\startingup\AIMO
python examples/comprehensive_evaluation.py --max-problems 20 --model-name "OMI-1.0"
```

### 2. Run Revolving Resolution Demo
```bash
python examples/revolving_resolution_demo.py
```

### 3. Run Basic Evaluation
```bash
python examples/quick_eval.py
```

---

## 📊 Evaluation Levels

### Level 1: Basic Evaluation
```python
from evaluation import EvaluationMetrics, EvaluationResult

metrics = EvaluationMetrics(dataset_name="Test")
metrics.start()

# Solve and add results
result = solve_problem(problem)
metrics.add_result(EvaluationResult(
    problem_id=0,
    problem=problem,
    reference_answer="42",
    predicted_answer=result,
    is_correct=(result == "42")
))

metrics.finish()
metrics.print_summary()
```

**Output**: Accuracy, time, difficulty breakdown

---

### Level 2: Advanced Metrics
```python
from evaluation.advanced_metrics import AdvancedEvaluator

evaluator = AdvancedEvaluator()

for problem in problems:
    result = solve(problem)
    evaluator.add_result(
        is_correct=(result == answer),
        latency=solve_time,
        error_type=None
    )

metrics = evaluator.calculate_comprehensive_metrics()
print(f"95% CI: {metrics.accuracy_ci}")
print(f"P95 latency: {metrics.p95_latency}s")
```

**Output**: Confidence intervals, p-values, latency metrics

---

### Level 3: Comprehensive Report
```python
from evaluation.comprehensive_reporting import ComprehensiveReporter

reporter = ComprehensiveReporter()
report = reporter.generate_full_report(
    results=all_results,
    metrics=calculated_metrics,
    report_name="Evaluation_2026Q1"
)
```

**Output**: Full report with 7+ visualizations, markdown, HTML

---

## 🔄 Revolving Resolution Patterns

### Pattern 1: Single Problem with Retry
```python
from pipeline.revolving_resolution import RevolvingResolver, ProblemContext

resolver = RevolvingResolver(max_iterations=3)

context = ProblemContext(
    problem_text="Solve x^2 - 5x + 6 = 0",
    domain="algebra",
    difficulty="medium",
    features={'has_equations': True}
)

answer, status, metadata = resolver.resolve(context, solver_fn)
```

---

### Pattern 2: Multi-Path Consensus
```python
from pipeline.revolving_resolution import MultiPathExplorer

explorer = MultiPathExplorer(n_paths=3)

answer, confidence, metadata = explorer.explore(
    problem_context,
    solver_function
)

if metadata['consensus']:
    print(f"High confidence answer: {answer}")
```

---

### Pattern 3: Adaptive Learning
```python
from pipeline.revolving_resolution import AdaptiveLearner

learner = AdaptiveLearner()

# Learn from attempts
for problem, strategy, success in training_data:
    learner.record_attempt(
        problem.features,
        strategy,
        success,
        confidence
    )

# Get recommendations
recommended = learner.get_recommended_strategies(
    problem.features,
    n=3
)
```

---

## 📈 Benchmarking Workflows

### Workflow 1: Save Benchmark
```python
from evaluation.benchmarking import BenchmarkManager, BenchmarkRun

manager = BenchmarkManager()

run = BenchmarkRun(
    run_id=f"run_{timestamp}",
    model_name="OMI-1.0",
    dataset="numina",
    timestamp=datetime.now().isoformat(),
    accuracy=85.5,
    total_problems=100,
    correct=85,
    avg_time=2.5,
    metadata={}
)

manager.add_run(run)
```

---

### Workflow 2: Generate Leaderboard
```python
manager = BenchmarkManager()

# Save leaderboard
path = manager.save_leaderboard("numina")

# Export report
report = manager.export_benchmark_report(
    "numina",
    output_format='markdown'
)
```

---

### Workflow 3: Compare Models
```python
manager = BenchmarkManager()

# Compare all models on dataset
comparison = manager.compare_models("numina")
print(comparison)

# Track progress over time
progress = manager.track_progress_over_time(
    model_name="OMI-1.0",
    dataset="numina"
)
print(progress)
```

---

## 🧮 Strategy Selection Guide

### By Problem Type

| Problem Type | Primary Strategy | Secondary Strategy |
|--------------|------------------|-------------------|
| Simple arithmetic | `DIRECT_COMPUTATION` | `ALGEBRAIC_MANIPULATION` |
| Linear equations | `ALGEBRAIC_MANIPULATION` | `SYMBOLIC_SOLVING` |
| Quadratic equations | `SYMBOLIC_SOLVING` | `ALGEBRAIC_MANIPULATION` |
| Systems of equations | `SYMBOLIC_SOLVING` | `NUMERICAL_APPROXIMATION` |
| Inequalities | `ALGEBRAIC_MANIPULATION` | `CASE_ANALYSIS` |
| Geometry | `THEOREM_APPLICATION` | `NUMERICAL_APPROXIMATION` |
| Number theory | `PATTERN_MATCHING` | `THEOREM_APPLICATION` |
| Combinatorics | `PATTERN_MATCHING` | `DIRECT_COMPUTATION` |
| Calculus | `SYMBOLIC_SOLVING` | `NUMERICAL_APPROXIMATION` |

---

### By Difficulty

```python
# Easy problems
strategies = [
    StrategyType.DIRECT_COMPUTATION,
    StrategyType.ALGEBRAIC_MANIPULATION
]

# Medium problems
strategies = [
    StrategyType.ALGEBRAIC_MANIPULATION,
    StrategyType.SYMBOLIC_SOLVING,
    StrategyType.PATTERN_MATCHING
]

# Hard problems (try all)
strategies = list(StrategyType)
```

---

## 🔍 Error Analysis

### Categorize Errors
```python
from evaluation.advanced_metrics import ErrorCategorizer

error_type = ErrorCategorizer.categorize_error(error_msg)

# Returns one of:
# - syntax_error
# - runtime_error
# - timeout
# - wrong_answer
# - parsing_error
# - oom_error
# - unknown
```

---

### Analyze Error Patterns
```python
analysis = ErrorCategorizer.analyze_error_patterns(errors)

print(f"Total errors: {analysis['total_errors']}")
print(f"Most common: {analysis['most_common']}")

for category, stats in analysis['by_category'].items():
    print(f"{category}: {stats['count']} ({stats['percentage']:.1f}%)")
```

---

## 📊 Visualization Quick Reference

The `ComprehensiveReporter` automatically generates:

1. **Accuracy Overview**: Bar chart of overall performance
2. **Difficulty Breakdown**: Accuracy by difficulty level
3. **Source Breakdown**: Performance by problem source
4. **Method Comparison**: Compare different solution methods
5. **Time Distribution**: Histogram and box plot of solve times
6. **Error Analysis**: Categorized error breakdown
7. **Result Distribution**: Pie chart of correct/incorrect

All saved as high-quality PNG files (300 DPI).

---

## 🎛️ Configuration Options

### Resolver Configuration
```python
resolver = RevolvingResolver(
    max_iterations=5,           # Max attempts per problem
    confidence_threshold=0.8,   # Early stop threshold
    time_budget=120.0          # Max time in seconds
)
```

### Evaluator Configuration
```python
metrics = EvaluationMetrics(
    dataset_name="MyDataset"    # Name for results
)
```

### Reporter Configuration
```python
reporter = ComprehensiveReporter(
    output_dir="reports"        # Where to save reports
)
```

---

## 🔬 Statistical Tests

### Confidence Intervals
```python
# Wilson score interval (default)
ci = evaluator.calculate_confidence_interval(confidence_level=0.95)

# Bootstrap interval
from evaluation.advanced_metrics import bootstrap_confidence_interval
ci = bootstrap_confidence_interval(results, n_bootstrap=10000)
```

### Model Comparison
```python
# McNemar's test
p_value, is_significant = evaluator.mcnemar_test(other_results)

if is_significant:
    print("Models are significantly different (p < 0.05)")
```

### Effect Size
```python
from evaluation.advanced_metrics import calculate_effect_size

effect = calculate_effect_size(model1_results, model2_results)

# Interpret Cohen's h:
# Small: 0.2, Medium: 0.5, Large: 0.8
```

---

## 🚀 Performance Tips

### 1. Parallel Evaluation
```python
# Use multiprocessing for large evaluations
from multiprocessing import Pool

with Pool(processes=4) as pool:
    results = pool.map(solve_problem, problems)
```

### 2. Early Stopping
```python
# Stop when confidence is high
resolver = RevolvingResolver(
    confidence_threshold=0.9,  # Higher threshold
    max_iterations=3           # Fewer max iterations
)
```

### 3. Strategy Caching
```python
# Cache expensive strategy results
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_solve(problem_hash, strategy):
    return solve(problem, strategy)
```

---

## 📁 Output Locations

```
AIMO/
├── results/              # Evaluation results (JSON)
├── reports/              # Comprehensive reports
│   └── [report_name]_[timestamp]/
│       ├── README.md     # Main report
│       ├── *.png         # Visualizations
│       └── summary.json  # Metadata
├── benchmarks/           # Benchmark database
│   ├── benchmark_runs.json
│   └── leaderboard_*.json
└── logs/                 # Evaluation logs
```

---

## 🐛 Troubleshooting

### Issue: Missing dependencies
```bash
# Install optional dependencies
pip install scipy matplotlib seaborn pandas
```

### Issue: Slow evaluation
- Reduce `max_problems`
- Increase `time_budget per problem
- Use strategy caching
- Enable parallel execution

### Issue: Low confidence
- Increase `max_iterations`
- Try multi-path exploration
- Use adaptive learning
- Check problem context quality

---

## 📚 Further Reading

1. **Research Tree**: `docs/MATHEMATICAL_SOLUTION_RESEARCH_TREE.md`
2. **Full Summary**: `docs/COMPREHENSIVE_EVALUATION_SUMMARY.md`
3. **Examples**: `examples/comprehensive_evaluation.py`
4. **Source Code**: `src/evaluation/` and `src/pipeline/`

---

## 💡 Best Practices

1. **Always set appropriate time budgets** to prevent hanging
2. **Use comprehensive reporting** for important evaluations
3. **Track progress** with benchmarking for long-term projects
4. **Enable adaptive learning** for repeated evaluations
5. **Generate confidence intervals** for rigorous comparisons
6. **Use multi-path exploration** for critical problems
7. **Document your evaluation setup** for reproducibility

---

**Last Updated**: 2026-02-22  
**Version**: 1.0
