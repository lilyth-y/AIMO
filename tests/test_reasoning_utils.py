"""
reasoning_utils 답 추출 테스트 (extract_final_answer_from_output 등)
"""

import pytest
from src.pipeline.reasoning_utils import extract_final_answer_from_output


class TestExtractFinalAnswerFromOutput:
    """실행 결과에서 최종 답 추출 테스트"""

    def test_sentence_answer_so(self):
        """문장 형태: So the answer is 42."""
        output = "We computed step by step. So the answer is 42."
        assert extract_final_answer_from_output(output) == "42"

    def test_sentence_answer_hence(self):
        """문장 형태: Hence the answer is 1/6."""
        output = "Hence the answer is 1/6."
        assert extract_final_answer_from_output(output) == "1/6"

    def test_labeled_result(self):
        """기존 동작: Result: 1/6"""
        output = "Result: 1/6"
        assert extract_final_answer_from_output(output) == "1/6"

    def test_error_output_unchanged(self):
        """Error로 시작하면 그대로 반환"""
        output = "Error: NameError"
        assert extract_final_answer_from_output(output) == "Error: NameError"

    def test_empty_output_becomes_error(self):
        assert extract_final_answer_from_output("") == "ERROR: EmptyOutput"
        assert extract_final_answer_from_output("   \n\n") == "ERROR: EmptyOutput"

    def test_multiline_prefers_last_numeric_token(self):
        output = "Part (I): c = (3.0, 6.0)\nPart (II): cos(theta) = 0.16666666666666666\n"
        assert extract_final_answer_from_output(output) == "0.16666666666666666"

    def test_multiline_prefers_last_latex_fraction(self):
        output = "Intermediate: 0.3\nFinal: \\\\frac{1}{6}\n"
        assert extract_final_answer_from_output(output) == r"\frac{1}{6}"
