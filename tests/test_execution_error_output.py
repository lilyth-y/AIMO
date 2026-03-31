"""is_execution_error_output: executor strings must not count as verified answers."""
from src.pipeline.orchestrator_helpers import is_execution_error_output


def test_error_colon_lowercase():
    assert is_execution_error_output("Error: list index out of range")


def test_error_colon_upper_e():
    assert is_execution_error_output("ERROR: Timeout")


def test_mixed_case():
    assert is_execution_error_output("error: something")


def test_normal_answer_not_error():
    assert not is_execution_error_output("3")
    assert not is_execution_error_output("\\frac{1}{6}")


def test_substring_error_is_not_prefix():
    """'trial and error' must not be treated as executor failure."""
    assert not is_execution_error_output("trial and error approach")


def test_empty():
    assert not is_execution_error_output("")
    assert not is_execution_error_output("   ")
