"""
Test file for safe mocks implementation.
This file creates and destroys many mock objects to verify memory handling.
"""

import gc
import unittest

import pytest

from tests.safe_mocks import SafeMockStringVar, SafeMockVariable, cleanup_mock_variables


class TestSafeMocks(unittest.TestCase):
    """Test memory usage with safe mocks."""

    @pytest.mark.timeout(10)
    def test_safe_mock_creation(self):
        """Test creating and destroying safe mocks."""
        # Create a large number of safe mocks
        mocks = []
        for i in range(1000):
            mocks.append(SafeMockStringVar())

        # Verify they exist
        self.assertEqual(len(mocks), 1000)

        # Test basic functionality
        mocks[0].set("test")
        self.assertEqual(mocks[0].get(), "test")

        # Use our helper for cleanup
        cleanup_mock_variables(mocks)

        # Force garbage collection
        gc.collect()

        # Success if we get here without crashing
        self.assertTrue(True)

    @pytest.mark.timeout(10)
    def test_safe_variable_mock(self):
        """Test the generic SafeMockVariable."""
        # Create a large number of variable mocks
        mocks = []
        for i in range(1000):
            mock_var = SafeMockVariable()
            mock_var.set(f"value-{i}")
            mocks.append(mock_var)

        # Verify they work
        self.assertEqual(mocks[500].get(), "value-500")

        # Use our helper for cleanup
        cleanup_mock_variables(mocks)

        # Force garbage collection
        gc.collect()

        # Success if we get here without crashing
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
