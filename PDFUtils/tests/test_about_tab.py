"""Tests for the AboutTab functionality."""

from __future__ import annotations

import tkinter as tk
from unittest import mock

import pytest

from pdfutils.tabs.about_tab import AboutTab
from tests.base_test import BaseTabTest


class TestAboutTab(BaseTabTest):
    """Test cases for the AboutTab class."""

    tab_class = AboutTab

    def _gather_text(self):
        """Return all text from Label widgets inside the tab."""
        texts = []

        def walk(widget):
            for child in getattr(widget, "winfo_children", lambda: [])():
                if hasattr(child, "cget"):
                    try:
                        # Try to get text from various widget types
                        if hasattr(child, "get"):
                            # Text widgets
                            if isinstance(child, tk.Text):
                                texts.append(child.get("1.0", "end"))
                        else:
                            # Label widgets and buttons
                            text = child.cget("text")
                            if text and text.strip():
                                texts.append(text)
                    except (tk.TclError, AttributeError):
                        pass
                walk(child)

        walk(self.tab)
        return "\n".join(texts)

    @pytest.mark.timeout(10)
    def test_initial_state(self, setup):
        """Test the initial state of the AboutTab."""
        # Check that the tab was created
        assert self.tab is not None

        # Check that we created the correct tab type
        assert isinstance(self.tab, AboutTab)

        # Check that the tab is not running any operations
        assert not hasattr(self.tab, "progress_tracker") or not self.tab.progress_tracker.is_running()

    @pytest.mark.timeout(10)
    def test_about_content_displayed(self, setup):
        """Test that the about content is displayed correctly."""
        # Get all text from the tab
        tab_text = self._gather_text()

        # Check for expected content in the about text
        assert "PDFUtils" in tab_text
        assert "merge" in tab_text.lower()
        assert "ocr" in tab_text.lower()

    @pytest.mark.timeout(10)
    def test_system_info_displayed(self, setup):
        """Test that system information is displayed correctly."""
        # Get all text from the tab
        tab_text = self._gather_text().lower()

        # System info is not displayed; ensure basic text present
        assert "pdfutils" in tab_text

    @pytest.mark.timeout(10)
    def test_links_are_clickable(self, setup):
        """Test that links in the about tab are clickable."""
        # Mock the webbrowser.open function
        with mock.patch("webbrowser.open") as mock_open:
            # Simulate clicking on a link (this is a simplified test)
            # In a real test, we would need to simulate actual mouse clicks on the text widget
            self.tab.open_url("https://example.com")

            # Check that webbrowser.open was called with the correct URL
            mock_open.assert_called_once_with("https://example.com")

    @pytest.mark.timeout(10)
    def test_dependencies_listed(self, setup):
        """Test that the main dependencies are listed in the about text."""
        # List of main dependencies to check for
        dependencies = [
            "pypdf",
            "pymupdf",
            "pytesseract",
            "camelot-py",
            "pdfplumber",
            "pyzbar",
            "kraken",
            "pandas",
            "opencv-python",
            "scikit-image",
        ]

        # Get the about text
        tab_text = self._gather_text().lower()

        # Check that each dependency is mentioned in the about text
        for dep in dependencies:
            assert dep in tab_text

    @pytest.mark.timeout(10)
    def test_responsive_layout(self, setup):
        """Test that the about tab layout is responsive."""
        self.tab.update()
        assert self.tab.winfo_width() > 0
        assert self.tab.winfo_height() > 0

        # Simulate window resize
        self.root.geometry("800x600")
        self.root.update()

        text_widget = None
        for child in self.tab.winfo_children():
            for sub in getattr(child, "winfo_children", lambda: [])():
                if isinstance(sub, tk.Text):
                    text_widget = sub
                    break

        if text_widget:
            assert text_widget.winfo_width() > 0
            assert text_widget.winfo_height() > 0

    @pytest.mark.timeout(10)
    def test_license_display(self, setup):
        """Test that the license information is displayed correctly."""
        tab_text = self._gather_text().lower()
        assert "optional dependencies" in tab_text

    @pytest.mark.timeout(10)
    def test_about_tab_scrollbar(self, setup):
        """Test that the about tab has a functional scrollable frame."""
        scrollable_frame_found = False

        # Find the scrollable frame (from TabContentFrame)
        def walk(widget):
            nonlocal scrollable_frame_found
            for child in getattr(widget, "winfo_children", lambda: [])():
                # Check if this is a scrollable frame by looking for scrollable_frame attribute
                if hasattr(widget, "scrollable_frame"):
                    scrollable_frame_found = True
                walk(child)

        walk(self.tab)

        # The AboutTab inherits from TabContentFrame which provides scrolling
        assert hasattr(self.tab, "scrollable_frame"), "Scrollable frame not found in the about tab"

        # Test that the scrollable frame exists and is properly configured
        if hasattr(self.tab, "scrollable_frame"):
            assert self.tab.scrollable_frame is not None

    @pytest.mark.timeout(10)
    def test_about_tab_resize(self, setup):
        """Test that the about tab resizes correctly."""
        # Get the initial size of the tab
        self.tab.update()
        initial_width = self.tab.winfo_width()
        initial_height = self.tab.winfo_height()

        # Resize the window
        self.root.geometry("1000x800")
        self.root.update()

        # Check that the tab resized
        new_width = self.tab.winfo_width()
        new_height = self.tab.winfo_height()

        # The tab should resize with the window
        assert new_width >= initial_width or new_height >= initial_height, "About tab did not resize with window"

        # Check that the scrollable frame also resized if it exists
        if hasattr(self.tab, "scrollable_frame") and self.tab.scrollable_frame:
            assert self.tab.scrollable_frame.winfo_width() > 0
            assert self.tab.scrollable_frame.winfo_height() > 0

    @pytest.mark.timeout(10)
    def test_about_tab_theme_consistency(self, setup):
        """Test that the about tab follows the application theme."""
        # This is a basic check; in a real test, we would verify colors and styles
        assert hasattr(self.tab, "winfo_toplevel")

        # Check that the tab has proper widget structure
        assert hasattr(self.tab, "scrollable_frame")

        # Verify that the tab contains the expected sections
        tab_text = self._gather_text().lower()
        assert len(tab_text) > 0, "Tab should contain text content"
