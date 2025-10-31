"""Minimal test to identify import issues."""

import pytest


@pytest.mark.timeout(10)
def test_imports():
    """Test importing required modules."""
    try:
        from pdfutils.tabs.merge_tab import MergeTab  # noqa: F401
        from tests.base_test import BaseTabTest  # noqa: F401

        assert True, "Imports successful"
    except ImportError as e:
        assert False, f"Import failed: {e}"
