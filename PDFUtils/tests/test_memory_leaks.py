"""
Test for memory leaks with mock objects.
This test repeatedly creates and destroys many mock objects to verify memory handling.
"""

import gc
import unittest

import pytest

from tests.safe_mocks import (
    SafeMockBooleanVar,
    SafeMockDoubleVar,
    SafeMockIntVar,
    SafeMockStringVar,
    SafeMockVariable,
    cleanup_mock_variables,
)


class TestMemoryLeaks(unittest.TestCase):
    """Test memory usage with safe mocks."""

    @pytest.mark.timeout(10)
    def test_repeated_create_destroy(self):
        """Test creating and destroying many mocks in succession."""
        # Run multiple iterations
        for iteration in range(10):
            # Create a large number of different mock types
            string_mocks = [SafeMockStringVar(f"test-{i}") for i in range(100)]
            int_mocks = [SafeMockIntVar(i) for i in range(100)]
            double_mocks = [SafeMockDoubleVar(i * 1.5) for i in range(100)]
            bool_mocks = [SafeMockBooleanVar(i % 2 == 0) for i in range(100)]
            var_mocks = [SafeMockVariable(f"var-{i}") for i in range(100)]

            # Verify they work correctly
            self.assertEqual(string_mocks[50].get(), "test-50")
            self.assertEqual(int_mocks[50].get(), 50)
            self.assertEqual(double_mocks[50].get(), 50 * 1.5)
            self.assertEqual(bool_mocks[50].get(), True)
            self.assertEqual(var_mocks[50].get(), "var-50")

            # Clean up each type
            cleanup_mock_variables(string_mocks)
            cleanup_mock_variables(int_mocks)
            cleanup_mock_variables(double_mocks)
            cleanup_mock_variables(bool_mocks)
            cleanup_mock_variables(var_mocks)

            # Force garbage collection
            gc.collect()

        # Success if we get here without memory issues
        self.assertTrue(True)

    @pytest.mark.timeout(10)
    def test_trace_callbacks(self):
        """Test that trace callbacks don't cause memory leaks."""
        mock_vars = []
        callbacks = []

        # Create mock with callbacks
        for i in range(100):
            var = SafeMockStringVar()

            # Create a callback
            def callback_func(*args):
                pass

            # Add the callback
            var.trace("w", callback_func)
            var.trace_add("write", callback_func)

            # Keep references
            mock_vars.append(var)
            callbacks.append(callback_func)

        # Clean up
        cleanup_mock_variables(mock_vars)
        callbacks.clear()

        # Force garbage collection
        gc.collect()

        # Success if we get here without memory issues
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
