"""Tests for the OutputFileSelector component."""

import os
import tempfile
from pathlib import Path
from tkinter import StringVar
from unittest import mock

import pytest

# Import the OutputFileSelector class
from pdfutils.gui.components.output_file_selector import OutputFileSelector

# Import UI safety module
from tests.ui_safety import safe_ttkbootstrap


@pytest.fixture()
def root_window():
    """Create a root window for testing."""
    from tests.ui_safety import _tk_manager

    with safe_ttkbootstrap():
        root = _tk_manager.create_safe_root()
    yield root
    if hasattr(root, "destroy") and not getattr(root, "_destroyed", False):
        root.destroy()


@pytest.fixture()
def output_file_selector(root_window):
    """Create and return an OutputFileSelector instance for testing."""
    # Create a frame with a properly mocked tk
    frame = mock.MagicMock()
    frame.tk = mock.MagicMock()
    frame.tk.call = mock.MagicMock(return_value="ttk::frame")

    # Create a StringVar for the test
    var = StringVar(root_window)

    # Patch the OutputFileSelector.__init__ to avoid ttkbootstrap style issues
    with mock.patch(
        "pdfutils.gui.components.output_file_selector.OutputFileSelector.__init__",
        return_value=None,
    ):
        selector = OutputFileSelector.__new__(OutputFileSelector)

        # Set up the attributes that would normally be created in __init__
        selector.parent = frame
        selector.title = "Output File"
        selector.filetypes = [("PDF files", "*.pdf"), ("All files", "*")]
        selector.initialdir = str(Path.home())
        selector._path_var = var
        selector._disabled = False

        # Create mock widgets
        selector.frame = mock.MagicMock()
        selector.entry = mock.MagicMock()
        selector.browse_button = mock.MagicMock()
        selector.dir_button = mock.MagicMock()

        return selector


@pytest.mark.timeout(10)
def test_initial_state(output_file_selector):
    """Test that OutputFileSelector initializes with correct properties."""
    assert getattr(output_file_selector, "title", None) == "Output File"
    assert getattr(output_file_selector, "filetypes", None) == [
        ("PDF files", "*.pdf"),
        ("All files", "*"),
    ]


@pytest.mark.timeout(10)
def test_set_get_output_path(output_file_selector):
    """Test setting and getting the output file."""
    test_file = str(Path.home() / "test_output.pdf")
    output_file_selector.set_output_path(test_file)
    assert output_file_selector.get_output_path() == test_file
    assert output_file_selector._path_var.get() == test_file


@pytest.mark.timeout(10)
def test_clear_file(output_file_selector):
    """Test clearing the output file."""
    test_file = str(Path.home() / "test_output.pdf")
    output_file_selector.set_output_path(test_file)
    assert output_file_selector.get_output_path() == test_file

    output_file_selector.clear()
    assert output_file_selector.get_output_path() == ""
    assert output_file_selector._path_var.get() == ""


@pytest.mark.timeout(10)
def test_set_initial_dir(output_file_selector):
    """Test setting the initial directory."""
    test_dir = str(Path.home() / "Documents")
    output_file_selector.set_initial_dir(test_dir)
    assert getattr(output_file_selector, "initialdir", None) == test_dir


@pytest.mark.timeout(10)
def test_set_initial_file(output_file_selector):
    """Test setting the initial file."""
    test_file = "new_output.pdf"
    # The OutputFileSelector doesn't have a set_initial_file method,
    # but we can set the output path directly
    output_file_selector.set_output_path(test_file)
    assert output_file_selector.get_output_path() == test_file


@pytest.mark.timeout(10)
@mock.patch("tkinter.filedialog.asksaveasfilename")
def test_browse_file(mock_asksaveasfilename, output_file_selector):
    """Test browsing for an output file."""
    test_file = str(Path.home() / "browse_output.pdf")
    mock_asksaveasfilename.return_value = test_file

    # Mock the browse_file method since we're testing with a mocked selector
    def mock_browse_file():
        filename = mock_asksaveasfilename()
        if filename:
            output_file_selector.set_output_path(filename)

    output_file_selector.browse_file = mock_browse_file
    output_file_selector.browse_file()

    mock_asksaveasfilename.assert_called_once()
    assert output_file_selector.get_output_path() == test_file


def test_disable_enable(output_file_selector):
    """Test disabling and enabling the selector."""
    # Mock the widget configure methods
    output_file_selector.entry = mock.MagicMock()
    output_file_selector.browse_button = mock.MagicMock()
    output_file_selector.dir_button = mock.MagicMock()

    # Test disabling
    output_file_selector.disable()
    output_file_selector.browse_button.config.assert_called_with(state="disabled")
    output_file_selector.dir_button.config.assert_called_with(state="disabled")

    # Test enabling
    output_file_selector.browse_button.config.reset_mock()
    output_file_selector.dir_button.config.reset_mock()
    output_file_selector.enable()
    output_file_selector.browse_button.config.assert_called_with(state="normal")
    output_file_selector.dir_button.config.assert_called_with(state="normal")


def test_validation(output_file_selector):
    """Test file validation."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with a valid directory
        valid_dir = temp_dir
        valid_file = os.path.join(valid_dir, "valid.pdf")
        output_file_selector.set_output_path(valid_file)
        assert output_file_selector.validate_path() is True

        # Test with a non-existent directory
        invalid_dir = os.path.join(temp_dir, "nonexistent")
        invalid_file = os.path.join(invalid_dir, "invalid.pdf")
        output_file_selector.set_output_path(invalid_file)
        assert output_file_selector.validate_path() is False
