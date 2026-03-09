"""
Revolving Resolution Framework
- Iterative problem-solving with strategy adaptation
- Multi-path solution exploration
- Meta-learning from successes and failures
- Confidence-based solution selection
"""

from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import time
from collections import defaultdict
import json


class ResolutionStatus(Enum):
    """Status of resolution attempt"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


class StrategyType(Enum):
    """Types of solution strategies"""
    DIRECT_COMPUTATION = "direct_computation"
    ALGEBRAIC_MANIPULATION = "algebraic_manipulation"
    NUMERICAL_APPROXIMATION = "numerical_approximation"
    SYMBOLIC_SOLVING = "symbolic_solving"
    HEURISTIC_SEARCH = "heuristic_search"
    PATTERN_MATCHING = "pattern_matching"
    ITERATIVE_REFINEMENT = "iterative_refinement"
    THEOREM_APPLICATION = "theorem_application"
    CASE_ANALYSIS = "case_analysis"
    REDUCTION = "reduction"


@dataclass
class SolutionAttempt:
    """Single solution attempt result"""
    strategy: StrategyType
    answer: Optional[str]
    confidence: float
    is_verified: bool
    execution_time: float
    error_message: Optional[str] = None
    intermediate_steps: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.intermediate_steps is None:
            self.intermediate_steps = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
@dataclass
class ProblemContext:
    """Enriched problem context for resolution"""
    problem_text: str
    domain: str
    difficulty: str
    features: Dict[str, Any]
    constraints: List[str] = None
    keywords: List[str] = None
    similar_problems: List[str] = None
    
    def __post_init__(self):
        if self.similar_problems is None:
            self.similar_problems = []
        if self.constraints is None:
            self.constraints = []
        if self.keywords is None:
            self.keywords = []


class StrategySelector:
    """
    Intelligent strategy selection based on problem features and history
    """
    
    def __init__(self):
        self.strategy_history = defaultdict(lambda: {'attempts': 0, 'successes': 0})
        self.problem_strategy_map = defaultdict(list)
    
    def select_best_strategy(self, 
                            problem_context: ProblemContext,
                            available_strategies: List[StrategyType],
                            tried_strategies: List[StrategyType]) -> StrategyType:
        """
        Select the best strategy for the problem
        
        Args:
            problem_context: Problem context information
            available_strategies: List of available strategies
            tried_strategies: Strategies already tried
        
        Returns:
            Best strategy to try next
        """
        untried = [s for s in available_strategies if s not in tried_strategies]
        
        if not untried:
            # All strategies tried, return the one with highest historical success
            return self._get_best_historical_strategy(available_strategies)
        
        # Score each untried strategy
        scores = {}
        for strategy in untried:
            score = self._calculate_strategy_score(strategy, problem_context)
            scores[strategy] = score
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _calculate_strategy_score(self, 
                                  strategy: StrategyType,
                                  context: ProblemContext) -> float:
        """Calculate compatibility score for strategy"""
        score = 0.0
        
        # Factor 1: Historical success rate (40%)
        history = self.strategy_history[strategy]
        if history['attempts'] > 0:
            success_rate = history['successes'] / history['attempts']
            score += 0.4 * success_rate
        else:
            score += 0.2  # Default score for untried strategies
        
        # Factor 2: Domain compatibility (30%)
        domain_compatibility = self._assess_domain_compatibility(strategy, context.domain)
        score += 0.3 * domain_compatibility
        
        # Factor 3: Feature matching (20%)
        feature_match = self._assess_feature_matching(strategy, context.features)
        score += 0.2 * feature_match
        
        # Factor 4: Difficulty appropriateness (10%)
        difficulty_match = self._assess_difficulty_match(strategy, context.difficulty)
        score += 0.1 * difficulty_match
        
        return score
    
    def _assess_domain_compatibility(self, strategy: StrategyType, domain: str) -> float:
        """Assess how well strategy matches domain"""
        compatibility_map = {
            StrategyType.ALGEBRAIC_MANIPULATION: {
                'algebra': 1.0, 'number_theory': 0.7, 'calculus': 0.6
            },
            StrategyType.NUMERICAL_APPROXIMATION: {
                'calculus': 1.0, 'analysis': 0.9, 'geometry': 0.5
            },
            StrategyType.SYMBOLIC_SOLVING: {
                'algebra': 0.9, 'calculus': 0.8, 'number_theory': 0.7
            },
            StrategyType.DIRECT_COMPUTATION: {
                'arithmetic': 1.0, 'algebra': 0.8, 'number_theory': 0.6
            },
            StrategyType.PATTERN_MATCHING: {
                'combinatorics': 0.9, 'number_theory': 0.8, 'algebra': 0.6
            },
            StrategyType.THEOREM_APPLICATION: {
                'geometry': 0.9, 'number_theory': 0.8, 'combinatorics': 0.7
            }
        }
        
        if strategy in compatibility_map:
            return compatibility_map[strategy].get(domain, 0.5)
        return 0.5
    
    def _assess_feature_matching(self, strategy: StrategyType, features: Dict) -> float:
        """Assess how well strategy matches problem features"""
        # Simplified feature matching
        score = 0.5
        
        # Check for specific feature-strategy alignments
        if features.get('has_equations') and strategy == StrategyType.SYMBOLIC_SOLVING:
            score += 0.3
        if features.get('requires_approximation') and strategy == StrategyType.NUMERICAL_APPROXIMATION:
            score += 0.3
        if features.get('has_pattern') and strategy == StrategyType.PATTERN_MATCHING:
            score += 0.3
        
        return min(score, 1.0)
    
    def _assess_difficulty_match(self, strategy: StrategyType, difficulty: str) -> float:
        """Assess if strategy is appropriate for difficulty level"""
        difficulty_map = {
            'easy': {
                StrategyType.DIRECT_COMPUTATION: 1.0,
                StrategyType.ALGEBRAIC_MANIPULATION: 0.8
            },
            'medium': {
                StrategyType.ALGEBRAIC_MANIPULATION: 1.0,
                StrategyType.SYMBOLIC_SOLVING: 0.9,
                StrategyType.PATTERN_MATCHING: 0.8
            },
            'hard': {
                StrategyType.SYMBOLIC_SOLVING: 1.0,
                StrategyType.THEOREM_APPLICATION: 0.9,
                StrategyType.CASE_ANALYSIS: 0.9,
                StrategyType.ITERATIVE_REFINEMENT: 0.8
            }
        }
        
        if difficulty in difficulty_map:
            return difficulty_map[difficulty].get(strategy, 0.5)
        return 0.5
    
    def _get_best_historical_strategy(self, strategies: List[StrategyType]) -> StrategyType:
        """Get strategy with best historical performance"""
        best_strategy = strategies[0]
        best_rate = 0.0
        
        for strategy in strategies:
            history = self.strategy_history[strategy]
            if history['attempts'] > 0:
                rate = history['successes'] / history['attempts']
                if rate > best_rate:
                    best_rate = rate
                    best_strategy = strategy
        
        return best_strategy
    
    def update_history(self, strategy: StrategyType, success: bool):
        """Update strategy history"""
        self.strategy_history[strategy]['attempts'] += 1
        if success:
            self.strategy_history[strategy]['successes'] += 1


class RevolvingResolver:
    """
    Main revolving resolution framework
    Iteratively attempts to solve problems with strategy adaptation
    """
    
    def __init__(self, 
                 max_iterations: int = 5,
                 confidence_threshold: float = 0.8,
                 time_budget: float = 120.0):
        """
        Initialize resolver
        
        Args:
            max_iterations: Maximum number of solution attempts
            confidence_threshold: Minimum confidence for early stopping
            time_budget: Maximum time budget in seconds
        """
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
        self.time_budget = time_budget
        self.strategy_selector = StrategySelector()
        self.solution_history = []
    
    def resolve(self, 
                problem_context: ProblemContext,
                solver_fn: Callable) -> Tuple[Optional[str], ResolutionStatus, Dict[str, Any]]:
        """
        Resolve problem using revolving strategy
        
        Args:
            problem_context: Problem context
            solver_fn: Function that attempts to solve problem with given strategy
        
        Returns:
            Tuple of (answer, status, metadata)
        """
        start_time = time.time()
        iteration = 0
        tried_strategies = []
        all_attempts = []
        best_attempt = None
        
        # Get available strategies
        available_strategies = self._get_available_strategies(problem_context)
        
        while iteration < self.max_iterations:
            # Check time budget
            if time.time() - start_time > self.time_budget:
                return (
                    best_attempt.answer if best_attempt else None,
                    ResolutionStatus.TIMEOUT,
                    self._create_metadata(all_attempts, "timeout")
                )
            
            # Select strategy
            strategy = self.strategy_selector.select_best_strategy(
                problem_context,
                available_strategies,
                tried_strategies
            )
            tried_strategies.append(strategy)
            
            # Attempt solution
            attempt = self._attempt_solution(
                problem_context,
                strategy,
                solver_fn
            )
            all_attempts.append(attempt)
            
            # Update best attempt
            if attempt.is_verified and (
                best_attempt is None or 
                attempt.confidence > best_attempt.confidence
            ):
                best_attempt = attempt
                
                # Early stopping if high confidence
                if attempt.confidence >= self.confidence_threshold:
                    self.strategy_selector.update_history(strategy, True)
                    return (
                        best_attempt.answer,
                        ResolutionStatus.SUCCESS,
                        self._create_metadata(all_attempts, "success_early_stop")
                    )
            
            # Update strategy history
            self.strategy_selector.update_history(strategy, attempt.is_verified)
            
            iteration += 1
        
        # All iterations exhausted
        if best_attempt and best_attempt.is_verified:
            return (
                best_attempt.answer,
                ResolutionStatus.SUCCESS,
                self._create_metadata(all_attempts, "success_full_iterations")
            )
        elif best_attempt:
            return (
                best_attempt.answer,
                ResolutionStatus.PARTIAL,
                self._create_metadata(all_attempts, "partial_solution")
            )
        else:
            return (
                None,
                ResolutionStatus.FAILURE,
                self._create_metadata(all_attempts, "all_attempts_failed")
            )
    
    def _get_available_strategies(self, context: ProblemContext) -> List[StrategyType]:
        """Get list of applicable strategies based on problem context"""
        # Start with all strategies
        strategies = list(StrategyType)
        
        # Filter based on problem features
        if context.features.get('is_simple_arithmetic'):
            return [StrategyType.DIRECT_COMPUTATION]
        
        if context.difficulty == 'easy':
            strategies = [
                StrategyType.DIRECT_COMPUTATION,
                StrategyType.ALGEBRAIC_MANIPULATION,
                StrategyType.SYMBOLIC_SOLVING
            ]
        elif context.difficulty == 'medium':
            strategies = [
                StrategyType.ALGEBRAIC_MANIPULATION,
                StrategyType.SYMBOLIC_SOLVING,
                StrategyType.PATTERN_MATCHING,
                StrategyType.NUMERICAL_APPROXIMATION
            ]
        # For hard problems, all strategies available
        
        return strategies
    
    def _attempt_solution(self,
                         context: ProblemContext,
                         strategy: StrategyType,
                         solver_fn: Callable) -> SolutionAttempt:
        """Attempt to solve problem with given strategy"""
        start_time = time.time()
        
        try:
            # Call solver with strategy hint
            result = solver_fn(context.problem_text, strategy)
            execution_time = time.time() - start_time
            
            # Extract solution components
            answer = result.get('answer', None)
            confidence = result.get('confidence', 0.5)
            is_verified = result.get('verified', False)
            steps = result.get('steps', [])
            
            return SolutionAttempt(
                strategy=strategy,
                answer=answer,
                confidence=confidence,
                is_verified=is_verified,
                execution_time=execution_time,
                intermediate_steps=steps,
                metadata=result.get('metadata', {})
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return SolutionAttempt(
                strategy=strategy,
                answer=None,
                confidence=0.0,
                is_verified=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _create_metadata(self, attempts: List[SolutionAttempt], reason: str) -> Dict[str, Any]:
        """Create metadata from all attempts"""
        return {
            'total_attempts': len(attempts),
            'strategies_tried': [a.strategy.value for a in attempts],
            'best_confidence': max([a.confidence for a in attempts]) if attempts else 0.0,
            'total_time': sum([a.execution_time for a in attempts]),
            'verified_attempts': sum([1 for a in attempts if a.is_verified]),
            'reason': reason,
            'all_attempts': [
                {
                    'strategy': a.strategy.value,
                    'confidence': a.confidence,
                    'verified': a.is_verified,
                    'time': a.execution_time,
                    'error': a.error_message
                }
                for a in attempts
            ]
        }
    
    def get_solution_history(self) -> List[Dict[str, Any]]:
        """Get history of all solutions"""
        return self.solution_history


class MultiPathExplorer:
    """
    Explore multiple solution paths in parallel and synthesize results
    """
    
    def __init__(self, n_paths: int = 3):
        self.n_paths = n_paths
    
    def explore(self,
                problem_context: ProblemContext,
                solver_fn: Callable,
                strategies: Optional[List[StrategyType]] = None) -> Tuple[str, float, Dict]:
        """
        Explore multiple solution paths
        
        Args:
            problem_context: Problem context
            solver_fn: Solver function
            strategies: Optional list of strategies to try
        
        Returns:
            Tuple of (answer, confidence, metadata)
        """
        if strategies is None:
            strategies = self._select_diverse_strategies(problem_context)
        
        # Execute all strategies
        attempts = []
        for strategy in strategies[:self.n_paths]:
            try:
                result = solver_fn(problem_context.problem_text, strategy)
                attempts.append((result, strategy))
            except Exception as e:
                attempts.append(({'error': str(e)}, strategy))
        
        # Analyze consensus
        answers = [a[0].get('answer') for a in attempts if a[0].get('answer')]
        
        if not answers:
            return None, 0.0, {'reason': 'all_paths_failed'}
        
        # Check for consensus
        if len(set(answers)) == 1:
            # All paths agree
            return answers[0], 0.95, {
                'consensus': True,
                'paths': len(answers),
                'strategies': [a[1].value for a in attempts]
            }
        
        # Partial consensus or conflict
        answer_counts = defaultdict(int)
        for ans in answers:
            answer_counts[ans] += 1
        
        # Return most common answer
        best_answer = max(answer_counts.items(), key=lambda x: x[1])
        confidence = best_answer[1] / len(answers)
        
        return best_answer[0], confidence, {
            'consensus': False,
            'agreement_rate': confidence,
            'answer_distribution': dict(answer_counts),
            'strategies': [a[1].value for a in attempts]
        }
    
    def _select_diverse_strategies(self, context: ProblemContext) -> List[StrategyType]:
        """Select diverse strategies to maximize coverage"""
        # Select strategies from different categories
        diverse_strategies = [
            StrategyType.DIRECT_COMPUTATION,
            StrategyType.SYMBOLIC_SOLVING,
            StrategyType.NUMERICAL_APPROXIMATION
        ]
        
        # Adjust based on difficulty
        if context.difficulty == 'hard':
            diverse_strategies = [
                StrategyType.SYMBOLIC_SOLVING,
                StrategyType.THEOREM_APPLICATION,
                StrategyType.CASE_ANALYSIS
            ]
        
        return diverse_strategies


class AdaptiveLearner:
    """
    Learn from solution attempts and adapt strategies
    """
    
    def __init__(self):
        self.problem_patterns = defaultdict(list)
        self.strategy_effectiveness = defaultdict(lambda: defaultdict(float))
    
    def record_attempt(self,
                      problem_features: Dict[str, Any],
                      strategy: StrategyType,
                      success: bool,
                      confidence: float):
        """Record solution attempt for learning"""
        pattern_key = self._extract_pattern(problem_features)
        
        self.problem_patterns[pattern_key].append({
            'strategy': strategy,
            'success': success,
            'confidence': confidence
        })
        
        # Update effectiveness
        current = self.strategy_effectiveness[pattern_key][strategy]
        # Exponential moving average
        alpha = 0.3
        new_value = 1.0 if success else 0.0
        self.strategy_effectiveness[pattern_key][strategy] = (
            alpha * new_value + (1 - alpha) * current
        )
    
    def get_recommended_strategies(self,
                                  problem_features: Dict[str, Any],
                                  n: int = 3) -> List[StrategyType]:
        """Get recommended strategies based on learned patterns"""
        pattern_key = self._extract_pattern(problem_features)
        
        if pattern_key not in self.strategy_effectiveness:
            # No history, return default strategies
            return [
                StrategyType.SYMBOLIC_SOLVING,
                StrategyType.ALGEBRAIC_MANIPULATION,
                StrategyType.DIRECT_COMPUTATION
            ]
        
        # Sort strategies by effectiveness
        effectiveness = self.strategy_effectiveness[pattern_key]
        sorted_strategies = sorted(
            effectiveness.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [s[0] for s in sorted_strategies[:n]]
    
    def _extract_pattern(self, features: Dict[str, Any]) -> str:
        """Extract pattern key from features"""
        # Create a simple pattern key
        key_features = [
            features.get('domain', 'unknown'),
            features.get('difficulty', 'unknown'),
            features.get('has_equations', False),
            features.get('requires_approximation', False)
        ]
        return str(tuple(key_features))
    
    def export_knowledge(self, filepath: str):
        """Export learned knowledge"""
        knowledge = {
            'problem_patterns': dict(self.problem_patterns),
            'strategy_effectiveness': {
                k: dict(v) for k, v in self.strategy_effectiveness.items()
            }
        }
        with open(filepath, 'w') as f:
            json.dump(knowledge, f, indent=2, default=str)
    
    def import_knowledge(self, filepath: str):
        """Import learned knowledge"""
        with open(filepath, 'r') as f:
            knowledge = json.load(f)
        
        self.problem_patterns = defaultdict(list, knowledge['problem_patterns'])
        self.strategy_effectiveness = defaultdict(
            lambda: defaultdict(float),
            {k: defaultdict(float, v) for k, v in knowledge['strategy_effectiveness'].items()}
        )
