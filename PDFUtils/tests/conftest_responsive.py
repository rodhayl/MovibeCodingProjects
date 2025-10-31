"""Minimal conftest for testing only the ResponsiveFrame."""

import tkinter as tk

import pytest


@pytest.fixture(scope="module")
def root():
    """Create and yield a root Tkinter window for testing."""
    root = tk.Tk()
    root.withdraw()  # Don't show the window during tests
    yield root
    root.destroy()
