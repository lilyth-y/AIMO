"""
Comprehensive Benchmarking Module
- Compare multiple models/runs
- Track performance over time
- Generate comparison reports
- Leaderboard functionality
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, asdict


@dataclass
class BenchmarkRun:
    """Single benchmark run result"""
    run_id: str
    model_name: str
    dataset: str
    timestamp: str
    accuracy: float
    total_problems: int
    correct: int
    avg_time: float
    metadata: Dict[str, Any]
    
    # Advanced metrics
    accuracy_ci_lower: Optional[float] = None
    accuracy_ci_upper: Optional[float] = None
    p50_latency: Optional[float] = None
    p95_latency: Optional[float] = None
    
    # Breakdown by difficulty
    easy_accuracy: Optional[float] = None
    medium_accuracy: Optional[float] = None
    hard_accuracy: Optional[float] = None


class BenchmarkManager:
    """
    Manage benchmarks across multiple runs and models
    """
    
    def __init__(self, benchmark_dir: str = "benchmarks"):
        self.benchmark_dir = Path(benchmark_dir)
        self.benchmark_dir.mkdir(parents=True, exist_ok=True)
        self.runs: List[BenchmarkRun] = []
        self._load_existing_runs()
    
    def _load_existing_runs(self):
        """Load existing benchmark runs from disk"""
        runs_file = self.benchmark_dir / "benchmark_runs.json"
        if runs_file.exists():
            with open(runs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.runs = [BenchmarkRun(**run) for run in data]
    
    def save_runs(self):
        """Save benchmark runs to disk"""
        runs_file = self.benchmark_dir / "benchmark_runs.json"
        with open(runs_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(run) for run in self.runs], f, indent=2)
    
    def add_run(self, run: BenchmarkRun):
        """Add a benchmark run"""
        self.runs.append(run)
        self.save_runs()
    
    def get_runs_by_dataset(self, dataset: str) -> List[BenchmarkRun]:
        """Get all runs for a specific dataset"""
        return [run for run in self.runs if run.dataset == dataset]
    
    def get_runs_by_model(self, model_name: str) -> List[BenchmarkRun]:
        """Get all runs for a specific model"""
        return [run for run in self.runs if run.model_name == model_name]
    
    def get_latest_run(self, dataset: str, model_name: str) -> Optional[BenchmarkRun]:
        """Get the latest run for a dataset and model"""
        matching_runs = [
            run for run in self.runs 
            if run.dataset == dataset and run.model_name == model_name
        ]
        if not matching_runs:
            return None
        return max(matching_runs, key=lambda x: x.timestamp)
    
    def compare_models(self, dataset: str, 
                      model_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Compare multiple models on the same dataset
        
        Args:
            dataset: Dataset name
            model_names: Optional list of model names to compare
        
        Returns:
            DataFrame with comparison
        """
        runs = self.get_runs_by_dataset(dataset)
        
        if model_names:
            runs = [r for r in runs if r.model_name in model_names]
        
        if not runs:
            return pd.DataFrame()
        
        # Get latest run for each model
        model_runs = {}
        for run in runs:
            if run.model_name not in model_runs:
                model_runs[run.model_name] = run
            elif run.timestamp > model_runs[run.model_name].timestamp:
                model_runs[run.model_name] = run
        
        # Create comparison dataframe
        data = []
        for model_name, run in model_runs.items():
            data.append({
                'Model': model_name,
                'Accuracy': f"{run.accuracy:.2f}%",
                'Correct': f"{run.correct}/{run.total_problems}",
                'Avg Time (s)': f"{run.avg_time:.2f}",
                'CI Lower': f"{run.accuracy_ci_lower:.2f}%" if run.accuracy_ci_lower else 'N/A',
                'CI Upper': f"{run.accuracy_ci_upper:.2f}%" if run.accuracy_ci_upper else 'N/A',
                'P95 Latency': f"{run.p95_latency:.2f}s" if run.p95_latency else 'N/A',
                'Easy': f"{run.easy_accuracy:.1f}%" if run.easy_accuracy is not None else 'N/A',
                'Medium': f"{run.medium_accuracy:.1f}%" if run.medium_accuracy is not None else 'N/A',
                'Hard': f"{run.hard_accuracy:.1f}%" if run.hard_accuracy is not None else 'N/A',
                'Date': run.timestamp[:10]
            })
        
        df = pd.DataFrame(data)
        # Sort by accuracy
        df = df.sort_values('Accuracy', ascending=False)
        return df
    
    def generate_leaderboard(self, dataset: str) -> Dict[str, Any]:
        """
        Generate leaderboard for a dataset
        
        Args:
            dataset: Dataset name
        
        Returns:
            Leaderboard data
        """
        runs = self.get_runs_by_dataset(dataset)
        
        if not runs:
            return {'dataset': dataset, 'entries': [], 'last_updated': None}
        
        # Get best run for each model
        model_best = {}
        for run in runs:
            if run.model_name not in model_best:
                model_best[run.model_name] = run
            elif run.accuracy > model_best[run.model_name].accuracy:
                model_best[run.model_name] = run
        
        # Sort by accuracy
        sorted_runs = sorted(model_best.values(), 
                           key=lambda x: x.accuracy, 
                           reverse=True)
        
        # Create leaderboard entries
        entries = []
        for rank, run in enumerate(sorted_runs, 1):
            entries.append({
                'rank': rank,
                'model': run.model_name,
                'accuracy': run.accuracy,
                'correct': run.correct,
                'total': run.total_problems,
                'avg_time': run.avg_time,
                'date': run.timestamp,
                'ci_lower': run.accuracy_ci_lower,
                'ci_upper': run.accuracy_ci_upper
            })
        
        return {
            'dataset': dataset,
            'entries': entries,
            'last_updated': datetime.now().isoformat(),
            'total_runs': len(runs),
            'unique_models': len(model_best)
        }
    
    def save_leaderboard(self, dataset: str, filename: Optional[str] = None):
        """Save leaderboard to file"""
        leaderboard = self.generate_leaderboard(dataset)
        
        if filename is None:
            filename = f"leaderboard_{dataset}.json"
        
        output_path = self.benchmark_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(leaderboard, f, indent=2)
        
        return str(output_path)
    
    def track_progress_over_time(self, model_name: str, 
                                 dataset: str) -> pd.DataFrame:
        """
        Track a model's performance over time
        
        Args:
            model_name: Model name
            dataset: Dataset name
        
        Returns:
            DataFrame with historical performance
        """
        runs = [
            r for r in self.runs 
            if r.model_name == model_name and r.dataset == dataset
        ]
        
        if not runs:
            return pd.DataFrame()
        
        # Sort by timestamp
        runs = sorted(runs, key=lambda x: x.timestamp)
        
        data = []
        for run in runs:
            data.append({
                'Date': run.timestamp[:10],
                'Time': run.timestamp[11:19],
                'Accuracy': run.accuracy,
                'Correct': run.correct,
                'Total': run.total_problems,
                'Avg Time': run.avg_time,
                'Run ID': run.run_id
            })
        
        return pd.DataFrame(data)
    
    def compare_runs(self, run_id1: str, run_id2: str) -> Dict[str, Any]:
        """
        Compare two specific runs
        
        Args:
            run_id1: First run ID
            run_id2: Second run ID
        
        Returns:
            Comparison data
        """
        run1 = next((r for r in self.runs if r.run_id == run_id1), None)
        run2 = next((r for r in self.runs if r.run_id == run_id2), None)
        
        if not run1 or not run2:
            return {'error': 'One or both runs not found'}
        
        # Calculate differences
        acc_diff = run2.accuracy - run1.accuracy
        time_diff = run2.avg_time - run1.avg_time
        
        return {
            'run1': {
                'id': run1.run_id,
                'model': run1.model_name,
                'accuracy': run1.accuracy,
                'avg_time': run1.avg_time,
                'date': run1.timestamp
            },
            'run2': {
                'id': run2.run_id,
                'model': run2.model_name,
                'accuracy': run2.accuracy,
                'avg_time': run2.avg_time,
                'date': run2.timestamp
            },
            'difference': {
                'accuracy': acc_diff,
                'accuracy_pct_change': (acc_diff / run1.accuracy * 100) if run1.accuracy > 0 else 0,
                'avg_time': time_diff,
                'time_pct_change': (time_diff / run1.avg_time * 100) if run1.avg_time > 0 else 0,
                'winner': run1.run_id if run1.accuracy > run2.accuracy else run2.run_id
            }
        }
    
    def export_benchmark_report(self, dataset: str, 
                               output_format: str = 'markdown') -> str:
        """
        Export comprehensive benchmark report
        
        Args:
            dataset: Dataset name
            output_format: 'markdown' or 'html'
        
        Returns:
            Path to exported file
        """
        leaderboard = self.generate_leaderboard(dataset)
        comparison_df = self.compare_models(dataset)
        
        if output_format == 'markdown':
            return self._export_markdown_report(dataset, leaderboard, comparison_df)
        elif output_format == 'html':
            return self._export_html_report(dataset, leaderboard, comparison_df)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def _export_markdown_report(self, dataset: str, 
                               leaderboard: Dict, 
                               comparison_df: pd.DataFrame) -> str:
        """Export markdown report"""
        filename = f"benchmark_report_{dataset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        output_path = self.benchmark_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Benchmark Report: {dataset}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- Total Runs: {leaderboard['total_runs']}\n")
            f.write(f"- Unique Models: {leaderboard['unique_models']}\n")
            f.write(f"- Last Updated: {leaderboard['last_updated']}\n\n")
            
            # Leaderboard
            f.write("## Leaderboard\n\n")
            f.write("| Rank | Model | Accuracy | Correct/Total | Avg Time | CI (95%) |\n")
            f.write("|------|-------|----------|---------------|----------|----------|\n")
            
            for entry in leaderboard['entries']:
                ci_str = f"{entry['ci_lower']:.2f}% - {entry['ci_upper']:.2f}%" if entry.get('ci_lower') else 'N/A'
                f.write(f"| {entry['rank']} | {entry['model']} | {entry['accuracy']:.2f}% | "
                       f"{entry['correct']}/{entry['total']} | {entry['avg_time']:.2f}s | {ci_str} |\n")
            
            # Detailed comparison
            f.write("\n## Detailed Comparison\n\n")
            if not comparison_df.empty:
                f.write(comparison_df.to_markdown(index=False))
            
            f.write("\n\n---\n")
            f.write("*Report generated by OMI Comprehensive Evaluation Framework*\n")
        
        return str(output_path)
    
    def _export_html_report(self, dataset: str, 
                           leaderboard: Dict, 
                           comparison_df: pd.DataFrame) -> str:
        """Export HTML report"""
        filename = f"benchmark_report_{dataset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_path = self.benchmark_dir / filename
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Report: {dataset}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; }}
        .rank-1 {{ background-color: #ffd700; }}
        .rank-2 {{ background-color: #c0c0c0; }}
        .rank-3 {{ background-color: #cd7f32; }}
    </style>
</head>
<body>
    <h1>Benchmark Report: {dataset}</h1>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <ul>
            <li>Total Runs: {leaderboard['total_runs']}</li>
            <li>Unique Models: {leaderboard['unique_models']}</li>
            <li>Last Updated: {leaderboard['last_updated']}</li>
        </ul>
    </div>
    
    <h2>Leaderboard</h2>
    <table>
        <tr>
            <th>Rank</th>
            <th>Model</th>
            <th>Accuracy</th>
            <th>Correct/Total</th>
            <th>Avg Time</th>
            <th>95% CI</th>
        </tr>
"""
        
        for entry in leaderboard['entries']:
            rank_class = f"rank-{entry['rank']}" if entry['rank'] <= 3 else ""
            ci_str = f"{entry['ci_lower']:.2f}% - {entry['ci_upper']:.2f}%" if entry.get('ci_lower') else 'N/A'
            html_content += f"""
        <tr class="{rank_class}">
            <td>{entry['rank']}</td>
            <td>{entry['model']}</td>
            <td>{entry['accuracy']:.2f}%</td>
            <td>{entry['correct']}/{entry['total']}</td>
            <td>{entry['avg_time']:.2f}s</td>
            <td>{ci_str}</td>
        </tr>
"""
        
        html_content += """
    </table>
    
    <h2>Detailed Comparison</h2>
"""
        
        if not comparison_df.empty:
            html_content += comparison_df.to_html(index=False, classes='comparison-table')
        
        html_content += """
    <hr>
    <p><em>Report generated by OMI Comprehensive Evaluation Framework</em></p>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)


class CrossValidation:
    """K-fold cross-validation support"""
    
    def __init__(self, n_folds: int = 5, random_seed: int = 42):
        self.n_folds = n_folds
        self.random_seed = random_seed
    
    def split_dataset(self, problems: List[Any]) -> List[Tuple[List[Any], List[Any]]]:
        """
        Split dataset into k folds
        
        Args:
            problems: List of problems
        
        Returns:
            List of (train, test) splits
        """
        import numpy as np
        np.random.seed(self.random_seed)
        
        # Shuffle problems
        indices = np.arange(len(problems))
        np.random.shuffle(indices)
        
        # Split into folds
        fold_size = len(problems) // self.n_folds
        folds = []
        
        for i in range(self.n_folds):
            test_start = i * fold_size
            test_end = (i + 1) * fold_size if i < self.n_folds - 1 else len(problems)
            
            test_indices = indices[test_start:test_end]
            train_indices = np.concatenate([indices[:test_start], indices[test_end:]])
            
            train_problems = [problems[idx] for idx in train_indices]
            test_problems = [problems[idx] for idx in test_indices]
            
            folds.append((train_problems, test_problems))
        
        return folds
    
    def evaluate_with_cv(self, problems: List[Any], 
                        evaluate_fn) -> Dict[str, Any]:
        """
        Evaluate with cross-validation
        
        Args:
            problems: List of problems
            evaluate_fn: Function that takes a list of problems and returns accuracy
        
        Returns:
            Cross-validation results
        """
        folds = self.split_dataset(problems)
        fold_accuracies = []
        
        for i, (train, test) in enumerate(folds):
            print(f"Evaluating fold {i+1}/{self.n_folds}...")
            accuracy = evaluate_fn(test)
            fold_accuracies.append(accuracy)
        
        import numpy as np
        return {
            'fold_accuracies': fold_accuracies,
            'mean_accuracy': np.mean(fold_accuracies),
            'std_accuracy': np.std(fold_accuracies),
            'min_accuracy': np.min(fold_accuracies),
            'max_accuracy': np.max(fold_accuracies),
            'n_folds': self.n_folds
        }
