"""
통합 평가 유틸리티
- 표준화된 평가 메트릭 계산
- 일관된 결과 저장 형식
- 개선된 에러 처리 및 로깅
"""

import json
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Import reasoning_utils with fallback
try:
    from ..pipeline.reasoning_utils import normalize_answer, sympy_equivalent
except ImportError:
    # Fallback for direct import
    try:
        from pipeline.reasoning_utils import normalize_answer, sympy_equivalent
    except ImportError:
        # Minimal fallback implementations
        def normalize_answer(ans: str) -> str:
            if not ans:
                return ""
            return str(ans).strip().replace(" ", "")
        
        def sympy_equivalent(a: str, b: str) -> bool:
            return normalize_answer(a) == normalize_answer(b)


class EvaluationResult:
    """평가 결과를 저장하는 표준 클래스"""
    
    def __init__(self, problem_id: Any, problem: str, 
                 reference_answer: Optional[str] = None,
                 predicted_answer: Optional[str] = None,
                 is_correct: bool = False,
                 solve_time: float = 0.0,
                 method: str = 'unknown',
                 difficulty: Optional[str] = None,
                 source: Optional[str] = None,
                 error: Optional[str] = None,
                 metadata: Optional[Dict] = None):
        self.problem_id = problem_id
        self.problem = problem
        self.reference_answer = reference_answer
        self.predicted_answer = predicted_answer
        self.is_correct = is_correct
        self.solve_time = solve_time
        self.method = method
        self.difficulty = difficulty
        self.source = source
        self.error = error
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'problem_id': self.problem_id,
            'problem': self.problem[:200] + '...' if len(self.problem) > 200 else self.problem,
            'reference_answer': self.reference_answer,
            'predicted_answer': self.predicted_answer,
            'is_correct': self.is_correct,
            'solve_time': self.solve_time,
            'method': self.method,
            'difficulty': self.difficulty,
            'source': self.source,
            'error': self.error,
            **self.metadata
        }


