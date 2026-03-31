"""executor_wall_seconds_from_env: defaults and env precedence."""
import math
import os

import pytest

from src.pipeline.executor_env import executor_wall_seconds_from_env


@pytest.fixture(autouse=True)
def clear_executor_env(monkeypatch):
    for key in (
        "AIMO_EXECUTOR_WALL_TIME_SEC",
        "AIMO_EXECUTOR_TIMEOUT_SEC",
        "OMI_EXECUTOR_TIMEOUT",
    ):
        monkeypatch.delenv(key, raising=False)


def test_default_is_unlimited():
    assert math.isinf(executor_wall_seconds_from_env())


def test_zero_means_unlimited(monkeypatch):
    monkeypatch.setenv("OMI_EXECUTOR_TIMEOUT", "0")
    assert math.isinf(executor_wall_seconds_from_env())


def test_positive_cap(monkeypatch):
    monkeypatch.setenv("AIMO_EXECUTOR_WALL_TIME_SEC", "42")
    assert executor_wall_seconds_from_env() == 42.0


def test_precedence_first_key_wins(monkeypatch):
    monkeypatch.setenv("AIMO_EXECUTOR_WALL_TIME_SEC", "10")
    monkeypatch.setenv("AIMO_EXECUTOR_TIMEOUT_SEC", "20")
    assert executor_wall_seconds_from_env() == 10.0
