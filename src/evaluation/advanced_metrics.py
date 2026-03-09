"""
Advanced Evaluation Metrics
- Statistical significance testing
- Confidence intervals
- Error analysis and categorization
- Performance profiling
- Distribution analysis
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import time
from collections import defaultdict


@dataclass
class AdvancedMetrics:
    """Advanced statistical metrics for evaluation"""
    
    # Basic metrics
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    
    # Confidence intervals
    accuracy_ci: Tuple[float, float]
    confidence_level: float = 0.95
    
    # Statistical tests
    p_value: Optional[float] = None
    is_significant: Optional[bool] = None
    
    # Error analysis
    error_types: Dict[str, int] = None
    error_rate_by_category: Dict[str, float] = None
    
    # Performance metrics
    avg_latency: float = 0.0
    p50_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    
    # Distribution metrics
    accuracy_by_quantile: Dict[str, float] = None


class AdvancedEvaluator:
    """
    Advanced evaluation with statistical rigor
    """
    
    def __init__(self):
        self.results = []
        self.error_categories = defaultdict(list)
        self.latencies = []
    
    def add_result(self, is_correct: bool, latency: float, 
                   error_type: Optional[str] = None,
                   metadata: Optional[Dict] = None):
        """Add evaluation result"""
        self.results.append({
            'is_correct': is_correct,
            'latency': latency,
            'error_type': error_type,
            'metadata': metadata or {}
        })
        self.latencies.append(latency)
        
        if error_type:
            self.error_categories[error_type].append(metadata)
    
    def calculate_confidence_interval(self, 
                                     confidence_level: float = 0.95) -> Tuple[float, float]:
        """
        Calculate confidence interval for accuracy using Wilson score interval
        
        Args:
            confidence_level: Confidence level (default 0.95 for 95% CI)
        
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if not self.results:
            return (0.0, 0.0)
        
        n = len(self.results)
        correct = sum(1 for r in self.results if r['is_correct'])
        p_hat = correct / n
        
        # Wilson score interval
        from scipy import stats
        z = stats.norm.ppf((1 + confidence_level) / 2)
        
        denominator = 1 + z**2 / n
        center = (p_hat + z**2 / (2*n)) / denominator
        margin = z * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4*n**2)) / denominator
        
        return (max(0, center - margin), min(1, center + margin))
    
    def mcnemar_test(self, other_results: List[bool]) -> Tuple[float, bool]:
        """
        McNemar's test for comparing two models
        
        Args:
            other_results: List of boolean results from another model
        
        Returns:
            Tuple of (p_value, is_significant)
        """
        from scipy import stats
        
        if len(self.results) != len(other_results):
            raise ValueError("Result lists must have same length")
        
        # Create contingency table
        # b: model1 correct, model2 incorrect
        # c: model1 incorrect, model2 correct
        b = sum(1 for i, r in enumerate(self.results) 
                if r['is_correct'] and not other_results[i])
        c = sum(1 for i, r in enumerate(self.results) 
                if not r['is_correct'] and other_results[i])
        
        if b + c == 0:
            return 1.0, False
        
        # McNemar's test statistic
        chi2 = (abs(b - c) - 1)**2 / (b + c)
        p_value = 1 - stats.chi2.cdf(chi2, 1)
        
        is_significant = p_value < 0.05
        
        return p_value, is_significant
    
    def analyze_errors(self) -> Dict[str, Any]:
        """
        Comprehensive error analysis
        
        Returns:
            Dictionary with error statistics
        """
        if not self.results:
            return {}
        
        total = len(self.results)
        errors = [r for r in self.results if not r['is_correct']]
        error_count = len(errors)
        
        # Error types distribution
        error_type_counts = defaultdict(int)
        for r in errors:
            if r['error_type']:
                error_type_counts[r['error_type']] += 1
            else:
                error_type_counts['unknown'] += 1
        
        # Error rate by category
        error_rates = {
            error_type: count / error_count if error_count > 0 else 0
            for error_type, count in error_type_counts.items()
        }
        
        # Most common error patterns
        error_metadata = defaultdict(list)
        for r in errors:
            if r['error_type']:
                error_metadata[r['error_type']].append(r['metadata'])
        
        return {
            'total_errors': error_count,
            'error_rate': error_count / total if total > 0 else 0,
            'error_types': dict(error_type_counts),
            'error_rates_by_type': error_rates,
            'error_metadata': dict(error_metadata)
        }
    
    def calculate_latency_metrics(self) -> Dict[str, float]:
        """
        Calculate latency percentiles and statistics
        
        Returns:
            Dictionary with latency metrics
        """
        if not self.latencies:
            return {}
        
        latencies = np.array(self.latencies)
        
        return {
            'mean': float(np.mean(latencies)),
            'median': float(np.median(latencies)),
            'std': float(np.std(latencies)),
            'min': float(np.min(latencies)),
            'max': float(np.max(latencies)),
            'p50': float(np.percentile(latencies, 50)),
            'p90': float(np.percentile(latencies, 90)),
            'p95': float(np.percentile(latencies, 95)),
            'p99': float(np.percentile(latencies, 99))
        }
    
    def accuracy_by_difficulty_quantile(self, 
                                       difficulty_scores: List[float],
                                       n_quantiles: int = 4) -> Dict[str, float]:
        """
        Calculate accuracy by difficulty quantile
        
        Args:
            difficulty_scores: List of difficulty scores for each problem
            n_quantiles: Number of quantiles to divide into
        
        Returns:
            Dictionary mapping quantile to accuracy
        """
        if len(difficulty_scores) != len(self.results):
            raise ValueError("Difficulty scores must match results length")
        
        # Create quantiles
        quantiles = np.quantile(difficulty_scores, 
                               np.linspace(0, 1, n_quantiles + 1))
        
        # Group results by quantile
        quantile_results = defaultdict(list)
        for i, score in enumerate(difficulty_scores):
            for q in range(n_quantiles):
                if quantiles[q] <= score <= quantiles[q + 1]:
                    quantile_results[f'Q{q+1}'].append(
                        self.results[i]['is_correct']
                    )
                    break
        
        # Calculate accuracy per quantile
        quantile_accuracy = {}
        for quantile, results in quantile_results.items():
            if results:
                quantile_accuracy[quantile] = sum(results) / len(results)
        
        return quantile_accuracy
    
    def calculate_comprehensive_metrics(self,
                                       other_results: Optional[List[bool]] = None,
                                       difficulty_scores: Optional[List[float]] = None
                                       ) -> AdvancedMetrics:
        """
        Calculate all advanced metrics
        
        Args:
            other_results: Optional comparison results from another model
            difficulty_scores: Optional difficulty scores for quantile analysis
        
        Returns:
            AdvancedMetrics object with all metrics
        """
        if not self.results:
            raise ValueError("No results to analyze")
        
        # Basic metrics
        total = len(self.results)
        correct = sum(1 for r in self.results if r['is_correct'])
        accuracy = correct / total if total > 0 else 0
        
        # For classification metrics (treating as binary)
        true_positives = correct
        false_negatives = total - correct
        # Assuming we don't have false positives/true negatives info
        precision = accuracy  # Simplified
        recall = accuracy
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Confidence interval
        ci = self.calculate_confidence_interval()
        
        # Statistical test
        p_value = None
        is_significant = None
        if other_results:
            p_value, is_significant = self.mcnemar_test(other_results)
        
        # Error analysis
        error_analysis = self.analyze_errors()
        
        # Latency metrics
        latency_metrics = self.calculate_latency_metrics()
        
        # Quantile analysis
        quantile_accuracy = None
        if difficulty_scores:
            try:
                quantile_accuracy = self.accuracy_by_difficulty_quantile(difficulty_scores)
            except Exception:
                pass
        
        return AdvancedMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            accuracy_ci=ci,
            confidence_level=0.95,
            p_value=p_value,
            is_significant=is_significant,
            error_types=error_analysis.get('error_types'),
            error_rate_by_category=error_analysis.get('error_rates_by_type'),
            avg_latency=latency_metrics.get('mean', 0.0),
            p50_latency=latency_metrics.get('p50', 0.0),
            p95_latency=latency_metrics.get('p95', 0.0),
            p99_latency=latency_metrics.get('p99', 0.0),
            accuracy_by_quantile=quantile_accuracy
        )


