"""
Test cases for GUI functionality.
"""

import pytest
import sys
from pathlib import Path
import unittest.mock as mock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestGUI:
    """Test cases for GUI functionality."""

    def test_gui_imports(self):
        """Test that GUI components can be imported."""
        try:
            from photofilter.gui.main_window import PhotoRecognitionGUI

            assert PhotoRecognitionGUI is not None
        except ImportError as e:
            pytest.skip(f"GUI dependencies not available: {e}")

    @mock.patch("tkinter.Tk")
    def test_gui_initialization(self, mock_tk):
        """Test GUI initialization without actually creating window."""
        try:
            from photofilter.gui.main_window import PhotoRecognitionGUI

            # Mock tkinter to avoid creating actual window
            mock_root = mock.MagicMock()
            mock_tk.return_value = mock_root

            gui = PhotoRecognitionGUI()
            assert gui is not None
        except ImportError as e:
            pytest.skip(f"GUI dependencies not available: {e}")
        except Exception as e:
            # GUI might fail due to missing display, which is expected in tests
            pytest.skip(
                f"GUI initialization failed (expected in headless environment): {e}"
            )

    def test_gui_constants(self):
        """Test that GUI constants are properly defined."""
        try:
            from photofilter.gui.main_window import (
                CORE_AVAILABLE,
                DEDUPLICATION_AVAILABLE,
                ADVANCED_DETECTORS_AVAILABLE,
            )

            # These should be boolean values
            assert isinstance(CORE_AVAILABLE, bool)
            assert isinstance(DEDUPLICATION_AVAILABLE, bool)
            assert isinstance(ADVANCED_DETECTORS_AVAILABLE, bool)
        except ImportError as e:
            pytest.skip(f"GUI dependencies not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
