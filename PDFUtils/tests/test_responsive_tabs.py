"""Tests for the responsive tabs."""

import pytest

# pytest.importorskip("ttkbootstrap", reason="ttkbootstrap not installed" - REMOVED, using mocking
try:
    import ttkbootstrap  # noqa: F401
except ImportError:
    # Mock ttkbootstrap if not available
    import sys
    from unittest.mock import MagicMock

    mock_ttk = MagicMock()
    sys.modules["ttkbootstrap"] = mock_ttk
from unittest.mock import MagicMock, patch

# Import UI safety module


# Mock ttkbootstrap to avoid style issues
@pytest.fixture(autouse=True)
def mock_ttkbootstrap():
    """Mock ttkbootstrap to avoid style issues."""
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(
            "ttkbootstrap.style.Bootstyle.update_ttk_widget_style",
            lambda *args, **kwargs: "",
        )
        mp.setattr("ttkbootstrap.style.Bootstyle.ttkstyle_name", lambda *args, **kwargs: "")
        mp.setattr(
            "ttkbootstrap.style.Bootstyle.ttkstyle_widget_class",
            lambda *args, **kwargs: "",
        )
        yield


@pytest.fixture
def mock_parent():
    """Create a mock parent frame."""
    parent = MagicMock()
    # If winfo_children is needed, mock as attribute
    parent.winfo_children = MagicMock(return_value=[])
    parent.tk = MagicMock()
    parent._last_child_ids = {}
    parent.winfo_toplevel = MagicMock(return_value=parent)
    return parent


@pytest.fixture
def mock_app():
    """Create a mock app."""
    app = MagicMock()
    app.show_notification = MagicMock()
    app.set_status = MagicMock()
    return app


@pytest.mark.timeout(10)
def test_merge_tab_instantiation(mock_parent, mock_app):
    """Test that MergeTab can be instantiated."""
    from pdfutils.tabs.merge_tab import MergeTab

    with patch.object(MergeTab, "__init__", return_value=None) as mock_init:
        MergeTab(mock_parent, mock_app)  # noqa: F841
        mock_init.assert_called_once_with(mock_parent, mock_app)


@pytest.mark.timeout(10)
def test_split_tab_instantiation(mock_parent, mock_app):
    """Test that SplitTab can be instantiated."""
    from pdfutils.tabs.split_tab import SplitTab

    with patch.object(SplitTab, "__init__", return_value=None) as mock_init:
        SplitTab(mock_parent, mock_app)  # noqa: F841
        mock_init.assert_called_once_with(mock_parent, mock_app)


@pytest.mark.timeout(10)
def test_compress_tab_instantiation(mock_parent, mock_app):
    """Test that CompressTab can be instantiated."""
    from pdfutils.tabs.compress_tab import CompressTab

    with patch.object(CompressTab, "__init__", return_value=None) as mock_init:
        CompressTab(mock_parent, mock_app)  # noqa: F841
        mock_init.assert_called_once_with(mock_parent, mock_app)


@pytest.mark.timeout(10)
def test_extract_tab_instantiation(mock_parent, mock_app):
    """Test that ExtractTab can be instantiated."""
    from pdfutils.tabs.extract_tab import ExtractTab

    with patch.object(ExtractTab, "__init__", return_value=None) as mock_init:
        ExtractTab(mock_parent, mock_app)  # noqa: F841
        mock_init.assert_called_once_with(mock_parent, mock_app)


@pytest.mark.timeout(10)
def test_ocr_tab_instantiation(mock_parent, mock_app):
    """Test that OcrTab can be instantiated."""
    from pdfutils.tabs.ocr_tab import OcrTab

    with patch.object(OcrTab, "__init__", return_value=None) as mock_init:
        OcrTab(mock_parent, mock_app)  # noqa: F841
        mock_init.assert_called_once_with(mock_parent, mock_app)


@pytest.mark.timeout(10)
def test_table_extraction_tab_instantiation(mock_parent, mock_app):
    """Test that TableExtractionTab can be instantiated."""
    from pdfutils.tabs.table_extraction_tab import TableExtractionTab

    with patch.object(TableExtractionTab, "__init__", return_value=None) as mock_init:
        TableExtractionTab(mock_parent, mock_app)  # noqa: F841
        mock_init.assert_called_once_with(mock_parent, mock_app)


@pytest.mark.timeout(10)
def test_barcode_tab_instantiation(mock_parent, mock_app):
    """Test that BarcodeTab can be instantiated."""
    from pdfutils.tabs.barcode_tab import BarcodeTab

    with patch.object(BarcodeTab, "__init__", return_value=None) as mock_init:
        BarcodeTab(mock_parent, mock_app)  # noqa: F841
        mock_init.assert_called_once_with(mock_parent, mock_app)


@pytest.mark.timeout(10)
def test_handwriting_ocr_tab_instantiation(mock_parent, mock_app):
    """Test that HandwritingOcrTab can be instantiated."""
    from pdfutils.tabs.handwriting_ocr_tab import HandwritingOcrTab

    with patch.object(HandwritingOcrTab, "__init__", return_value=None) as mock_init:
        HandwritingOcrTab(mock_parent, mock_app)  # noqa: F841
        mock_init.assert_called_once_with(mock_parent, mock_app)


@pytest.mark.timeout(10)
def test_about_tab_instantiation(mock_parent, mock_app):
    """Test that AboutTab can be instantiated."""
    from pdfutils.tabs.about_tab import AboutTab

    with patch.object(AboutTab, "__init__", return_value=None) as mock_init:
        AboutTab(mock_parent, mock_app)  # noqa: F841
        mock_init.assert_called_once_with(mock_parent, mock_app)