class ErrorCategorizer:
    """Categorize and analyze different types of errors"""
    
    ERROR_CATEGORIES = {
        'syntax_error': 'Code syntax error',
        'runtime_error': 'Runtime execution error',
        'timeout': 'Execution timeout',
        'wrong_answer': 'Incorrect answer',
        'parsing_error': 'Answer parsing error',
        'oom_error': 'Out of memory',
        'unknown': 'Unknown error'
    }
    
    @staticmethod
    def categorize_error(error_message: str) -> str:
        """
        Categorize error based on error message
        
        Args:
            error_message: Error message string
        
        Returns:
            Error category
        """
        if not error_message:
            return 'unknown'
        
        error_lower = error_message.lower()
        
        if any(keyword in error_lower for keyword in ['syntax', 'syntaxerror', 'invalid syntax']):
            return 'syntax_error'
        elif any(keyword in error_lower for keyword in ['timeout', 'time limit']):
            return 'timeout'
        elif any(keyword in error_lower for keyword in ['memory', 'oom', 'out of memory']):
            return 'oom_error'
        elif any(keyword in error_lower for keyword in ['name', 'attribute', 'key', 'index']):
            return 'runtime_error'
        elif 'parsing' in error_lower or 'parse' in error_lower:
            return 'parsing_error'
        elif 'wrong' in error_lower or 'incorrect' in error_lower:
            return 'wrong_answer'
        else:
            return 'unknown'
    
    @staticmethod
    def analyze_error_patterns(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze patterns in errors
        
        Args:
            errors: List of error dictionaries
        
        Returns:
            Analysis results
        """
        if not errors:
            return {}
        
        # Categorize all errors
        categorized = defaultdict(list)
        for error in errors:
            category = ErrorCategorizer.categorize_error(
                error.get('error', '') or error.get('error_message', '')
            )
            categorized[category].append(error)
        
        # Calculate statistics
        total = len(errors)
        category_stats = {}
        for category, error_list in categorized.items():
            count = len(error_list)
            category_stats[category] = {
                'count': count,
                'percentage': count / total * 100,
                'description': ErrorCategorizer.ERROR_CATEGORIES.get(category, 'Unknown'),
                'examples': error_list[:3]  # First 3 examples
            }
        
        return {
            'total_errors': total,
            'by_category': category_stats,
            'most_common': max(categorized.items(), key=lambda x: len(x[1]))[0] if categorized else None
        }


def bootstrap_confidence_interval(results: List[bool], 
                                  n_bootstrap: int = 10000,
                                  confidence_level: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval using bootstrap resampling
    
    Args:
        results: List of boolean results
        n_bootstrap: Number of bootstrap samples
        confidence_level: Confidence level
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    results_array = np.array(results, dtype=float)
    n = len(results_array)
    
    # Bootstrap resampling
    bootstrap_accuracies = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(results_array, size=n, replace=True)
        bootstrap_accuracies.append(np.mean(sample))
    
    # Calculate percentiles
    alpha = 1 - confidence_level
    lower = np.percentile(bootstrap_accuracies, alpha/2 * 100)
    upper = np.percentile(bootstrap_accuracies, (1 - alpha/2) * 100)
    
    return (lower, upper)


def calculate_effect_size(results1: List[bool], results2: List[bool]) -> float:
    """
    Calculate Cohen's h effect size for difference in proportions
    
    Args:
        results1: Results from model 1
        results2: Results from model 2
    
    Returns:
        Effect size (Cohen's h)
    """
    p1 = np.mean(results1)
    p2 = np.mean(results2)
    
    # Cohen's h
    h = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))
    
    return h
