"""Basic UI tests for PDFUtils."""

import shutil
import tempfile
import tkinter as tk
from pathlib import Path

import pytest

# Import UI safety module
from tests.ui_safety import (
    safe_ttkbootstrap,
)

# Skip if not on Windows - REMOVED for cross-platform testing
# pytestmark = pytest.mark.skipif(
#     not sys.platform.startswith('win'),
#     reason="GUI tests require Windows"
# )


class TestUIBasic:
    """Basic test cases for UI components."""

    def setup_method(self):
        """Setup test environment."""
        # Use ui_safety fixture instead of custom TkTestRoot
        from tests.ui_safety import _tk_manager

        self.root = _tk_manager.create_safe_root()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="pdfutils_"))
        self.parent = tk.Frame(self.root)
        self.parent.pack(fill="both", expand=True)
        try:
            self.root.update()
        except tk.TclError:
            pass  # Ignore if root is destroyed

    def teardown_method(self):
        """Cleanup after test."""
        if hasattr(self, "parent"):
            try:
                if hasattr(self.parent, "winfo_exists") and self.parent.winfo_exists():
                    for widget in self.parent.winfo_children():
                        try:
                            widget.pack_forget()
                            widget.destroy()
                        except (tk.TclError, RuntimeError, AttributeError):
                            pass  # Ignore cleanup errors
                    self.parent.destroy()
            except (tk.TclError, AttributeError):
                pass  # Ignore cleanup errors

        if hasattr(self, "temp_dir") and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass  # Ignore cleanup errors

    @pytest.mark.timeout(30)
    def test_imports(self):
        """Test that all required modules can be imported."""
        from pdfutils.responsive_app import ResponsiveApp
        from pdfutils.tabs.compress_tab import CompressTab
        from pdfutils.tabs.merge_tab import MergeTab
        from pdfutils.tabs.split_tab import SplitTab

        assert ResponsiveApp is not None
        assert MergeTab is not None
        assert SplitTab is not None
        assert CompressTab is not None

    @pytest.mark.timeout(30)
    def test_merge_tab_creation(self):
        """Test creating a MergeTab instance."""
        from pdfutils.tabs.merge_tab import MergeTab

        mock_app = object()

        with safe_ttkbootstrap():
            # Configure parent for grid layout
            self.parent.columnconfigure(0, weight=1)
            self.parent.rowconfigure(0, weight=1)
            tab = MergeTab(self.parent, mock_app)
            # TabContentFrame uses grid internally, so don't call pack
            self.root.update_idletasks()
            assert tab is not None
            assert hasattr(tab, "file_listbox")
            assert hasattr(tab, "merge_btn")
            assert hasattr(tab, "output_selector")
            tab.destroy()

    @pytest.mark.timeout(30)
    def test_split_tab_creation(self):
        """Test creating a SplitTab instance."""
        from pdfutils.tabs.split_tab import SplitTab

        mock_app = object()
        with safe_ttkbootstrap():
            # Configure parent for grid layout
            self.parent.columnconfigure(0, weight=1)
            self.parent.rowconfigure(0, weight=1)
            tab = SplitTab(self.parent, mock_app)
            # TabContentFrame uses grid internally, so don't call pack
            self.root.update_idletasks()
            assert tab is not None
            assert hasattr(tab, "file_selector")
            assert hasattr(tab, "split_btn")
            tab.destroy()

    @pytest.mark.timeout(30)
    def test_compress_tab_creation(self):
        """Test creating a CompressTab instance."""
        from pdfutils.tabs.compress_tab import CompressTab

        mock_app = object()
        with safe_ttkbootstrap():
            # Configure parent for grid layout
            self.parent.columnconfigure(0, weight=1)
            self.parent.rowconfigure(0, weight=1)
            tab = CompressTab(self.parent, mock_app)
            # TabContentFrame uses grid internally, so don't call pack
            self.root.update_idletasks()
            assert tab is not None
            assert hasattr(tab, "file_selector")
            assert hasattr(tab, "compress_btn")
            tab.destroy()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
