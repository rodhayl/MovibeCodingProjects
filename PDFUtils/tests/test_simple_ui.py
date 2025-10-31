#!/usr/bin/env python3
"""Minimal test file to check pytest imports work."""

import pytest

# Import UI safety module


def get_tk_color(widget, color_attr):
    """Helper to get the string representation of a Tkinter color."""
    color = widget.cget(color_attr)
    return str(color).lower()


@pytest.mark.timeout(10)
def test_simple():
    """Simple test."""
    assert True
