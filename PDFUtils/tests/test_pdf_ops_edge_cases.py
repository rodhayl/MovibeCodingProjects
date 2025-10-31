"""Edge case tests for pdf_ops functionality."""

from unittest import mock
from unittest.mock import MagicMock

import pytest


class TestPdfOpsEdgeCases:
    """Test edge cases for pdf_ops."""

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=False)
    def test_merge_pdfs_nonexistent_file(self, mock_exists):
        """Test merging nonexistent input file."""
        from pdfutils.pdf_ops import merge_pdfs

        with pytest.raises(FileNotFoundError, match="Input file not found"):
            merge_pdfs(["nonexistent.pdf"], "output.pdf")

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True)
    @mock.patch("pdfutils.pdf_ops.PdfReader")
    def test_merge_pdfs_corrupted_file(self, mock_reader, mock_exists):
        """Test merging corrupted input file."""
        from pdfutils.pdf_ops import merge_pdfs

        mock_reader.side_effect = Exception("Corrupted PDF")
        with pytest.raises(RuntimeError, match="Failed to read PDF"):
            merge_pdfs(["corrupted.pdf"], "output.pdf")

    @pytest.mark.timeout(10)
    def test_split_pdf_no_output_dir(self):
        """Test splitting without output directory."""
        from pdfutils.pdf_ops import split_pdf

        with pytest.raises(TypeError, match="output_dir is required"):
            split_pdf("input.pdf", None)

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=False)
    def test_split_pdf_nonexistent_file(self, mock_exists):
        """Test splitting nonexistent input file."""
        from pdfutils.pdf_ops import split_pdf

        with pytest.raises(FileNotFoundError, match="Input file not found"):
            split_pdf("nonexistent.pdf", "output_dir")

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True)
    @mock.patch("pdfutils.pdf_ops.PdfReader")
    def test_extract_page_range_invalid_range(self, mock_reader, mock_exists):
        """Test extracting with invalid page range."""
        from pdfutils.pdf_ops import extract_page_range

        mock_reader.return_value.pages = [MagicMock()] * 5  # 5 pages
        with pytest.raises(ValueError, match="Invalid page range"):
            extract_page_range("input.pdf", "output.pdf", 5, 3)

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=False)
    def test_extract_page_range_nonexistent_file(self, mock_exists):
        """Test extracting from nonexistent input file."""
        from pdfutils.pdf_ops import extract_page_range

        with pytest.raises(FileNotFoundError, match="Input file not found"):
            extract_page_range("nonexistent.pdf", "output.pdf", 1, 2)

    @pytest.mark.timeout(10)
    def test_compress_pdf_invalid_quality(self):
        """Test compressing with invalid quality setting."""
        from pdfutils.pdf_ops import compress_pdf

        # Mock Path.exists to return True so the quality check happens before file check
        with mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True):
            with pytest.raises(ValueError, match="Invalid quality setting"):
                compress_pdf("input.pdf", "output.pdf", "invalid_quality")

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=False)
    def test_compress_pdf_nonexistent_file(self, mock_exists):
        """Test compressing nonexistent input file."""
        from pdfutils.pdf_ops import compress_pdf

        with pytest.raises(FileNotFoundError, match="Input file not found"):
            compress_pdf("nonexistent.pdf", "output.pdf", "screen")

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops._HAVE_PYMUPDF", False)
    @mock.patch("pdfutils.pdf_ops.find_ghostscript_command", return_value=None)
    def test_compress_pdf_no_backends(self, mock_find_gs):
        """Test compressing when no compression backends are available."""
        from pdfutils.pdf_ops import compress_pdf

        # Mock Path.exists to return True so the backend check happens before file check
        with mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True):
            with pytest.raises(RuntimeError, match="Compression unavailable"):
                compress_pdf("input.pdf", "output.pdf", "screen")

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops._HAVE_PYMUPDF", False)
    @mock.patch("pdfutils.pdf_ops._HAVE_TESSERACT", False)
    def test_ocr_missing_dependencies(self):
        """Test OCR with missing dependencies."""
        from pdfutils.pdf_ops import extract_text_with_ocr

        # Mock Path.exists to return True so the dependency check happens before file check
        with mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True):
            with pytest.raises(RuntimeError, match="PyMuPDF is required"):
                extract_text_with_ocr("input.pdf", "output.txt")

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True)
    @mock.patch("pdfutils.pdf_ops._HAVE_TESSERACT", True)
    @mock.patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", False)
    def test_ocr_tesseract_not_installed(self):
        """Test OCR when Tesseract is not installed."""
        from pdfutils.pdf_ops import extract_text_with_ocr

        # Mock Path.exists to return True so the Tesseract check happens before file check
        with mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True):
            with pytest.raises(Exception, match="Tesseract OCR engine not found"):
                extract_text_with_ocr("input.pdf", "output.txt")

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True)
    @mock.patch("pdfutils.pdf_ops._HAVE_TESSERACT", True)
    @mock.patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=False)
    def test_ocr_nonexistent_file(self, mock_exists):
        """Test OCR on nonexistent input file."""
        from pdfutils.pdf_ops import extract_text_with_ocr

        with pytest.raises(FileNotFoundError, match="Input file not found"):
            extract_text_with_ocr("nonexistent.pdf", "output.txt")

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True)
    @mock.patch("pdfutils.pdf_ops._HAVE_TESSERACT", True)
    @mock.patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True)
    @mock.patch("pdfutils.pdf_ops.pdf_document")
    def test_ocr_invalid_page_range(self, mock_pdf_document, mock_exists):
        """Test OCR with invalid page range."""
        from pdfutils.pdf_ops import extract_text_with_ocr

        mock_doc = mock.MagicMock()
        mock_doc.__len__.return_value = 5
        mock_pdf_document.return_value.__enter__.return_value = mock_doc
        with pytest.raises(ValueError, match="Invalid page range"):
            extract_text_with_ocr("input.pdf", "output.txt", start_page=3, end_page=1)

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True)
    @mock.patch("pdfutils.pdf_ops._HAVE_TESSERACT", True)
    @mock.patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=False)
    def test_create_searchable_pdf_nonexistent_file(self, mock_exists):
        """Test creating searchable PDF from nonexistent input file."""
        from pdfutils.pdf_ops import create_searchable_pdf

        with pytest.raises(FileNotFoundError, match="Input file not found"):
            create_searchable_pdf("nonexistent.pdf", "output.pdf")

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True)
    @mock.patch("pdfutils.pdf_ops._HAVE_TESSERACT", True)
    @mock.patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True)
    @mock.patch("pdfutils.pdf_ops.fitz.open")
    def test_create_searchable_pdf_invalid_page_range(self, mock_fitz_open, mock_exists):
        """Test creating searchable PDF with invalid page range."""
        from pdfutils.pdf_ops import create_searchable_pdf

        mock_doc = mock.MagicMock()
        mock_doc.__len__.return_value = 5
        mock_fitz_open.return_value = mock_doc
        with pytest.raises(ValueError, match="Invalid page range"):
            create_searchable_pdf("input.pdf", "output.pdf", start_page=3, end_page=1)

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True)
    @mock.patch("pdfutils.pdf_ops.PdfReader")
    def test_split_at_page_invalid_page(self, mock_reader, mock_exists):
        """Test splitting at invalid page number."""
        from pdfutils.pdf_ops import split_at_page

        mock_reader.return_value.pages = [MagicMock()] * 5  # 5 pages
        with pytest.raises(ValueError, match="split_page must be between"):
            split_at_page("input.pdf", "output_dir", 0)

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True)
    @mock.patch("pdfutils.pdf_ops.PdfReader")
    def test_split_at_page_corrupted_file(self, mock_reader, mock_exists):
        """Test splitting corrupted input file."""
        from pdfutils.pdf_ops import split_at_page

        mock_reader.side_effect = Exception("Corrupted PDF")
        with pytest.raises(Exception, match="Corrupted PDF"):
            split_at_page("corrupted.pdf", "output_dir", 1)

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True)
    @mock.patch("pdfutils.pdf_ops.PdfReader")
    def test_extract_page_range_corrupted_file(self, mock_reader, mock_exists):
        """Test extracting from corrupted input file."""
        from pdfutils.pdf_ops import extract_page_range

        # For this test, we need to mock exists to return True first, then simulate corruption
        mock_exists.return_value = True
        mock_reader.side_effect = Exception("Corrupted PDF")
        with pytest.raises(RuntimeError, match="Failed to read PDF"):
            extract_page_range("corrupted.pdf", "output.pdf", 1, 2)

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True)
    @mock.patch("pdfutils.pdf_ops._HAVE_TESSERACT", True)
    @mock.patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True)
    @mock.patch("pdfutils.pdf_ops.pdf_document")
    def test_ocr_empty_pdf(self, mock_pdf_document, mock_exists):
        """Test OCR on empty PDF (no pages)."""
        import os
        import tempfile

        from pdfutils.pdf_ops import extract_text_with_ocr

        mock_doc = mock.MagicMock()
        mock_doc.__len__.return_value = 0
        mock_pdf_document.return_value.__enter__.return_value = mock_doc

        # Should not raise an exception for empty PDF, but create an empty output file
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "output.txt")
            extract_text_with_ocr("empty.pdf", output_file)
            # Output file should be created
            assert os.path.exists(output_file)
            # Output file should be empty
            with open(output_file) as f:
                assert f.read() == ""

    @pytest.mark.timeout(10)
    @mock.patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True)
    @mock.patch("pdfutils.pdf_ops._HAVE_TESSERACT", True)
    @mock.patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True)
    @mock.patch("pdfutils.pdf_ops.Path.exists", return_value=True)
    @mock.patch("pdfutils.pdf_ops.fitz.open")
    def test_create_searchable_pdf_empty_pdf(self, mock_fitz_open, mock_exists):
        """Test creating searchable PDF from empty PDF (no pages)."""
        from pdfutils.pdf_ops import create_searchable_pdf

        mock_doc = mock.MagicMock()
        mock_doc.__len__.return_value = 0
        mock_fitz_open.return_value = mock_doc
        with pytest.raises(ValueError, match="contains no pages"):
            create_searchable_pdf("empty.pdf", "output.pdf")
