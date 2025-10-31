"""Ultra-simplified test to verify basic functionality."""

import pytest


class TestBasicPytest:
    """Basic pytest functionality test."""

    @pytest.mark.timeout(10)
    def test_basic_assertion(self):
        """Test that basic assertions work."""
        assert 1 == 1
        assert "hello" == "hello"

    @pytest.mark.timeout(10)
    def test_basic_math(self):
        """Test basic math operations."""
        result = 2 + 2
        assert result == 4

    @pytest.mark.timeout(10)
    def test_string_operations(self):
        """Test string operations."""
        text = "hello world"
        assert len(text) == 11
        assert "world" in text


if __name__ == "__main__":
    pytest.main([__file__])
