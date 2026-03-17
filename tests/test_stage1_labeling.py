"""
Stage1 (ProblemAnalyzer) 변수 추출 및 도메인 분류 테스트
Phase 3.1 변수 추출 패턴 확장 검증
"""

import pytest
from src.pipeline.stage1_labeling import ProblemAnalyzer


class TestExtractVariables:
    """extract_variables 패턴 테스트"""

    def test_equals_style_uppercase(self):
        """N = 10 형태"""
        analyzer = ProblemAnalyzer()
        out = analyzer.extract_variables("Given N = 5, find the sum.")
        assert out.get("N") == 5

    def test_equals_style_lowercase_normalized(self):
        """n=10 형태 → 단일 문자는 대문자 N으로 통일"""
        analyzer = ProblemAnalyzer()
        out = analyzer.extract_variables("Let n=10 and k=3.")
        assert out.get("N") == 10
        assert out.get("K") == 3

    def test_let_N_be_style(self):
        """let N be 10 / N be 10 형태"""
        analyzer = ProblemAnalyzer()
        out = analyzer.extract_variables("Let N be 100. Compute something.")
        assert out.get("N") == 100

    def test_multiple_variables(self):
        """여러 변수 혼합"""
        analyzer = ProblemAnalyzer()
        out = analyzer.extract_variables("N = 7, K = 2. Let P be 11.")
        assert out.get("N") == 7
        assert out.get("K") == 2
        assert out.get("P") == 11

    def test_no_variables(self):
        """변수 없으면 빈 dict"""
        analyzer = ProblemAnalyzer()
        out = analyzer.extract_variables("Just some text with no numbers.")
        assert out == {}


class TestClassifyDomain:
    """classify_domain 기본 동작 유지 확인"""

    def test_geometry(self):
        analyzer = ProblemAnalyzer()
        assert analyzer.classify_domain("Find the area of a triangle.") == "Geometry"

    def test_number_theory(self):
        analyzer = ProblemAnalyzer()
        assert analyzer.classify_domain("Find the remainder when 2^10 is divided by 7.") == "Number Theory"
