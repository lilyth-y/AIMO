"""
Comprehensive Reporting Module
- Detailed evaluation reports with visualizations
- Error analysis reports
- Performance analysis
- Progress tracking
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


class ComprehensiveReporter:
    """
    Generate comprehensive evaluation reports with visualizations
    """
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        sns.set_style("whitegrid")
    
    def generate_full_report(self, 
                           results: List[Dict[str, Any]],
                           metrics: Dict[str, Any],
                           report_name: str = "evaluation_report") -> str:
        """
        Generate comprehensive evaluation report with all visualizations
        
        Args:
            results: List of evaluation results
            metrics: Calculated metrics dictionary
            report_name: Name for the report
        
        Returns:
            Path to generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = self.output_dir / f"{report_name}_{timestamp}"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate visualizations
        viz_paths = self._generate_visualizations(results, metrics, report_dir)
        
        # Generate markdown report
        report_path = self._generate_markdown_report(
            results, metrics, viz_paths, report_dir, report_name
        )
        
        # Generate JSON summary
        summary_path = report_dir / "summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'metrics': metrics,
                'total_results': len(results),
                'report_name': report_name
            }, f, indent=2)
        
        print(f"✅ Comprehensive report generated: {report_path}")
        return str(report_path)
    
    def _generate_visualizations(self, 
                                results: List[Dict[str, Any]],
                                metrics: Dict[str, Any],
                                output_dir: Path) -> Dict[str, str]:
        """Generate all visualization plots"""
        viz_paths = {}
        
        # 1. Accuracy bar chart
        viz_paths['accuracy'] = self._plot_accuracy_overview(metrics, output_dir)
        
        # 2. Difficulty breakdown
        if metrics.get('by_difficulty'):
            viz_paths['difficulty'] = self._plot_difficulty_breakdown(
                metrics['by_difficulty'], output_dir
            )
        
        # 3. Source/dataset breakdown
        if metrics.get('by_source'):
            viz_paths['source'] = self._plot_source_breakdown(
                metrics['by_source'], output_dir
            )
        
        # 4. Method comparison
        if metrics.get('by_method'):
            viz_paths['method'] = self._plot_method_comparison(
                metrics['by_method'], output_dir
            )
        
        # 5. Time distribution
        solve_times = [r.get('solve_time', 0) for r in results if r.get('solve_time', 0) > 0]
        if solve_times:
            viz_paths['time_dist'] = self._plot_time_distribution(
                solve_times, output_dir
            )
        
        # 6. Error analysis
        errors = [r for r in results if not r.get('is_correct', False)]
        if errors:
            viz_paths['errors'] = self._plot_error_analysis(errors, output_dir)
        
        # 7. Success/Failure distribution
        viz_paths['distribution'] = self._plot_result_distribution(results, output_dir)
        
        return viz_paths
    
    def _plot_accuracy_overview(self, metrics: Dict[str, Any], 
                               output_dir: Path) -> str:
        """Plot accuracy overview"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        categories = ['Overall', 'Correct', 'Incorrect', 'Errors']
        values = [
            metrics.get('accuracy', 0),
            metrics.get('correct', 0),
            metrics.get('incorrect', 0),
            metrics.get('error_count', 0)
        ]
        
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']
        
        # Create bars for percentages
        bars = ax.bar(categories[:1], [values[0]], color=colors[0], alpha=0.8)
        
        # Create counts on side
        ax2 = ax.twinx()
        bars2 = ax2.bar(categories[1:], values[1:], color=colors[1:], alpha=0.8)
        
        ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax.set_title('Evaluation Overview', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 100)
        
        plt.tight_layout()
        output_path = output_dir / 'accuracy_overview.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def _plot_difficulty_breakdown(self, difficulty_stats: Dict[str, Any],
                                   output_dir: Path) -> str:
        """Plot accuracy by difficulty"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        difficulties = list(difficulty_stats.keys())
        accuracies = [difficulty_stats[d]['accuracy'] for d in difficulties]
        totals = [difficulty_stats[d]['total'] for d in difficulties]
        
        bars = ax.bar(difficulties, accuracies, alpha=0.8, 
                     color=['#2ecc71', '#f39c12', '#e74c3c'][:len(difficulties)])
        
        # Add count labels on bars
        for bar, total in zip(bars, totals):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'n={total}',
                   ha='center', va='bottom', fontsize=10)
        
        ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Difficulty', fontsize=12, fontweight='bold')
        ax.set_title('Accuracy by Difficulty Level', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 110)
        ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='50% baseline')
        ax.legend()
        
        plt.tight_layout()
        output_path = output_dir / 'difficulty_breakdown.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def _plot_source_breakdown(self, source_stats: Dict[str, Any],
                              output_dir: Path) -> str:
        """Plot accuracy by source/dataset"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        sources = list(source_stats.keys())
        accuracies = [source_stats[s]['accuracy'] for s in sources]
        totals = [source_stats[s]['total'] for s in sources]
        
        # Sort by accuracy
        sorted_indices = sorted(range(len(accuracies)), key=lambda i: accuracies[i], reverse=True)
        sources = [sources[i] for i in sorted_indices]
        accuracies = [accuracies[i] for i in sorted_indices]
        totals = [totals[i] for i in sorted_indices]
        
        bars = ax.barh(sources, accuracies, alpha=0.8, color='#3498db')
        
        # Add count labels
        for bar, total in zip(bars, totals):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f' n={total}',
                   ha='left', va='center', fontsize=9)
        
        ax.set_xlabel('Accuracy (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Source', fontsize=12, fontweight='bold')
        ax.set_title('Accuracy by Problem Source', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 110)
        
        plt.tight_layout()
        output_path = output_dir / 'source_breakdown.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def _plot_method_comparison(self, method_stats: Dict[str, Any],
                               output_dir: Path) -> str:
        """Plot comparison of different methods"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        methods = list(method_stats.keys())
        accuracies = [method_stats[m]['accuracy'] for m in methods]
        totals = [method_stats[m]['total'] for m in methods]
        
        bars = ax.bar(methods, accuracies, alpha=0.8, color='#9b59b6')
        
        # Add count labels
        for bar, total in zip(bars, totals):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'n={total}',
                   ha='center', va='bottom', fontsize=10)
        
        ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Method', fontsize=12, fontweight='bold')
        ax.set_title('Accuracy by Solution Method', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 110)
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        output_path = output_dir / 'method_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def _plot_time_distribution(self, solve_times: List[float],
                               output_dir: Path) -> str:
        """Plot distribution of solve times"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Histogram
        ax1.hist(solve_times, bins=30, alpha=0.7, color='#3498db', edgecolor='black')
        ax1.set_xlabel('Solve Time (seconds)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax1.set_title('Solve Time Distribution', fontsize=14, fontweight='bold')
        ax1.axvline(np.median(solve_times), color='red', linestyle='--', 
                   label=f'Median: {np.median(solve_times):.2f}s')
        ax1.legend()
        
        # Box plot
        ax2.boxplot(solve_times, vert=True)
        ax2.set_ylabel('Solve Time (seconds)', fontsize=12, fontweight='bold')
        ax2.set_title('Solve Time Box Plot', fontsize=14, fontweight='bold')
        
        # Add statistics text
        stats_text = f"Mean: {np.mean(solve_times):.2f}s\n"
        stats_text += f"Median: {np.median(solve_times):.2f}s\n"
        stats_text += f"Std: {np.std(solve_times):.2f}s\n"
        stats_text += f"P95: {np.percentile(solve_times, 95):.2f}s"
        
        ax2.text(1.15, np.median(solve_times), stats_text,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        output_path = output_dir / 'time_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def _plot_error_analysis(self, errors: List[Dict[str, Any]],
                            output_dir: Path) -> str:
        """Plot error analysis"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Categorize errors
        error_types = {}
        for error in errors:
            error_type = error.get('error', 'Unknown')
            if error_type:
                # Simplify error messages
                if 'timeout' in error_type.lower():
                    error_type = 'Timeout'
                elif 'syntax' in error_type.lower():
                    error_type = 'Syntax Error'
                elif 'memory' in error_type.lower():
                    error_type = 'Memory Error'
                elif error_type == 'N/A' or not error.get('error'):
                    error_type = 'Wrong Answer'
                else:
                    error_type = 'Other Error'
            else:
                error_type = 'Wrong Answer'
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Sort by frequency
        sorted_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)
        labels = [e[0] for e in sorted_errors]
        counts = [e[1] for e in sorted_errors]
        
        bars = ax.barh(labels, counts, alpha=0.8, color='#e74c3c')
        
        # Add percentage labels
        total_errors = sum(counts)
        for bar, count in zip(bars, counts):
            width = bar.get_width()
            pct = count / total_errors * 100
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f' {count} ({pct:.1f}%)',
                   ha='left', va='center', fontsize=10)
        
        ax.set_xlabel('Count', fontsize=12, fontweight='bold')
        ax.set_title(f'Error Analysis (Total: {total_errors})', 
                    fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        output_path = output_dir / 'error_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def _plot_result_distribution(self, results: List[Dict[str, Any]],
                                 output_dir: Path) -> str:
        """Plot pie chart of result distribution"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        correct = sum(1 for r in results if r.get('is_correct', False))
        incorrect = len(results) - correct
        
        sizes = [correct, incorrect]
        labels = ['Correct', 'Incorrect']
        colors = ['#2ecc71', '#e74c3c']
        explode = (0.1, 0)
        
        ax.pie(sizes, explode=explode, labels=labels, colors=colors,
               autopct='%1.1f%%', shadow=True, startangle=90,
               textprops={'fontsize': 14, 'fontweight': 'bold'})
        
        ax.set_title(f'Result Distribution (Total: {len(results)})',
                    fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        output_path = output_dir / 'result_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def _generate_markdown_report(self, 
                                 results: List[Dict[str, Any]],
                                 metrics: Dict[str, Any],
                                 viz_paths: Dict[str, str],
                                 output_dir: Path,
                                 report_name: str) -> str:
        """Generate markdown report"""
        report_path = output_dir / "README.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# {report_name.replace('_', ' ').title()}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Problems:** {metrics.get('total', 0)}\n")
            f.write(f"- **Correct:** {metrics.get('correct', 0)}\n")
            f.write(f"- **Accuracy:** {metrics.get('accuracy', 0):.2f}%\n")
            f.write(f"- **Average Solve Time:** {metrics.get('avg_solve_time', 0):.2f}s\n")
            f.write(f"- **Total Evaluation Time:** {metrics.get('total_evaluation_time', 0):.2f}s\n\n")
            
            if metrics.get('error_count', 0) > 0:
                f.write(f"- **Errors:** {metrics['error_count']} ({metrics.get('error_rate', 0):.2f}%)\n\n")
            
            # Visualizations
            f.write("## Visualizations\n\n")
            
            if 'accuracy' in viz_paths:
                f.write("### Accuracy Overview\n\n")
                f.write(f"![Accuracy Overview]({Path(viz_paths['accuracy']).name})\n\n")
            
            if 'distribution' in viz_paths:
                f.write("### Result Distribution\n\n")
                f.write(f"![Result Distribution]({Path(viz_paths['distribution']).name})\n\n")
            
            if 'difficulty' in viz_paths:
                f.write("### Accuracy by Difficulty\n\n")
                f.write(f"![Difficulty Breakdown]({Path(viz_paths['difficulty']).name})\n\n")
            
            if 'source' in viz_paths:
                f.write("### Accuracy by Source\n\n")
                f.write(f"![Source Breakdown]({Path(viz_paths['source']).name})\n\n")
            
            if 'method' in viz_paths:
                f.write("### Method Comparison\n\n")
                f.write(f"![Method Comparison]({Path(viz_paths['method']).name})\n\n")
            
            if 'time_dist' in viz_paths:
                f.write("### Solve Time Distribution\n\n")
                f.write(f"![Time Distribution]({Path(viz_paths['time_dist']).name})\n\n")
            
            if 'errors' in viz_paths:
                f.write("### Error Analysis\n\n")
                f.write(f"![Error Analysis]({Path(viz_paths['errors']).name})\n\n")
            
            # Detailed Metrics
            f.write("## Detailed Metrics\n\n")
            
            if metrics.get('by_difficulty'):
                f.write("### By Difficulty\n\n")
                f.write("| Difficulty | Total | Correct | Accuracy |\n")
                f.write("|------------|-------|---------|----------|\n")
                for diff, stats in sorted(metrics['by_difficulty'].items()):
                    f.write(f"| {diff} | {stats['total']} | {stats['correct']} | "
                           f"{stats['accuracy']:.2f}% |\n")
                f.write("\n")
            
            if metrics.get('by_source'):
                f.write("### By Source\n\n")
                f.write("| Source | Total | Correct | Accuracy |\n")
                f.write("|--------|-------|---------|----------|\n")
                for source, stats in sorted(metrics['by_source'].items()):
                    f.write(f"| {source} | {stats['total']} | {stats['correct']} | "
                           f"{stats['accuracy']:.2f}% |\n")
                f.write("\n")
            
            if metrics.get('by_method'):
                f.write("### By Method\n\n")
                f.write("| Method | Total | Correct | Accuracy |\n")
                f.write("|--------|-------|---------|----------|\n")
                for method, stats in sorted(metrics['by_method'].items()):
                    f.write(f"| {method} | {stats['total']} | {stats['correct']} | "
                           f"{stats['accuracy']:.2f}% |\n")
                f.write("\n")
            
            # Sample Results
            f.write("## Sample Results\n\n")
            f.write("### Correct Answers (Sample)\n\n")
            correct_results = [r for r in results if r.get('is_correct', False)][:5]
            for i, result in enumerate(correct_results, 1):
                f.write(f"{i}. **Problem:** {result.get('problem', '')[:100]}...\n")
                f.write(f"   - **Answer:** {result.get('predicted_answer', 'N/A')}\n")
                f.write(f"   - **Time:** {result.get('solve_time', 0):.2f}s\n\n")
            
            f.write("### Incorrect Answers (Sample)\n\n")
            incorrect_results = [r for r in results if not r.get('is_correct', False)][:5]
            for i, result in enumerate(incorrect_results, 1):
                f.write(f"{i}. **Problem:** {result.get('problem', '')[:100]}...\n")
                f.write(f"   - **Expected:** {result.get('reference_answer', 'N/A')}\n")
                f.write(f"   - **Got:** {result.get('predicted_answer', 'N/A')}\n")
                if result.get('error'):
                    f.write(f"   - **Error:** {result['error'][:100]}\n")
                f.write("\n")
            
            # Footer
            f.write("---\n\n")
            f.write("*Generated by OMI Comprehensive Evaluation Framework*\n")
        
        return str(report_path)


class ProgressTracker:
    """Track evaluation progress over multiple runs"""
    
    def __init__(self, tracking_file: str = "progress_tracking.json"):
        self.tracking_file = Path(tracking_file)
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load tracking history"""
        if self.tracking_file.exists():
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_history(self):
        """Save tracking history"""
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2)
    
    def add_run(self, run_data: Dict[str, Any]):
        """Add a new run to history"""
        run_data['timestamp'] = datetime.now().isoformat()
        self.history.append(run_data)
        self.save_history()
    
    def plot_progress(self, metric: str = 'accuracy', output_path: Optional[str] = None):
        """Plot progress over time"""
        if not self.history:
            print("No history to plot")
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        timestamps = [datetime.fromisoformat(run['timestamp']) for run in self.history]
        values = [run.get(metric, 0) for run in self.history]
        
        ax.plot(timestamps, values, marker='o', linewidth=2, markersize=8)
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel(metric.replace('_', ' ').title(), fontsize=12, fontweight='bold')
        ax.set_title(f'{metric.replace("_", " ").title()} Progress Over Time', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if output_path is None:
            output_path = f'progress_{metric}.png'
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Progress plot saved to: {output_path}")
