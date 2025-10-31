"""
Ultra-minimal test file that won't consume memory.
This file contains simple tests that require no complex mocking or resource usage.
"""

import pytest


@pytest.mark.timeout(10)
def test_basic_addition():
    """Test basic addition."""
    assert 1 + 1 == 2


@pytest.mark.timeout(10)
def test_basic_string():
    """Test basic string operations."""
    assert "hello" + " " + "world" == "hello world"


@pytest.mark.timeout(10)
def test_basic_boolean():
    """Test basic boolean operations."""
    assert True is not False
    assert bool(1) is True
    assert bool(0) is False


@pytest.mark.timeout(10)
def test_basic_list():
    """Test basic list operations."""
    my_list = [1, 2, 3]
    assert len(my_list) == 3
    assert sum(my_list) == 6


class TestBasicClass:
    """Group basic tests in a class."""

    @pytest.mark.timeout(10)
    def test_class_method(self):
        """Test a simple method in a class."""
        assert "test".upper() == "TEST"

    @pytest.mark.timeout(10)
    def test_numeric_comparison(self):
        """Test basic numeric comparisons."""
        assert 5 > 3
        assert 10 >= 10
        assert -1 < 0
