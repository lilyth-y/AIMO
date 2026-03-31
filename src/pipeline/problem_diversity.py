"""
문제 다양성 분석 및 검증 모듈
문제 유형과 종류의 다양성을 확보하고 검증합니다.
"""

from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import json
from pathlib import Path


class ProblemDiversityAnalyzer:
    """
    문제 다양성 분석기
    
    문제 유형, 난이도, 소스 등의 다양성을 분석하고 검증합니다.
    """
    
    def __init__(self):
        self.domain_keywords = {
            'Geometry': [
                'triangle', 'circle', 'angle', 'perpendicular', 'parallel',
                'tangent', 'area', 'perimeter', 'polygon', 'coordinate',
                'distance', 'midpoint', 'radius', 'diameter', 'chord',
                'rectangle', 'square', 'trapezoid', 'rhombus', 'ellipse',
                'parabola', 'hyperbola', 'conic', 'sphere', 'cylinder'
            ],
            'Number Theory': [
                'prime', 'gcd', 'lcm', 'mod', 'divisible', 'integer',
                'congruence', 'diophantine', 'modular',
                'remainder', 'divided by', 'composite', 'coprime',
                'euclidean', 'fermat', 'wilson'
            ],
            'Algebra': [
                'polynomial', 'factor', 'expand', 'root', 'quadratic',
                'cubic', 'equation', 'system', 'simplify', 'inequality',
                'matrix', 'determinant', 'eigenvalue', 'vector', 'linear'
            ],
            'Combinatorics': [
                'permutation', 'combination', 'arrangement', 'count',
                'choose', 'binomial', 'pigeonhole', 'graph', 'tree',
                'path', 'cycle', 'matching', 'coloring', 'partition',
                'ways to', 'how many ways', 'arrange'
            ],
            'Calculus': [
                'limit', 'derivative', 'integral', 'series', 'converge',
                'diverge', 'taylor', 'fourier', 'optimization', 'critical',
                'inflection', 'asymptote', 'continuity', 'differentiable',
                'f(x)', 'maximum value', 'minimum value', 'local maximum', 'local minimum'
            ],
            'Inequalities': [
                'inequality', 'am-gm', 'cauchy', 'schwarz', 'jensen', 'holder',
                'rearrangement', 'chebyshev', 'muirhead'
            ],
            'Logic': [
                'puzzle', 'constraint', 'logic', 'satisfy', 'condition',
                'if and only if', 'implies', 'contradiction', 'proof',
                'theorem', 'lemma', 'corollary', 'conjecture'
            ],
            'Probability': [
                'probability', 'expectation', 'variance', 'distribution',
                'random', 'event', 'outcome', 'sample', 'space'
            ]
        }
        
        self.difficulty_keywords = {
            'easy': ['simple', 'basic', 'elementary', 'straightforward'],
            'medium': ['find', 'determine', 'calculate', 'compute'],
            'hard': ['prove', 'show that', 'demonstrate', 'establish'],
            'olympiad': ['imo', 'aime', 'usamo', 'olympiad', 'competition']
        }
        
        self.problem_formats = {
            'optimization': ['maximum', 'minimum', 'optimize', 'maximize', 'minimize', 'max value', 'min value'],
            'proof': ['prove', 'show that', 'demonstrate', 'establish'],
            'multiple_choice': ['which of', 'select', 'choose'],
            'construction': ['construct', 'draw', 'build'],
            'word_problem': ['what is', 'how many', 'find the', 'calculate']  # 가장 일반적이므로 마지막에 체크
        }
    
    def classify_domain(self, problem_text: str) -> str:
        """
        문제를 도메인으로 분류합니다.
        
        Args:
            problem_text: 문제 텍스트
        
        Returns:
            도메인 이름 (Geometry, Number Theory, Algebra, 등)
        """
        problem_lower = problem_text.lower()

        # High-precision rules (avoid keyword-score ties)
        if 'polynomial' in problem_lower:
            return 'Algebra'
        if 'remainder' in problem_lower or 'divided by' in problem_lower:
            return 'Number Theory'
        if 'how many ways' in problem_lower or 'ways to arrange' in problem_lower:
            return 'Combinatorics'
        if 'f(x)' in problem_lower and ('maximum' in problem_lower or 'minimum' in problem_lower):
            return 'Calculus'

        domain_scores = {}
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for kw in keywords if kw in problem_lower)
            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            best_score = max(domain_scores.values())
            candidates = [d for d, s in domain_scores.items() if s == best_score]
            if len(candidates) > 1:
                priority = [
                    'Calculus', 'Number Theory', 'Algebra', 'Combinatorics',
                    'Inequalities', 'Geometry', 'Probability', 'Logic',
                ]
                for dom in priority:
                    if dom in candidates:
                        return dom
            return max(domain_scores.items(), key=lambda x: x[1])[0]

        return 'General'
    
    def classify_difficulty(self, problem_text: str, source: Optional[str] = None) -> str:
        """
        문제의 난이도를 분류합니다.
        
        Args:
            problem_text: 문제 텍스트
            source: 문제 출처 (선택적)
        
        Returns:
            난이도 (easy, medium, hard, olympiad)
        """
        problem_lower = problem_text.lower()
        
        # 소스 기반 분류
        if source:
            source_lower = source.lower()
            if any(kw in source_lower for kw in self.difficulty_keywords['olympiad']):
                return 'olympiad'
        
        # 키워드 기반 분류
        for difficulty, keywords in self.difficulty_keywords.items():
            if difficulty == 'olympiad':
                continue
            if any(kw in problem_lower for kw in keywords):
                if difficulty == 'hard':
                    return 'hard'
                elif difficulty == 'medium':
                    return 'medium'
        
        return 'medium'  # 기본값
    
    def classify_format(self, problem_text: str) -> str:
        """
        문제 형식을 분류합니다.
        
        Args:
            problem_text: 문제 텍스트
        
        Returns:
            형식 (word_problem, proof, multiple_choice, construction, optimization)
        """
        problem_lower = problem_text.lower()
        
        for format_type, keywords in self.problem_formats.items():
            if any(kw in problem_lower for kw in keywords):
                return format_type
        
        return 'word_problem'  # 기본값
    
    def analyze_problem(self, problem_text: str, source: Optional[str] = None) -> Dict[str, Any]:
        """
        문제를 종합적으로 분석합니다.
        
        Args:
            problem_text: 문제 텍스트
            source: 문제 출처 (선택적)
        
        Returns:
            분석 결과 딕셔너리
        """
        return {
            'domain': self.classify_domain(problem_text),
            'difficulty': self.classify_difficulty(problem_text, source),
            'format': self.classify_format(problem_text),
            'length': len(problem_text),
            'word_count': len(problem_text.split())
        }
    
    def analyze_dataset(self, problems: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        데이터셋의 다양성을 분석합니다.
        
        Args:
            problems: 문제 리스트 (각 문제는 'problem' 키를 가져야 함)
        
        Returns:
            다양성 분석 결과
        """
        domain_counter = Counter()
        difficulty_counter = Counter()
        format_counter = Counter()
        source_counter = Counter()
        
        for problem_data in problems:
            problem_text = problem_data.get('problem', '')
            source = problem_data.get('source', None)
            
            analysis = self.analyze_problem(problem_text, source)
            
            domain_counter[analysis['domain']] += 1
            difficulty_counter[analysis['difficulty']] += 1
            format_counter[analysis['format']] += 1
            
            if source:
                source_counter[source] += 1
        
        total = len(problems)
        
        return {
            'total_problems': total,
            'domain_distribution': dict(domain_counter),
            'domain_diversity': len(domain_counter) / max(len(self.domain_keywords), 1),
            'difficulty_distribution': dict(difficulty_counter),
            'difficulty_diversity': len(difficulty_counter) / 4,  # 4가지 난이도
            'format_distribution': dict(format_counter),
            'format_diversity': len(format_counter) / max(len(self.problem_formats), 1),
            'source_distribution': dict(source_counter),
            'source_diversity': len(source_counter),
            'coverage_score': self._calculate_coverage_score(
                domain_counter, difficulty_counter, format_counter
            )
        }
    
    def _calculate_coverage_score(self, domain_counter: Counter, 
                                  difficulty_counter: Counter,
                                  format_counter: Counter) -> float:
        """
        커버리지 점수를 계산합니다.
        
        Args:
            domain_counter: 도메인 분포
            difficulty_counter: 난이도 분포
            format_counter: 형식 분포
        
        Returns:
            커버리지 점수 (0.0 ~ 1.0)
        """
        # 도메인 커버리지 (최소 5개 도메인 이상)
        domain_coverage = min(len(domain_counter) / 5, 1.0)
        
        # 난이도 커버리지 (모든 난이도 포함)
        difficulty_coverage = min(len(difficulty_counter) / 4, 1.0)
        
        # 형식 커버리지 (최소 3개 형식 이상)
        format_coverage = min(len(format_counter) / 3, 1.0)
        
        # 균형성 (각 카테고리별 최소 문제 수)
        domain_balance = min(min(domain_counter.values()) / 10, 1.0) if domain_counter else 0.0
        difficulty_balance = min(min(difficulty_counter.values()) / 10, 1.0) if difficulty_counter else 0.0
        
        # 가중 평균
        coverage = (
            domain_coverage * 0.4 +
            difficulty_coverage * 0.3 +
            format_coverage * 0.2 +
            (domain_balance + difficulty_balance) / 2 * 0.1
        )
        
        return coverage
    
    def validate_diversity(self, problems: List[Dict[str, Any]], 
                          min_domains: int = 5,
                          min_difficulties: int = 3,
                          min_formats: int = 2) -> Tuple[bool, List[str]]:
        """
        데이터셋의 다양성을 검증합니다.
        
        Args:
            problems: 문제 리스트
            min_domains: 최소 도메인 수
            min_difficulties: 최소 난이도 수
            min_formats: 최소 형식 수
        
        Returns:
            (검증 통과 여부, 문제점 리스트)
        """
        analysis = self.analyze_dataset(problems)
        issues = []
        
        if len(analysis['domain_distribution']) < min_domains:
            issues.append(f"도메인 다양성 부족: {len(analysis['domain_distribution'])}개 도메인 (최소 {min_domains}개 필요)")
        
        if len(analysis['difficulty_distribution']) < min_difficulties:
            issues.append(f"난이도 다양성 부족: {len(analysis['difficulty_distribution'])}개 난이도 (최소 {min_difficulties}개 필요)")
        
        if len(analysis['format_distribution']) < min_formats:
            issues.append(f"형식 다양성 부족: {len(analysis['format_distribution'])}개 형식 (최소 {min_formats}개 필요)")
        
        if analysis['coverage_score'] < 0.6:
            issues.append(f"전체 커버리지 점수 낮음: {analysis['coverage_score']:.2f} (권장: 0.6 이상)")
        
        return len(issues) == 0, issues
    
    def generate_diversity_report(self, problems: List[Dict[str, Any]], 
                                  output_file: Optional[Path] = None) -> str:
        """
        다양성 분석 보고서를 생성합니다.
        
        Args:
            problems: 문제 리스트
            output_file: 출력 파일 경로 (선택적)
        
        Returns:
            보고서 텍스트
        """
        analysis = self.analyze_dataset(problems)
        is_valid, issues = self.validate_diversity(problems)
        
        report = []
        report.append("=" * 70)
        report.append("문제 다양성 분석 보고서")
        report.append("=" * 70)
        report.append("")
        
        report.append(f"총 문제 수: {analysis['total_problems']}")
        report.append("")
        
        report.append("도메인 분포:")
        for domain, count in sorted(analysis['domain_distribution'].items(), 
                                   key=lambda x: x[1], reverse=True):
            percentage = (count / analysis['total_problems']) * 100
            report.append(f"  {domain}: {count}개 ({percentage:.1f}%)")
        report.append(f"도메인 다양성: {analysis['domain_diversity']:.2f}")
        report.append("")
        
        report.append("난이도 분포:")
        for difficulty, count in sorted(analysis['difficulty_distribution'].items(),
                                       key=lambda x: x[1], reverse=True):
            percentage = (count / analysis['total_problems']) * 100
            report.append(f"  {difficulty}: {count}개 ({percentage:.1f}%)")
        report.append(f"난이도 다양성: {analysis['difficulty_diversity']:.2f}")
        report.append("")
        
        report.append("형식 분포:")
        for format_type, count in sorted(analysis['format_distribution'].items(),
                                        key=lambda x: x[1], reverse=True):
            percentage = (count / analysis['total_problems']) * 100
            report.append(f"  {format_type}: {count}개 ({percentage:.1f}%)")
        report.append(f"형식 다양성: {analysis['format_diversity']:.2f}")
        report.append("")
        
        if analysis['source_distribution']:
            report.append("출처 분포:")
            for source, count in sorted(analysis['source_distribution'].items(),
                                       key=lambda x: x[1], reverse=True)[:10]:
                percentage = (count / analysis['total_problems']) * 100
                report.append(f"  {source}: {count}개 ({percentage:.1f}%)")
            report.append("")
        
        report.append(f"전체 커버리지 점수: {analysis['coverage_score']:.2f}")
        report.append("")
        
        report.append("검증 결과:")
        if is_valid:
            report.append("  ✅ 다양성 검증 통과")
        else:
            report.append("  ❌ 다양성 검증 실패")
            for issue in issues:
                report.append(f"    - {issue}")
        report.append("")
        
        report.append("=" * 70)
        
        report_text = "\n".join(report)
        
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text


def analyze_problem_diversity(problems: List[Dict[str, Any]], 
                             output_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    문제 다양성을 분석하는 편의 함수입니다.
    
    Args:
        problems: 문제 리스트
        output_file: 출력 파일 경로 (선택적)
    
    Returns:
        분석 결과 딕셔너리
    """
    analyzer = ProblemDiversityAnalyzer()
    analysis = analyzer.analyze_dataset(problems)
    report = analyzer.generate_diversity_report(problems, output_file)
    
    return {
        'analysis': analysis,
        'report': report,
        'is_valid': analyzer.validate_diversity(problems)[0]
    }