class EvaluationMetrics:
    """평가 메트릭을 계산하고 저장하는 클래스"""
    
    def __init__(self, dataset_name: str = "unknown"):
        self.dataset_name = dataset_name
        self.results: List[EvaluationResult] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def start(self):
        """평가 시작 시간 기록"""
        self.start_time = time.time()
    
    def finish(self):
        """평가 종료 시간 기록"""
        self.end_time = time.time()
    
    def add_result(self, result: EvaluationResult):
        """결과 추가"""
        self.results.append(result)
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """메트릭 계산"""
        if not self.results:
            return {
                'total': 0,
                'correct': 0,
                'accuracy': 0.0,
                'avg_time': 0.0
            }
        
        total = len(self.results)
        correct = sum(1 for r in self.results if r.is_correct)
        accuracy = (correct / total * 100) if total > 0 else 0.0
        
        solve_times = [r.solve_time for r in self.results if r.solve_time > 0]
        avg_time = sum(solve_times) / len(solve_times) if solve_times else 0.0
        
        total_time = (self.end_time - self.start_time) if (self.start_time and self.end_time) else 0.0
        
        # 난이도별 통계
        by_difficulty = {}
        for result in self.results:
            if result.difficulty:
                if result.difficulty not in by_difficulty:
                    by_difficulty[result.difficulty] = {'total': 0, 'correct': 0}
                by_difficulty[result.difficulty]['total'] += 1
                if result.is_correct:
                    by_difficulty[result.difficulty]['correct'] += 1
        
        # 난이도별 정확도 계산
        difficulty_accuracy = {}
        for diff, stats in by_difficulty.items():
            difficulty_accuracy[diff] = {
                'total': stats['total'],
                'correct': stats['correct'],
                'accuracy': (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
            }
        
        # 소스별 통계
        by_source = {}
        for result in self.results:
            if result.source:
                if result.source not in by_source:
                    by_source[result.source] = {'total': 0, 'correct': 0}
                by_source[result.source]['total'] += 1
                if result.is_correct:
                    by_source[result.source]['correct'] += 1
        
        source_accuracy = {}
        for source, stats in by_source.items():
            source_accuracy[source] = {
                'total': stats['total'],
                'correct': stats['correct'],
                'accuracy': (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
            }
        
        # 메서드별 통계
        by_method = {}
        for result in self.results:
            method = result.method or 'unknown'
            if method not in by_method:
                by_method[method] = {'total': 0, 'correct': 0}
            by_method[method]['total'] += 1
            if result.is_correct:
                by_method[method]['correct'] += 1
        
        method_accuracy = {}
        for method, stats in by_method.items():
            method_accuracy[method] = {
                'total': stats['total'],
                'correct': stats['correct'],
                'accuracy': (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
            }
        
        # 에러 통계
        errors = [r for r in self.results if r.error]
        error_count = len(errors)
        
        return {
            'total': total,
            'correct': correct,
            'incorrect': total - correct,
            'accuracy': accuracy,
            'avg_solve_time': avg_time,
            'total_evaluation_time': total_time,
            'error_count': error_count,
            'error_rate': (error_count / total * 100) if total > 0 else 0.0,
            'by_difficulty': difficulty_accuracy,
            'by_source': source_accuracy,
            'by_method': method_accuracy
        }
    
    def save_results(self, output_dir: str = "results", 
                     filename: Optional[str] = None) -> str:
        """결과를 JSON 파일로 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.dataset_name}_results_{timestamp}.json"
        
        output_path = os.path.join(output_dir, filename)
        
        metrics = self.calculate_metrics()
        try:
            from .run_helpers import get_run_revision
            run_revision = get_run_revision()
        except Exception:
            run_revision = {}
        output_data = {
            'dataset': self.dataset_name,
            'timestamp': datetime.now().isoformat(),
            'run_revision': run_revision,
            'summary': metrics,
            'results': [r.to_dict() for r in self.results]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def print_summary(self):
        """요약 정보 출력"""
        metrics = self.calculate_metrics()
        
        print(f"\n{'='*70}")
        print(f"{self.dataset_name} 평가 결과")
        print(f"{'='*70}")
        print(f"총 문제 수: {metrics['total']}")
        print(f"정답: {metrics['correct']}")
        print(f"오답: {metrics['incorrect']}")
        print(f"정확도: {metrics['accuracy']:.2f}%")
        print(f"평균 해결 시간: {metrics['avg_solve_time']:.2f}초")
        print(f"총 평가 시간: {metrics['total_evaluation_time']:.2f}초")
        
        if metrics['error_count'] > 0:
            print(f"에러 발생: {metrics['error_count']}개 ({metrics['error_rate']:.2f}%)")
        
        if metrics['by_difficulty']:
            print(f"\n난이도별 정확도:")
            for diff, stats in sorted(metrics['by_difficulty'].items()):
                print(f"  {diff:12s}: {stats['correct']:3d}/{stats['total']:3d} ({stats['accuracy']:5.1f}%)")
        
        if metrics['by_source']:
            print(f"\n소스별 정확도:")
            for source, stats in sorted(metrics['by_source'].items()):
                print(f"  {source:15s}: {stats['correct']:3d}/{stats['total']:3d} ({stats['accuracy']:5.1f}%)")
        
        if metrics['by_method']:
            print(f"\n메서드별 정확도:")
            for method, stats in sorted(metrics['by_method'].items()):
                print(f"  {method:15s}: {stats['correct']:3d}/{stats['total']:3d} ({stats['accuracy']:5.1f}%)")
        
        print(f"{'='*70}\n")


def check_answer_correctness(reference: Optional[str], 
                            predicted: Optional[str],
                            use_sympy: bool = True) -> bool:
    """
    답변 정확도 검사
    
    Args:
        reference: 참조 답변
        predicted: 예측 답변
        use_sympy: SymPy를 사용한 등가성 검사 사용 여부
    
    Returns:
        정답 여부
    """
    if not reference or not predicted:
        return False
    
    if predicted == 'N/A' or predicted is None:
        return False
    
    # 정규화
    ref_norm = normalize_answer(str(reference))
    pred_norm = normalize_answer(str(predicted))
    
    # 직접 비교
    if ref_norm == pred_norm:
        return True
    
    # SymPy 등가성 검사 (옵션)
    if use_sympy:
        try:
            return sympy_equivalent(ref_norm, pred_norm)
        except Exception:
            pass
    
    return False


def extract_aime_answer(solution_text: str) -> Optional[str]:
    """
    AIME 솔루션 텍스트에서 boxed 답변 추출
    
    Args:
        solution_text: AIME 솔루션 텍스트
    
    Returns:
        추출된 답변 또는 None
    """
    import re
    boxed_match = re.search(r'\\boxed\{([^}]+)\}', solution_text)
    return boxed_match.group(1) if boxed_match else None


def determine_difficulty_from_source(source: str) -> str:
    """
    소스로부터 난이도 결정
    
    Args:
        source: 문제 소스
    
    Returns:
        난이도 ('easy', 'medium', 'hard')
    """
    easy_sources = ['orca_math', 'gsm8k']
    hard_sources = ['olympiads', 'amc_aime', 'aops_forum', 'math', 'cn_contest', 'olympiads_ref']
    
    if source in easy_sources:
        return 'easy'
    elif source in hard_sources:
        return 'hard'
    else:
        return 'medium'

