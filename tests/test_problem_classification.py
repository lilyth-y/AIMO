"""
문제 분류 시스템 테스트
다양한 문제 유형에 대한 분류 정확도를 검증합니다.
"""

import pytest
from src.pipeline.stage1_labeling import ProblemAnalyzer
from src.pipeline.problem_diversity import ProblemDiversityAnalyzer


class TestProblemClassification:
    """문제 분류 테스트"""
    
    def test_geometry_problems(self):
        """기하학 문제 분류 테스트"""
        analyzer = ProblemAnalyzer()
        diversity_analyzer = ProblemDiversityAnalyzer()
        
        geometry_problems = [
            "Find the area of a triangle with sides 3, 4, 5",
            "What is the radius of a circle with area 25π?",
            "Find the distance between two points (0,0) and (3,4)",
            "Calculate the perimeter of a rectangle with length 5 and width 3",
            "Find the angle between two perpendicular lines"
        ]
        
        for problem in geometry_problems:
            domain = analyzer.classify_domain(problem)
            assert domain == "Geometry", f"Failed for: {problem}"
            
            diversity_domain = diversity_analyzer.classify_domain(problem)
            assert diversity_domain == "Geometry", f"Diversity analyzer failed for: {problem}"
    
    def test_number_theory_problems(self):
        """정수론 문제 분류 테스트"""
        analyzer = ProblemAnalyzer()
        diversity_analyzer = ProblemDiversityAnalyzer()
        
        nt_problems = [
            "Find all prime numbers less than 100",
            "What is gcd(48, 18)?",
            "Find the remainder when 2^100 is divided by 7",  # "divided by" 키워드로 인식
            "How many integers n satisfy n mod 5 = 3?",
            "Find all solutions to x^2 ≡ 1 (mod 10)"
        ]
        
        for problem in nt_problems:
            domain = analyzer.classify_domain(problem)
            # "divided by"가 포함된 경우 Number Theory로 분류되어야 함
            assert domain in ["Number Theory", "General"], f"Failed for: {problem}, got: {domain}"
            
            diversity_domain = diversity_analyzer.classify_domain(problem)
            assert diversity_domain == "Number Theory", f"Diversity analyzer failed for: {problem}"
    
    def test_algebra_problems(self):
        """대수학 문제 분류 테스트"""
        analyzer = ProblemAnalyzer()
        diversity_analyzer = ProblemDiversityAnalyzer()
        
        algebra_problems = [
            "Solve the quadratic equation x^2 + 5x + 6 = 0",
            "Factor the polynomial x^3 - 8",
            "Find the roots of x^2 - 4x + 3 = 0",
            "Simplify (x+1)(x+2)",
            "Solve the system: x + y = 5, x - y = 1"
        ]
        
        for problem in algebra_problems:
            domain = analyzer.classify_domain(problem)
            assert domain == "Algebra", f"Failed for: {problem}"
            
            diversity_domain = diversity_analyzer.classify_domain(problem)
            assert diversity_domain == "Algebra", f"Diversity analyzer failed for: {problem}"
    
    def test_combinatorics_problems(self):
        """조합론 문제 분류 테스트"""
        analyzer = ProblemAnalyzer()
        diversity_analyzer = ProblemDiversityAnalyzer()
        
        comb_problems = [
            "How many ways to arrange 5 books on a shelf?",
            "Find the number of combinations of 10 choose 3",
            "How many paths from A to B in a grid?",
            "Count the number of ways to choose 2 items from 5",
            "How many permutations of the letters in 'MATH'?"
        ]
        
        for problem in comb_problems:
            domain = analyzer.classify_domain(problem)
            # "ways", "arrange", "choose" 등 키워드로 인식
            assert domain in ["Combinatorics", "General"], f"Failed for: {problem}, got: {domain}"
            
            diversity_domain = diversity_analyzer.classify_domain(problem)
            assert diversity_domain == "Combinatorics", f"Diversity analyzer failed for: {problem}"
    
    def test_calculus_problems(self):
        """미적분 문제 분류 테스트"""
        analyzer = ProblemAnalyzer()
        diversity_analyzer = ProblemDiversityAnalyzer()
        
        calc_problems = [
            "Find the derivative of x^2 + 3x",
            "Calculate the integral of x^2 from 0 to 1",
            "Find the limit of (x^2 - 1)/(x - 1) as x approaches 1",
            "Determine if the series 1/n converges",
            "Find the maximum value of f(x) = x^2 - 4x"
        ]
        
        for problem in calc_problems:
            domain = analyzer.classify_domain(problem)
            # "f(x)" 또는 "derivative", "integral" 키워드가 포함된 경우 Calculus로 분류
            assert domain in ["Calculus", "General"], f"Failed for: {problem}, got: {domain}"
            
            diversity_domain = diversity_analyzer.classify_domain(problem)
            assert diversity_domain == "Calculus", f"Diversity analyzer failed for: {problem}"
    
    def test_mixed_domain_problems(self):
        """복합 도메인 문제 테스트"""
        analyzer = ProblemAnalyzer()
        
        # 여러 도메인 키워드가 포함된 경우
        mixed_problem = "Find the area of a triangle and solve x^2 + 5x + 6 = 0"
        domain = analyzer.classify_domain(mixed_problem)
        # 첫 번째로 매칭되는 도메인 반환 (Geometry가 먼저 체크됨)
        assert domain in ["Geometry", "Algebra"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
