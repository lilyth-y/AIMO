"""
통합 평가 유틸리티
- 표준화된 평가 메트릭 계산
- 일관된 결과 저장 형식
- 개선된 에러 처리 및 로깅
"""

import json
import math
import os
import re
import time
from typing import Dict, List, Any, Literal, Optional, Tuple
from fractions import Fraction
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
            s = str(ans).strip()
            for _ in range(5):
                n = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
                if n == s:
                    break
                s = n
            s = s.replace("\\$", "").replace("$", "")
            return re.sub(r"\s+", " ", s).replace(" ", "")

        def sympy_equivalent(a: str, b: str) -> bool:
            return normalize_answer(a) == normalize_answer(b)


MatchKind = Literal["strict", "sympy", "numeric", "ratio", "interval", "none"]


def _parse_scalar_float(s: str) -> Optional[float]:
    t = (s or "").strip()
    if not t:
        return None
    # Support exact rationals like "1/6" for numeric_equivalent fallback.
    m = re.match(r"^([-+]?\d+)\s*/\s*(\d+)$", t)
    if m:
        try:
            return float(Fraction(int(m.group(1)), int(m.group(2))))
        except Exception:
            return None
    try:
        x = float(t)
    except ValueError:
        # Try sympy numeric evaluation for simple expressions like "sqrt(5)/2".
        try:
            import sympy as sp  # type: ignore

            expr = sp.sympify(t)
            if getattr(expr, "free_symbols", None) and len(expr.free_symbols) > 0:
                return None
            x = float(sp.N(expr))
        except Exception:
            return None
    if not math.isfinite(x):
        return None
    return x


def ratio_equivalent(ref_norm: str, pred_norm: str) -> bool:
    """정답이 'a:b' 형태일 때만 'c/d', 'c:d' 또는 스칼라(정규화로 4/2→2)와 동치 비교."""
    m1 = re.match(r"^(\d+):(\d+)$", ref_norm)
    if not m1:
        return False
    r = Fraction(int(m1.group(1)), int(m1.group(2)))
    m2 = re.match(r"^(\d+)/(\d+)$", pred_norm)
    if m2:
        return r == Fraction(int(m2.group(1)), int(m2.group(2)))
    m3 = re.match(r"^(\d+):(\d+)$", pred_norm)
    if m3:
        return r == Fraction(int(m3.group(1)), int(m3.group(2)))
    px = _parse_scalar_float(pred_norm)
    if px is not None:
        try:
            return abs(float(r) - px) < 1e-9
        except Exception:
            return False
    return False


def interval_pair_equivalent(ref_norm: str, pred_norm: str) -> bool:
    """쉼표로 구분된 두 실수 쌍 (구간/순서쌍) 근사 비교. 둘 다 쌍 형태일 때만."""
    def _pair(s: str) -> Optional[Tuple[float, float]]:
        t = re.sub(r"\s+", "", str(s))
        t = re.sub(r"[\(\)\[\]]", "", t)
        t = re.sub(r"x\\in|\\in", "", t, flags=re.IGNORECASE)
        m = re.match(
            r"^([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?),([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)$",
            t,
        )
        if not m:
            return None
        a = _parse_scalar_float(m.group(1))
        b = _parse_scalar_float(m.group(2))
        if a is None or b is None:
            return None
        return (a, b)

    p1 = _pair(ref_norm)
    p2 = _pair(pred_norm)
    if p1 is None or p2 is None:
        return False
    return numeric_equivalent(str(p1[0]), str(p2[0])) and numeric_equivalent(str(p1[1]), str(p2[1]))


def numeric_equivalent(
    ref_norm: str,
    pred_norm: str,
    *,
    rtol: float = 1e-4,
    atol: float = 1e-8,
) -> bool:
    """정규화된 두 문자열이 둘 다 유한 실수로 읽힐 때만 근사 비교.

    rtol 기본 1e-4: 소수 둘째 자리 반올림(116.67 vs 116.666…) 등 표시 차이를 허용.
    """
    a = _parse_scalar_float(ref_norm)
    b = _parse_scalar_float(pred_norm)
    if a is None or b is None:
        return False
    return math.isclose(a, b, rel_tol=rtol, abs_tol=atol)


def classify_answer_match(
    reference: Optional[str],
    predicted: Optional[str],
    *,
    use_sympy: bool = True,
) -> MatchKind:
    """
    채점 일치 방식: strict → ratio(정답 a:b) → interval(두 실수 쌍) → sympy → numeric.
    """
    if not reference or not predicted:
        return "none"
    if predicted == "N/A" or predicted is None:
        return "none"
    ref_norm = normalize_answer(str(reference))
    pred_norm = normalize_answer(str(predicted))
    if not ref_norm or not pred_norm:
        return "none"
    if ref_norm == pred_norm:
        return "strict"
    if ratio_equivalent(ref_norm, pred_norm):
        return "ratio"
    if interval_pair_equivalent(ref_norm, pred_norm):
        return "interval"
    if use_sympy:
        try:
            if sympy_equivalent(ref_norm, pred_norm):
                return "sympy"
        except Exception:
            pass
    if numeric_equivalent(ref_norm, pred_norm):
        return "numeric"
    return "none"


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


