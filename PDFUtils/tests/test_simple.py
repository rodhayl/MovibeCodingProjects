"""Simple test to verify pytest is working."""

import pytest


@pytest.mark.timeout(10)
def test_simple():
    """A simple passing test."""
    assert True
