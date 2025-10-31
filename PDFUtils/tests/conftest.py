from unittest.mock import MagicMock

import pytest

# Ensure global UI safety patches are applied across all tests
# Importing registers autouse fixtures in tests/ui_safety.py
from tests import ui_safety as _ui_safety  # noqa: F401


@pytest.fixture
def mock_root():
    """Mock tkinter root window."""
    root = MagicMock()
    root.winfo_width.return_value = 800
    root.winfo_height.return_value = 600
    return root


@pytest.fixture
def file_selector(mock_root):
    """Mock file selector component."""
    selector = MagicMock()
    selector.master = mock_root
    selector.path_entry = MagicMock()
    selector.browse_btn = MagicMock()
    selector.set_disabled = MagicMock()
    selector.get_files = MagicMock(return_value=["/test/file.pdf"])
    selector.set_files = MagicMock()
    selector.get_path = MagicMock(return_value="/test/path")
    selector.set_path = MagicMock()
    selector.clear = MagicMock()
    selector.validate_path = MagicMock(return_value=True)
    return selector


@pytest.fixture
def output_file_selector(mock_root):
    """Mock output file selector component."""
    selector = MagicMock()
    selector.master = mock_root
    selector.path_entry = MagicMock()
    selector.browse_btn = MagicMock()
    selector.set_disabled = MagicMock()
    selector.get_path = MagicMock(return_value="/test/output.pdf")
    selector.set_path = MagicMock()
    selector.clear = MagicMock()
    selector.validate_path = MagicMock(return_value=True)
    selector.path_exists = MagicMock(return_value=True)
    selector.browse_file = MagicMock()
    return selector


@pytest.fixture
def progress_tracker(mock_root):
    """Mock progress tracker component."""
    tracker = MagicMock()
    tracker.master = mock_root
    tracker.progress_bar = MagicMock()
    tracker.status_label = MagicMock()
    tracker.percentage_label = MagicMock()
    tracker.progress_var = MagicMock()
    tracker.status_var = MagicMock()
    tracker.percent_var = MagicMock()

    # Mock progress bar methods
    tracker.progress_bar.configure = MagicMock()
    tracker.progress_bar.get = MagicMock(return_value=50)

    # Mock label methods
    tracker.status_label.configure = MagicMock()
    tracker.percentage_label.configure = MagicMock()

    # Mock tracker methods
    tracker.set_progress = MagicMock()
    tracker.update_progress = MagicMock()
    tracker.set_status = MagicMock()
    tracker.reset = MagicMock()
    tracker.complete = MagicMock()
    tracker.update = MagicMock()
    tracker.is_running = MagicMock(return_value=False)

    return tracker


@pytest.fixture
def notification_panel(mock_root):
    """Mock notification panel component."""
    panel = MagicMock()
    panel.master = mock_root
    panel.message_label = MagicMock()
    panel.icon_label = MagicMock()
    panel.close_btn = MagicMock()

    # Mock methods
    panel.show_info = MagicMock()
    panel.show_warning = MagicMock()
    panel.show_error = MagicMock()
    panel.show_success = MagicMock()
    panel.hide = MagicMock()
    panel.clear = MagicMock()

    return panel


@pytest.fixture
def ocr_tab(mock_root):
    """Mock OCR tab component."""
    tab = MagicMock()
    tab.master = mock_root
    tab.file_selector = MagicMock()
    tab.output_selector = MagicMock()
    tab.progress_tracker = MagicMock()

    # Mock language variables
    tab.lang_var = MagicMock()
    tab.lang_var.get = MagicMock(return_value="eng")
    tab.lang_var.set = MagicMock()

    # Mock buttons and controls
    tab.ocr_button = MagicMock()
    tab.language_var = MagicMock()
    tab.dpi_var = MagicMock()
    tab.psm_var = MagicMock()

    # Mock methods
    tab.start_ocr = MagicMock()
    tab._perform_ocr = MagicMock()
    tab.cancel_ocr = MagicMock()
    tab.validate_inputs = MagicMock(return_value=True)
    tab.update_language = MagicMock()
    tab.extract_text = MagicMock(return_value="Sample OCR text")

    # Configure file selector
    tab.file_selector.get_files = MagicMock(return_value=["test.pdf"])
    tab.output_selector.get_path = MagicMock(return_value="output.txt")

    return tab