def _accuracy_by_metadata_label(
    results: List["EvaluationResult"], metadata_key: str
) -> Dict[str, Dict[str, Any]]:
    """metadata[metadata_key] 값별로 total/correct/accuracy 집계. 없으면 'unknown'."""
    buckets: Dict[str, Dict[str, int]] = {}
    for result in results:
        raw = (result.metadata or {}).get(metadata_key)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            label = "unknown"
        else:
            label = str(raw).strip()
        if label not in buckets:
            buckets[label] = {"total": 0, "correct": 0}
        buckets[label]["total"] += 1
        if result.is_correct:
            buckets[label]["correct"] += 1
    out: Dict[str, Dict[str, Any]] = {}
    for lab, stats in buckets.items():
        out[lab] = {
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0.0,
        }
    return out


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
                'avg_time': 0.0,
                'by_problem_type': {},
                'by_question_type': {},
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

        by_problem_type = _accuracy_by_metadata_label(self.results, "problem_type")
        by_question_type = _accuracy_by_metadata_label(self.results, "question_type")
        
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
            'by_method': method_accuracy,
            'by_problem_type': by_problem_type,
            'by_question_type': by_question_type,
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

        if metrics.get('by_problem_type'):
            print(f"\n문제 유형별 정확도 (problem_type):")
            for pt, stats in sorted(metrics['by_problem_type'].items()):
                print(f"  {pt:20s}: {stats['correct']:3d}/{stats['total']:3d} ({stats['accuracy']:5.1f}%)")

        if metrics.get('by_question_type'):
            print(f"\n질문 유형별 정확도 (question_type):")
            for qt, stats in sorted(metrics['by_question_type'].items()):
                print(f"  {qt:20s}: {stats['correct']:3d}/{stats['total']:3d} ({stats['accuracy']:5.1f}%)")
        
        print(f"{'='*70}\n")


def check_answer_correctness(reference: Optional[str], 
                            predicted: Optional[str],
                            use_sympy: bool = True) -> bool:
    """
    답변 정확도 검사.

    정규화 후 문자열 일치 → SymPy 등가 → 스칼라 실수 근사(math.isclose).
    자세한 분류는 classify_answer_match 참고.
    """
    return classify_answer_match(reference, predicted, use_sympy=use_sympy) != "none"


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


def mcnemar_exact_two_sided_p_value(b_only: int, t_only: int) -> float:
    """
    페어 A/B 정오표에서 McNemar exact two-sided p-value.

    - b_only: baseline만 맞음 (baseline correct, treatment wrong)
    - t_only: treatment만 맞음 (baseline wrong, treatment correct)

    불일치 쌍 b_only+t_only 를 이항(n, 0.5)으로 두측 검정.
    """
    n = b_only + t_only
    if n == 0:
        return 1.0
    k = min(b_only, t_only)
    p_cdf = 0.0
    for x in range(0, k + 1):
        p_cdf += math.comb(n, x) * (0.5**n)
    return min(1.0, 2.0 * p_cdf)


def stratified_mcnemar_paired_ab(
    paired_results: List[Dict[str, Any]],
    stratum_key: str,
) -> Dict[str, Any]:
    """
    유형(또는 임의의 층화 키)별로 동일한 McNemar를 독립 적용.

    각 원소 형식 (``examples/ab_eval_1000.py`` 산출 ``paired_results`` 와 동일):

    - ``stratum_key`` 에 해당하는 라벨 (없으면 ``"unknown"``)
    - ``baseline`` / ``treatment`` 각각 ``is_correct``: bool

    주의: 층마다 p-value를 따로 보므로 **다중비교 보정 없음**;
    ``discordant_n`` 이 작으면 검정력이 매우 낮다.
    """
    from collections import defaultdict

    cells: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {
            "both_correct": 0,
            "both_wrong": 0,
            "baseline_only_correct": 0,
            "treatment_only_correct": 0,
        }
    )
    for row in paired_results:
        raw = row.get(stratum_key)
        if raw is None or (isinstance(raw, str) and not str(raw).strip()):
            label = "unknown"
        else:
            label = str(raw).strip()
        bc = bool(row["baseline"]["is_correct"])
        tc = bool(row["treatment"]["is_correct"])
        bucket = cells[label]
        if bc and tc:
            bucket["both_correct"] += 1
        elif (not bc) and (not tc):
            bucket["both_wrong"] += 1
        elif bc and (not tc):
            bucket["baseline_only_correct"] += 1
        else:
            bucket["treatment_only_correct"] += 1

    strata_out: Dict[str, Dict[str, Any]] = {}
    for lab in sorted(cells.keys()):
        b = cells[lab]
        bo = b["baseline_only_correct"]
        to = b["treatment_only_correct"]
        d = bo + to
        n_pairs = sum(b[k] for k in b)
        strata_out[lab] = {
            "n_pairs": n_pairs,
            "both_correct": b["both_correct"],
            "both_wrong": b["both_wrong"],
            "baseline_only_correct": bo,
            "treatment_only_correct": to,
            "discordant_n": d,
            "mcnemar_exact_p_value": mcnemar_exact_two_sided_p_value(bo, to),
        }

    return {
        "stratum_key": stratum_key,
        "strata": strata_out,
        "caveat": (
            "Stratified McNemar: no multiplicity adjustment across strata; "
            "interpret cautiously when discordant_n is small."
        ),
    }

