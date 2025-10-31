"""
Example test fixture using safe mocks to prevent memory leaks.
This file demonstrates how to use safe_mocks in real test cases.
"""

import gc

import pytest

from tests.safe_mocks import (
    SafeMockBooleanVar,
    SafeMockDoubleVar,
    SafeMockIntVar,
    SafeMockStringVar,
    cleanup_mock_variables,
    patch_tkinter_variables,
)

# Import UI safety module


class TestFixtureExample:
    """Test fixture using safe mocks."""

    @pytest.fixture
    def setup_safe_mocks(self):
        """Set up safe mocks for testing."""
        # Create mock variables
        mock_vars = []

        # Create string variables
        str_var = SafeMockStringVar("hello")
        mock_vars.append(str_var)

        # Create int variables
        int_var = SafeMockIntVar(42)
        mock_vars.append(int_var)

        # Create double variables
        double_var = SafeMockDoubleVar(3.14)
        mock_vars.append(double_var)

        # Create boolean variables
        bool_var = SafeMockBooleanVar(True)
        mock_vars.append(bool_var)

        # Return the variables to the test
        yield {
            "str_var": str_var,
            "int_var": int_var,
            "double_var": double_var,
            "bool_var": bool_var,
            "_mock_vars": mock_vars,  # Keep track for cleanup
        }

        # Clean up after the test
        cleanup_mock_variables(mock_vars)
        gc.collect()

    @pytest.mark.timeout(10)
    def test_with_safe_mocks(self, setup_safe_mocks):
        """Test using safe mocks."""
        # Get variables from fixture
        vars = setup_safe_mocks

        # Use the variables
        assert vars["str_var"].get() == "hello"
        assert vars["int_var"].get() == 42
        assert vars["double_var"].get() == 3.14
        assert vars["bool_var"].get() is True

        # Update variables
        vars["str_var"].set("world")
        vars["int_var"].set(99)
        vars["double_var"].set(2.71)
        vars["bool_var"].set(False)

        # Check updates
        assert vars["str_var"].get() == "world"
        assert vars["int_var"].get() == 99
        assert vars["double_var"].get() == 2.71
        assert vars["bool_var"].get() is False


class TestWithPatchingExample:
    """Example test class that patches tkinter variables."""

    @pytest.fixture(autouse=True)
    def setup_patches(self):
        """Set up patches for tkinter variables."""
        # Patch tkinter variables with our safe mocks
        patches = patch_tkinter_variables()

        yield

        # Stop all patches
        for p in patches:
            p.stop()

        # Force garbage collection
        gc.collect()

    @pytest.mark.timeout(10)
    def test_with_patched_tkinter(self):
        """Test using patched tkinter variables."""
        # Import tkinter here to use patched versions
        import tkinter as tk

        # Create tkinter variables - these will be our safe mocks
        str_var = tk.StringVar(value="test")
        int_var = tk.IntVar(value=42)
        double_var = tk.DoubleVar(value=3.14)
        bool_var = tk.BooleanVar(value=True)

        # Use the variables
        assert str_var.get() == "test"
        assert int_var.get() == 42
        assert double_var.get() == 3.14
        assert bool_var.get() is True