# PDF Fixtures for E2E OCR Tests
@pytest.fixture
def simple_text_pdf(tmp_path):
    """Create a simple PDF with text for testing."""
    pdf_file = tmp_path / "simple_text.pdf"
    # Create a PDF with actual text content using ReportLab
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(pdf_file), pagesize=letter)
        width, height = letter

        # Add text at a specific position
        c.setFont("Helvetica", 12)
        c.drawString(72, 720, "Hello")
        c.save()
    except ImportError:
        # Fallback to minimal PDF if ReportLab is not available
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000204 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
        pdf_file.write_bytes(pdf_content)
    return str(pdf_file)


@pytest.fixture
def multipage_pdf(tmp_path):
    """Create a multipage PDF for testing."""
    pdf_file = tmp_path / "multipage.pdf"
    # Create a minimal valid PDF with multiple pages
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R 5 0 R]
/Count 2
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 48
>>
stream
BT
/F1 12 Tf
72 720 Td
(Page 1) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 6 0 R
>>
endobj
6 0 obj
<<
/Length 48
>>
stream
BT
/F1 12 Tf
72 720 Td
(Page 2) Tj
ET
endstream
endobj
xref
0 7
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000125 00000 n
0000000214 00000 n
0000000313 00000 n
0000000402 00000 n
trailer
<<
/Size 7
/Root 1 0 R
>>
startxref
501
%%EOF"""
    pdf_file.write_bytes(pdf_content)
    return str(pdf_file)


@pytest.fixture
def image_pdf(tmp_path):
    """Create a PDF with image content for testing."""
    pdf_file = tmp_path / "image.pdf"
    # Create a minimal valid PDF that represents an image
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 47
>>
stream
BT
/F1 12 Tf
72 720 Td
(Image) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000204 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
302
%%EOF"""
    pdf_file.write_bytes(pdf_content)
    return str(pdf_file)


@pytest.fixture
def handwriting_pdf(tmp_path):
    """Create a PDF with handwriting content for testing."""
    pdf_file = tmp_path / "handwriting.pdf"
    # Create a PDF with handwriting text using ReportLab
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        # Handle both normal and mocked letter objects
        if hasattr(letter, "__len__") and len(letter) >= 2:
            width, height = letter
        else:
            # Default to standard letter size if letter is mocked
            width, height = 612, 792

        c = canvas.Canvas(str(pdf_file), pagesize=(width, height))

        # Add handwriting-like text at a specific position
        c.setFont("Helvetica", 14)
        c.drawString(72, 720, "Handwriting")
        c.save()
    except ImportError:
        # Fallback to minimal PDF if ReportLab is not available
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 55
>>
stream
BT
/F1 12 Tf
72 720 Td
(Handwriting) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000204 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
310
%%EOF"""
        pdf_file.write_bytes(pdf_content)
    return str(pdf_file)


@pytest.fixture
def table_pdf(tmp_path):
    """Create a PDF with table content for testing."""
    pdf_file = tmp_path / "table.pdf"
    # Create a minimal valid PDF that represents a table
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 47
>>
stream
BT
/F1 12 Tf
72 720 Td
(Table) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000204 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
302
%%EOF"""
    pdf_file.write_bytes(pdf_content)
    return str(pdf_file)


@pytest.fixture
def barcode_pdf(tmp_path):
    """Create a PDF with barcode content for testing."""
    pdf_file = tmp_path / "barcode.pdf"
    # Create a minimal valid PDF that represents a barcode
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 49
>>
stream
BT
/F1 12 Tf
72 720 Td
(Barcode) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000204 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
304
%%EOF"""
    pdf_file.write_bytes(pdf_content)
    return str(pdf_file)


@pytest.fixture
def about_tab(mock_root):
    """Mock about tab component."""
    tab = MagicMock()
    tab.master = mock_root
    tab.icon = MagicMock()
    tab.version_label = MagicMock()
    tab.description_label = MagicMock()

    # Mock icon properties
    tab.icon.size = (32, 32)
    tab.icon.width = 32
    tab.icon.height = 32

    # Mock methods
    tab.resize = MagicMock()
    tab.update_version = MagicMock()
    tab.load_icon = MagicMock()

    return tab
