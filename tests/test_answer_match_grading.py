"""classify_answer_match / check_answer_correctness 확장(근사·정규화) 단위 테스트."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from evaluation.evaluation_utils import (
    check_answer_correctness,
    classify_answer_match,
    numeric_equivalent,
)
from pipeline.reasoning_utils import normalize_answer


def test_classify_strict():
    assert classify_answer_match("42", "42") == "strict"
    assert check_answer_correctness("42", "42") is True


def test_classify_numeric_rounding():
    assert classify_answer_match("116.66666666666666", "116.67") == "numeric"
    assert check_answer_correctness("116.66666666666666", "116.67") is True


def test_currency_and_text_stripped():
    assert check_answer_correctness(r"\$63.78", "63.78") is True
    assert classify_answer_match(r"\$63.78", "63.78") in ("strict", "numeric")
    assert check_answer_correctness(r"\text{B}", "B") is True
    assert classify_answer_match(r"\text{B}", "B") == "strict"


def test_normalize_dollar():
    n = normalize_answer(r"\$63.78")
    assert "63.78" in n or n.replace(" ", "") == "63.78"


def test_wrong_stays_false():
    assert check_answer_correctness("1", "2") is False
    assert classify_answer_match("1", "2") == "none"


def test_numeric_equivalent_helper():
    assert numeric_equivalent("116.67", "116.66666666666666") is True
    assert numeric_equivalent("1", "2") is False


def test_ratio_match():
    assert classify_answer_match("2:1", "4/2") == "ratio"
    assert check_answer_correctness("2:1", "4/2") is True


def test_interval_pair_match():
    assert classify_answer_match("(1,2)", "(1.0, 2.0)") == "interval"
    assert check_answer_correctness("(1,2)", "(1.0, 2.0)") is True


def test_latex_frac_matches_decimal():
    # Typical Numina/TeX reference answers
    assert check_answer_correctness(r"\frac{1}{6}", "0.16666666666666666") is True
    assert classify_answer_match(r"\frac{1}{6}", "0.16666666666666666") in ("numeric", "sympy", "strict")


def test_latex_sqrt_expression_matches_numeric():
    # Ensure simple latex sqrt rewrites allow sympy/numeric equivalence
    assert check_answer_correctness(r"\frac{\sqrt{5}}{2}", "1.11803398875") is True
