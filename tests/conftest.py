import pytest


@pytest.fixture(scope="session")
def problems():
    """
    Shared fixture for `tests/test_real_imo_puzzle.py`.
    Loads a small set of representative problems from the configured dataset.
    """
    from tests.test_real_imo_puzzle import find_test_problems

    return find_test_problems()

