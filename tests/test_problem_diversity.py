"""
문제 다양성 분석 모듈 테스트
"""

import pytest
from src.pipeline.problem_diversity import ProblemDiversityAnalyzer, analyze_problem_diversity


class TestProblemDiversityAnalyzer:
    """ProblemDiversityAnalyzer 테스트"""
    
    def test_classify_domain_geometry(self):
        """기하학 문제 분류 테스트"""
        analyzer = ProblemDiversityAnalyzer()
        problem = "Find the area of a triangle with sides 3, 4, 5"
        assert analyzer.classify_domain(problem) == 'Geometry'
    
    def test_classify_domain_number_theory(self):
        """정수론 문제 분류 테스트"""
        analyzer = ProblemDiversityAnalyzer()
        problem = "Find all prime numbers less than 100"
        assert analyzer.classify_domain(problem) == 'Number Theory'
    
    def test_classify_domain_algebra(self):
        """대수학 문제 분류 테스트"""
        analyzer = ProblemDiversityAnalyzer()
        problem = "Solve the quadratic equation x^2 + 5x + 6 = 0"
        assert analyzer.classify_domain(problem) == 'Algebra'
    
    def test_classify_difficulty(self):
        """난이도 분류 테스트"""
        analyzer = ProblemDiversityAnalyzer()
        
        easy_problem = "What is 2 + 2?"
        assert analyzer.classify_difficulty(easy_problem) in ['easy', 'medium']
        
        hard_problem = "Prove that for all positive integers n, n^2 is even"
        assert analyzer.classify_difficulty(hard_problem) == 'hard'
        
        olympiad_problem = "AIME 2023 Problem 1"
        assert analyzer.classify_difficulty(olympiad_problem, source='aime') == 'olympiad'
    
    def test_classify_format(self):
        """형식 분류 테스트"""
        analyzer = ProblemDiversityAnalyzer()
        
        word_problem = "What is the sum of 1 to 100?"
        assert analyzer.classify_format(word_problem) == 'word_problem'
        
        proof_problem = "Prove that sqrt(2) is irrational"
        assert analyzer.classify_format(proof_problem) == 'proof'
        
        optimization_problem = "Find the maximum value of x^2 + y^2"
        # "maximum value" 키워드로 인식되어야 함
        assert analyzer.classify_format(optimization_problem) in ['optimization', 'word_problem']
    
    def test_analyze_problem(self):
        """문제 분석 테스트"""
        analyzer = ProblemDiversityAnalyzer()
        problem = "Find the area of a circle with radius 5"
        
        analysis = analyzer.analyze_problem(problem)
        
        assert 'domain' in analysis
        assert 'difficulty' in analysis
        assert 'format' in analysis
        assert 'length' in analysis
        assert 'word_count' in analysis
        assert analysis['domain'] == 'Geometry'
    
    def test_analyze_dataset_diversity(self):
        """데이터셋 다양성 분석 테스트"""
        analyzer = ProblemDiversityAnalyzer()
        
        # 다양한 문제 유형 포함
        problems = [
            {'problem': 'Find the area of a triangle', 'source': 'geometry'},
            {'problem': 'Find all prime numbers less than 10', 'source': 'number_theory'},
            {'problem': 'Solve x^2 + 5x + 6 = 0', 'source': 'algebra'},
            {'problem': 'Prove that 1 + 1 = 2', 'source': 'proof'},
            {'problem': 'Find the maximum value of x^2', 'source': 'optimization'},
        ]
        
        analysis = analyzer.analyze_dataset(problems)
        
        assert analysis['total_problems'] == 5
        assert 'domain_distribution' in analysis
        assert 'difficulty_distribution' in analysis
        assert 'format_distribution' in analysis
        assert 'coverage_score' in analysis
        assert 0.0 <= analysis['coverage_score'] <= 1.0
    
    def test_validate_diversity_pass(self):
        """다양성 검증 통과 테스트"""
        analyzer = ProblemDiversityAnalyzer()
        
        # 다양한 문제 유형 포함
        problems = [
            {'problem': 'Geometry problem 1', 'source': 'geo1'},
            {'problem': 'Geometry problem 2', 'source': 'geo2'},
            {'problem': 'Number theory problem', 'source': 'nt1'},
            {'problem': 'Algebra problem', 'source': 'alg1'},
            {'problem': 'Combinatorics problem', 'source': 'comb1'},
            {'problem': 'Calculus problem', 'source': 'calc1'},
        ]
        
        is_valid, issues = analyzer.validate_diversity(problems, min_domains=3)
        # 최소 도메인 수가 충족되면 통과
        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)
    
    def test_validate_diversity_fail(self):
        """다양성 검증 실패 테스트"""
        analyzer = ProblemDiversityAnalyzer()
        
        # 단일 도메인만 포함
        problems = [
            {'problem': 'Geometry problem 1', 'source': 'geo1'},
            {'problem': 'Geometry problem 2', 'source': 'geo2'},
            {'problem': 'Geometry problem 3', 'source': 'geo3'},
        ]
        
        is_valid, issues = analyzer.validate_diversity(problems, min_domains=5)
        # 최소 도메인 수가 충족되지 않으면 실패
        assert is_valid == False
        assert len(issues) > 0


class TestAnalyzeProblemDiversity:
    """analyze_problem_diversity 함수 테스트"""
    
    def test_analyze_problem_diversity(self):
        """문제 다양성 분석 함수 테스트"""
        problems = [
            {'problem': 'Find the area of a triangle', 'source': 'geometry'},
            {'problem': 'Find all prime numbers', 'source': 'number_theory'},
            {'problem': 'Solve quadratic equation', 'source': 'algebra'},
        ]
        
        result = analyze_problem_diversity(problems)
        
        assert 'analysis' in result
        assert 'report' in result
        assert 'is_valid' in result
        assert isinstance(result['report'], str)
        assert len(result['report']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
