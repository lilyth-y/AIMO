"""
평가 모듈
통합된 평가 유틸리티를 제공합니다.
"""

from .evaluation_utils import (
    EvaluationResult,
    EvaluationMetrics,
    check_answer_correctness,
    classify_answer_match,
    extract_aime_answer,
    determine_difficulty_from_source
)

from . import config

# Advanced evaluation modules (optional imports)
try:
    from .advanced_metrics import (
        AdvancedMetrics,
        AdvancedEvaluator,
        ErrorCategorizer,
        bootstrap_confidence_interval,
        calculate_effect_size
    )
    _has_advanced_metrics = True
except ImportError:
    _has_advanced_metrics = False
    AdvancedMetrics = None
    AdvancedEvaluator = None
    ErrorCategorizer = None

try:
    from .benchmarking import (
        BenchmarkManager,
        BenchmarkRun,
        CrossValidation
    )
    _has_benchmarking = True
except ImportError:
    _has_benchmarking = False
    BenchmarkManager = None
    BenchmarkRun = None
    CrossValidation = None

try:
    from .comprehensive_reporting import (
        ComprehensiveReporter,
        ProgressTracker
    )
    _has_reporting = True
except ImportError:
    _has_reporting = False
    ComprehensiveReporter = None
    ProgressTracker = None

try:
    from .mathematical_devops_gradients import (
        evaluate_mathematical_and_devops,
        compute_difficulty_gradient,
        get_gradient_levels_documentation,
        MATHEMATICAL_GRADIENT_LEVELS,
        DEVOPS_GRADIENT_LEVELS,
    )
    _has_gradients = True
except ImportError:
    _has_gradients = False
    evaluate_mathematical_and_devops = None
    compute_difficulty_gradient = None
    get_gradient_levels_documentation = None
    MATHEMATICAL_GRADIENT_LEVELS = None
    DEVOPS_GRADIENT_LEVELS = None

__all__ = [
    'EvaluationResult',
    'EvaluationMetrics',
    'check_answer_correctness',
    'classify_answer_match',
    'extract_aime_answer',
    'determine_difficulty_from_source',
    'config'
]

# Add advanced features if available
if _has_advanced_metrics:
    __all__.extend([
        'AdvancedMetrics',
        'AdvancedEvaluator',
        'ErrorCategorizer'
    ])

if _has_benchmarking:
    __all__.extend([
        'BenchmarkManager',
        'BenchmarkRun',
        'CrossValidation'
    ])

if _has_reporting:
    __all__.extend([
        'ComprehensiveReporter',
        'ProgressTracker'
    ])

if _has_gradients:
    __all__.extend([
        'evaluate_mathematical_and_devops',
        'compute_difficulty_gradient',
        'get_gradient_levels_documentation',
        'MATHEMATICAL_GRADIENT_LEVELS',
        'DEVOPS_GRADIENT_LEVELS',
    ])
