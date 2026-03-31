"""Tests for pipeline.ans_format_guard."""

import os
import sys

import pytest

project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from pipeline.ans_format_guard import (
    build_format_repair_prompt,
    build_prompt_strict_first,
    build_verification_agent_prompt,
    validate_ans_strict,
)


def test_validate_ok_single_block():
    v = validate_ans_strict("  \n<ANS>42</ANS>  ")
    assert v.ok
    assert v.inner_content == "42"
    assert v.reason is None


def test_validate_ok_case_insensitive_tags():
    v = validate_ans_strict("<ans>1/2</ans>")
    assert v.ok
    assert v.inner_content == "1/2"


def test_validate_empty_inner():
    v = validate_ans_strict("<ANS>  </ANS>")
    assert not v.ok
    assert v.reason == "EMPTY_ANS"


def test_validate_no_tag():
    v = validate_ans_strict("just text")
    assert not v.ok
    assert v.reason == "NO_ANS_TAG"


def test_validate_multiple_blocks():
    v = validate_ans_strict("<ANS>1</ANS> and <ANS>2</ANS>")
    assert not v.ok
    assert v.reason == "MULTIPLE_ANS_BLOCKS"


def test_build_prompts_contain_problem():
    p = "Compute $1+1$."
    assert p in build_prompt_strict_first(p)
    assert p in build_format_repair_prompt(p)


def test_verification_agent_prompt_contains_problem_and_prior():
    p = "Find $2+2$."
    prior = "Here is a long solution...\nThus the answer is 4."
    s = build_verification_agent_prompt(p, prior)
    assert p in s
    assert "Prior model output" in s or "prior" in s.lower()
    assert "verification" in s.lower() or "ANS" in s


def test_validate_empty_completion():
    v = validate_ans_strict("")
    assert not v.ok
    assert v.reason == "EMPTY_COMPLETION"


def test_single_block_only_false_allows_multiple():
    v = validate_ans_strict("<ANS>1</ANS> mid <ANS>2</ANS>", single_block_only=False)
    assert v.ok
    assert v.inner_content == "1"
