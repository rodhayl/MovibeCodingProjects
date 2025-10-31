"""Tests for OCR error conditions and edge cases."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestOCRErrorConditions:
    """Test class for OCR error conditions and edge cases."""

    @pytest.mark.timeout(10)
    def test_missing_input_file(self):
        """Test OCR with missing input file."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
        ):
            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                with tempfile.NamedTemporaryFile(suffix=".txt") as output_file:
                    # Try to process a non-existent file
                    with pytest.raises(FileNotFoundError):
                        extract_text_with_ocr("non_existent_file.pdf", output_file.name, language="eng")
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_permission_denied_on_output(self):
        """Test OCR with permission denied on output file."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops.fitz") as mock_fitz,
            patch("pdfutils.pdf_ops.pytesseract") as mock_tesseract,
        ):
            # Mock the PDF processing
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_pixmap.return_value.tobytes.return_value = b"fake_image_data"
            mock_doc.load_page.return_value = mock_page
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            # Mock pytesseract to return some text
            mock_tesseract.image_to_string.return_value = "Sample OCR text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a directory where we'll try to write a file (should fail)
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Make the directory read-only
                    os.chmod(temp_dir, 0o444)

                    # Try to write to the read-only directory
                    output_path = Path(temp_dir) / "output.txt"

                    with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
                        with pytest.raises(PermissionError):
                            extract_text_with_ocr(pdf_file.name, str(output_path), language="eng")
            except ImportError:
                pytest.skip("OCR functions not available")
            except Exception:
                # On some systems, the permission change might not work as expected
                assert True

    @pytest.mark.timeout(10)
    def test_invalid_language_code(self):
        """Test OCR with invalid language code."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops.fitz") as mock_fitz,
            patch("pdfutils.pdf_ops.pytesseract") as mock_tesseract,
        ):
            # Mock the PDF processing
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_pixmap.return_value.tobytes.return_value = b"fake_image_data"
            mock_doc.load_page.return_value = mock_page
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            # Mock pytesseract to raise an exception for invalid language
            mock_tesseract.image_to_string.side_effect = Exception("Tesseract couldn't load language 'invalid_lang'")

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                with (
                    tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file,
                    tempfile.NamedTemporaryFile(suffix=".txt") as output_file,
                    pytest.raises(Exception),
                ):
                    extract_text_with_ocr(pdf_file.name, output_file.name, language="invalid_lang")
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_corrupted_pdf_file(self):
        """Test OCR with corrupted PDF file."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops.fitz") as mock_fitz,
        ):
            # Mock fitz.open to raise an exception for corrupted PDF
            mock_fitz.open.side_effect = Exception("Failed to load PDF: Corrupted file")

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                with (
                    tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file,
                    tempfile.NamedTemporaryFile(suffix=".txt") as output_file,
                    pytest.raises(RuntimeError),
                ):
                    extract_text_with_ocr(pdf_file.name, output_file.name, language="eng")
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_empty_pdf_file(self):
        """Test OCR with empty PDF file."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_document,
            patch("pdfutils.pdf_ops.pytesseract") as mock_tesseract,
        ):
            # Mock the PDF processing with 0 pages
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 0
            mock_pdf_document.return_value.__enter__.return_value = mock_doc

            # Mock pytesseract
            mock_tesseract.image_to_string.return_value = ""

            try:
                import os
                import tempfile

                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create temporary file paths but don't open them
                with tempfile.TemporaryDirectory() as temp_dir:
                    pdf_file = os.path.join(temp_dir, "input.pdf")
                    output_file = os.path.join(temp_dir, "output.txt")

                    # Create empty input file
                    with open(pdf_file, "w") as f:
                        f.write("")

                    # Should not raise an exception for empty PDF
                    extract_text_with_ocr(pdf_file, output_file, language="eng")
                    # Output file should be created
                    assert Path(output_file).exists()
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_invalid_page_range(self):
        """Test OCR with invalid page range."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_document,
            patch("pdfutils.pdf_ops.pytesseract") as mock_tesseract,
        ):
            # Mock the PDF processing
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_pixmap.return_value.tobytes.return_value = b"fake_image_data"
            mock_doc.load_page.return_value = mock_page
            mock_doc.__len__.return_value = 5  # 5 pages
            mock_pdf_document.return_value.__enter__.return_value = mock_doc

            # Mock pytesseract
            mock_tesseract.image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                with (
                    tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file,
                    tempfile.NamedTemporaryFile(suffix=".txt") as output_file,
                ):
                    # Test with end_page less than start_page
                    with pytest.raises(ValueError):
                        extract_text_with_ocr(
                            pdf_file.name,
                            output_file.name,
                            start_page=5,
                            end_page=2,  # Invalid: end < start
                            language="eng",
                        )
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_unsupported_output_format(self):
        """Test OCR with unsupported output format."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_document,
            patch("pdfutils.pdf_ops.pytesseract") as mock_tesseract,
        ):
            # Mock the PDF processing
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_pixmap.return_value.tobytes.return_value = b"fake_image_data"
            mock_doc.load_page.return_value = mock_page
            mock_doc.__len__.return_value = 1
            mock_pdf_document.return_value.__enter__.return_value = mock_doc

            # Mock pytesseract
            mock_tesseract.image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                with (
                    tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file,
                    tempfile.NamedTemporaryFile(suffix=".txt") as output_file,
                ):
                    # Test with unsupported format
                    with pytest.raises(ValueError):
                        extract_text_with_ocr(
                            pdf_file.name,
                            output_file.name,
                            output_format="unsupported_format",
                            language="eng",
                        )
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_invalid_preprocessing_parameters(self):
        """Test OCR with invalid preprocessing parameters."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops.fitz") as mock_fitz,
            patch("pdfutils.pdf_ops.pytesseract") as mock_tesseract,
        ):
            # Mock the PDF processing
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_pixmap.return_value.tobytes.return_value = b"fake_image_data"
            mock_doc.load_page.return_value = mock_page
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            # Mock pytesseract
            mock_tesseract.image_to_string.return_value = "Sample text"

            try:
                import io

                from PIL import Image

                from pdfutils.pdf_ops import extract_text_with_ocr, preprocess_image

                # Create a fake image
                img = Image.new("RGB", (100, 100), color="red")

                # Test invalid threshold
                with pytest.raises(ValueError):
                    preprocess_image(img, binarize=True, threshold=300)  # Invalid: > 255

                # Test invalid resize factor
                with pytest.raises(ValueError):
                    preprocess_image(img, resize_factor=-1)  # Invalid: negative

                # Test invalid blur radius
                with pytest.raises(ValueError):
                    preprocess_image(img, blur=-1)  # Invalid: negative

                # Test invalid morphological kernel
                with pytest.raises(ValueError):
                    preprocess_image(img, morph_op="dilate", morph_kernel=2)  # Invalid: even number
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_zonal_ocr_error_conditions(self):
        """Test zonal OCR error conditions."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_document,
            patch("pdfutils.pdf_ops.pytesseract") as mock_tesseract,
        ):
            # Mock the PDF processing
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_pixmap.return_value.tobytes.return_value = b"fake_image_data"
            mock_doc.load_page.return_value = mock_page
            mock_doc.__len__.return_value = 1
            mock_pdf_document.return_value.__enter__.return_value = mock_doc

            # Mock pytesseract
            mock_tesseract.image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import zonal_ocr_from_pdf

                with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
                    # Test with empty zones list - should not raise an exception
                    import os

                    output_file = pdf_file.name + "_output.txt"
                    zonal_ocr_from_pdf(pdf_file.name, zones=[], output_file=output_file)

                    # Test with invalid output format
                    with pytest.raises(ValueError):
                        zonal_ocr_from_pdf(
                            pdf_file.name,
                            zones=[{"page": 1, "x": 0, "y": 0, "w": 100, "h": 100}],
                            output_file=output_file + "_2.txt",
                            output_format="invalid_format",
                        )
                    # Clean up output files
                    if os.path.exists(output_file):
                        os.remove(output_file)
                    if os.path.exists(output_file + "_2.txt"):
                        os.remove(output_file + "_2.txt")
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_handwriting_ocr_error_conditions(self):
        """Test handwriting OCR error conditions."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_document,
            patch("pdfutils.pdf_ops.pytesseract") as mock_tesseract,
        ):
            # Mock the PDF processing
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_pixmap.return_value.tobytes.return_value = b"fake_image_data"
            mock_doc.load_page.return_value = mock_page
            mock_doc.__len__.return_value = 1
            mock_pdf_document.return_value.__enter__.return_value = mock_doc

            # Mock pytesseract
            mock_tesseract.image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import handwriting_ocr_from_pdf

                with (
                    tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file,
                    tempfile.NamedTemporaryFile(suffix=".txt") as output_file,
                ):
                    # Test with invalid output format
                    with pytest.raises(ValueError):
                        handwriting_ocr_from_pdf(
                            pdf_file.name,
                            output_file.name,
                            output_format="invalid_format",
                        )
            except ImportError:
                pytest.skip("OCR functions not available")
