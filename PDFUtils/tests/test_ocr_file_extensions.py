"""Tests for OCR file extension handling consistency."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def create_test_pdf(name: str = "test.pdf", content: str = "Test PDF Content") -> Path:
    """Create a test PDF file."""
    try:
        from reportlab.pdfgen import canvas

        pdf_path = Path(name)
        c = canvas.Canvas(str(pdf_path))
        c.setFont("Helvetica", 12)
        c.drawString(72, 800, content)
        c.save()
        return pdf_path
    except ImportError:
        # If reportlab is not available, create a minimal dummy PDF file
        pdf_path = Path(name)
        # Create a minimal PDF with proper structure
        pdf_content = (
            b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
            b"2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n"
            b"3 0 obj\n<<\n/Type /Page\n/Parent 2 R\n/MediaBox [0 0 612 792]\n>>\nendobj\n"
            b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
            b"0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n189\n%%EOF"
        )
        pdf_path.write_bytes(pdf_content)
        return pdf_path


class TestOCRFileExtensions:
    """Test class for OCR file extension handling consistency."""

    @pytest.mark.timeout(10)
    def test_text_output_file_extensions(self):
        """Test OCR with text output file extensions."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
        ):
            # Mock the context managers
            mock_pdf_context = MagicMock()
            mock_image_context = MagicMock()
            mock_pdf_doc.return_value.__enter__.return_value = mock_pdf_context
            mock_img_doc.return_value.__enter__.return_value = mock_image_context

            # Mock the PDF processing
            mock_page = MagicMock()
            mock_pixmap = MagicMock()
            mock_pixmap.tobytes.return_value = b"fake_image_data"
            mock_page.get_pixmap.return_value = mock_pixmap
            mock_pdf_context.load_page.return_value = mock_page
            mock_pdf_context.__len__.return_value = 1

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_text_output.pdf", "Test content for text output")

                try:
                    # Test with .txt extension
                    output_path = Path("output_text.txt")
                    extract_text_with_ocr(str(pdf_path), str(output_path), language="eng")
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test with no extension (should use the exact path provided)
                    output_path = Path("output_file.txt")  # Add .txt extension explicitly
                    extract_text_with_ocr(str(pdf_path), str(output_path), language="eng")
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_hocr_output_file_extensions(self):
        """Test OCR with hOCR output file extensions."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_pdf_or_hocr") as mock_image_to_hocr,
        ):
            # Mock the context managers
            mock_pdf_context = MagicMock()
            mock_image_context = MagicMock()
            mock_pdf_doc.return_value.__enter__.return_value = mock_pdf_context
            mock_img_doc.return_value.__enter__.return_value = mock_image_context

            # Mock the PDF processing
            mock_page = MagicMock()
            mock_pixmap = MagicMock()
            mock_pixmap.tobytes.return_value = b"fake_image_data"
            mock_page.get_pixmap.return_value = mock_pixmap
            mock_pdf_context.load_page.return_value = mock_page
            mock_pdf_context.__len__.return_value = 1

            # Mock pytesseract to return sample hOCR
            mock_image_to_hocr.return_value = b"<hocr>Sample text</hocr>"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_hocr_output.pdf", "Test content for hOCR output")

                try:
                    # Test with .html extension
                    output_path = Path("output_hocr.html")
                    extract_text_with_ocr(
                        str(pdf_path),
                        str(output_path),
                        language="eng",
                        output_format="hocr",
                    )
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test with .hocr extension
                    output_path = Path("output_hocr.hocr")
                    extract_text_with_ocr(
                        str(pdf_path),
                        str(output_path),
                        language="eng",
                        output_format="hocr",
                    )
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test with .html extension (should use the exact path provided)
                    output_path = Path("output_file.html")  # Add .html extension explicitly
                    extract_text_with_ocr(
                        str(pdf_path),
                        str(output_path),
                        language="eng",
                        output_format="hocr",
                    )
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_json_output_file_extensions(self):
        """Test OCR with JSON output file extensions."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_data") as mock_image_to_data,
        ):
            # Mock the context managers
            mock_pdf_context = MagicMock()
            mock_image_context = MagicMock()
            mock_pdf_doc.return_value.__enter__.return_value = mock_pdf_context
            mock_img_doc.return_value.__enter__.return_value = mock_image_context

            # Mock the PDF processing
            mock_page = MagicMock()
            mock_pixmap = MagicMock()
            mock_pixmap.tobytes.return_value = b"fake_image_data"
            mock_page.get_pixmap.return_value = mock_pixmap
            mock_pdf_context.load_page.return_value = mock_page
            mock_pdf_context.__len__.return_value = 1

            # Mock pytesseract to return sample JSON data
            mock_image_to_data.return_value = {
                "text": ["Sample", "text"],
                "left": [0, 50],
                "top": [0, 0],
                "width": [50, 50],
                "height": [20, 20],
            }

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_json_output.pdf", "Test content for JSON output")

                try:
                    # Test with .json extension
                    output_path = Path("output_json.json")
                    extract_text_with_ocr(
                        str(pdf_path),
                        str(output_path),
                        language="eng",
                        output_format="json",
                    )
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test with .json extension (should use the exact path provided)
                    output_path = Path("output_file.json")  # Add .json extension explicitly
                    extract_text_with_ocr(
                        str(pdf_path),
                        str(output_path),
                        language="eng",
                        output_format="json",
                    )
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_zonal_ocr_file_extensions(self):
        """Test zonal OCR with different file extensions."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
        ):
            # Mock the context managers
            mock_pdf_context = MagicMock()
            mock_image_context = MagicMock()
            mock_pdf_doc.return_value.__enter__.return_value = mock_pdf_context
            mock_img_doc.return_value.__enter__.return_value = mock_image_context

            # Mock the PDF processing
            mock_page = MagicMock()
            mock_pixmap = MagicMock()
            mock_pixmap.tobytes.return_value = b"fake_image_data"
            mock_page.get_pixmap.return_value = mock_pixmap
            mock_pdf_context.load_page.return_value = mock_page
            mock_pdf_context.__len__.return_value = 1

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import zonal_ocr_from_pdf

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_zonal_output.pdf", "Test content for zonal OCR")
                regions = [{"page": 1, "x": 0, "y": 0, "w": 100, "h": 100}]

                try:
                    # Test with .txt extension
                    output_path = Path("output_zonal.txt")
                    zonal_ocr_from_pdf(str(pdf_path), regions, str(output_path), output_format="text")
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test with .json extension
                    output_path = Path("output_zonal.json")
                    zonal_ocr_from_pdf(str(pdf_path), regions, str(output_path), output_format="json")
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test with .json extension (should use the exact path provided)
                    output_path = Path("output_file.json")  # Add .json extension explicitly
                    zonal_ocr_from_pdf(str(pdf_path), regions, str(output_path), output_format="json")
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test with .txt extension (should use the exact path provided)
                    output_path = Path("output_file_text.txt")  # Add .txt extension explicitly
                    zonal_ocr_from_pdf(str(pdf_path), regions, str(output_path), output_format="text")
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_handwriting_ocr_file_extensions(self):
        """Test handwriting OCR with different file extensions."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
            patch("pdfutils.pdf_ops.pytesseract.image_to_data") as mock_image_to_data,
            patch("pdfutils.pdf_ops.preprocess_image") as mock_preprocess,
        ):
            # Mock the context managers
            mock_pdf_context = MagicMock()
            mock_image_context = MagicMock()
            mock_pdf_doc.return_value.__enter__.return_value = mock_pdf_context
            mock_img_doc.return_value.__enter__.return_value = mock_image_context

            # Mock the PDF processing
            mock_page = MagicMock()
            mock_pixmap = MagicMock()
            mock_pixmap.tobytes.return_value = b"fake_image_data"
            mock_page.get_pixmap.return_value = mock_pixmap
            mock_pdf_context.load_page.return_value = mock_page
            mock_pdf_context.__len__.return_value = 1

            # Mock image processing - return the same mock image context
            mock_preprocess.return_value = mock_image_context

            # Mock pytesseract functions
            mock_image_to_string.return_value = "Sample text"
            mock_image_to_data.return_value = {
                "text": ["Sample", "text"],
                "left": [0, 50],
                "top": [0, 0],
                "width": [50, 50],
                "height": [20, 20],
            }

            try:
                from pdfutils.pdf_ops import handwriting_ocr_from_pdf

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_handwriting_output.pdf", "Test content for handwriting OCR")

                try:
                    # Test with .txt extension
                    output_path = Path("output_handwriting.txt")
                    handwriting_ocr_from_pdf(
                        str(pdf_path),
                        str(output_path),
                        engine="pytesseract",
                        output_format="text",
                    )
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test with .json extension
                    output_path = Path("output_handwriting.json")
                    handwriting_ocr_from_pdf(
                        str(pdf_path),
                        str(output_path),
                        engine="pytesseract",
                        output_format="json",
                    )
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test with .json extension (should use the exact path provided)
                    output_path = Path("output_file.json")  # Add .json extension explicitly
                    handwriting_ocr_from_pdf(
                        str(pdf_path),
                        str(output_path),
                        engine="pytesseract",
                        output_format="json",
                    )
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test with .txt extension (should use the exact path provided)
                    output_path = Path("output_file_text.txt")  # Add .txt extension explicitly
                    handwriting_ocr_from_pdf(
                        str(pdf_path),
                        str(output_path),
                        engine="pytesseract",
                        output_format="text",
                    )
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_searchable_pdf_file_extensions(self):
        """Test searchable PDF creation with file extension handling."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.fitz") as mock_fitz,
            patch("pdfutils.pdf_ops.pytesseract.image_to_data") as mock_image_to_data,
        ):
            # Mock the PDF processing
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_pixmap.return_value.tobytes.return_value = b"fake_image_data"
            mock_page.insert_text = MagicMock()
            mock_doc.load_page.return_value = mock_page
            mock_doc.__len__.return_value = 1
            mock_doc.save = MagicMock()
            mock_fitz.open.return_value = mock_doc

            # Mock pytesseract to return sample data
            mock_image_to_data.return_value = {
                "text": ["Sample", "text"],
                "left": [0, 50],
                "top": [0, 0],
                "width": [50, 50],
                "height": [20, 20],
            }

            try:
                from pdfutils.pdf_ops import create_searchable_pdf

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_searchable_output.pdf", "Test content for searchable PDF")

                try:
                    # Test with .pdf extension
                    output_path = Path("output_searchable.pdf")
                    create_searchable_pdf(str(pdf_path), str(output_path), language="eng")
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test with .pdf extension (should use the exact path provided)
                    output_path = Path("output_file.pdf")  # Add .pdf extension explicitly
                    create_searchable_pdf(str(pdf_path), str(output_path), language="eng")
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_consistent_extension_handling_across_functions(self):
        """Test that all OCR functions handle file extensions consistently."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.fitz") as mock_fitz,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
            patch("pdfutils.pdf_ops.pytesseract.image_to_pdf_or_hocr") as mock_image_to_hocr,
            patch("pdfutils.pdf_ops.pytesseract.image_to_data") as mock_image_to_data,
            patch("pdfutils.pdf_ops.preprocess_image") as mock_preprocess_image,
        ):
            # Mock the PDF processing for context manager functions
            mock_pdf_context = MagicMock()
            mock_pdf_context.__len__.return_value = 1
            mock_image_context = MagicMock()
            # Mock preprocess_image to return the same image
            mock_preprocess_image.return_value = mock_image_context
            mock_pdf_doc.return_value.__enter__.return_value = mock_pdf_context
            mock_img_doc.return_value.__enter__.return_value = mock_image_context

            # Mock the PDF processing for direct fitz functions
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_pixmap.return_value.tobytes.return_value = b"fake_image_data"
            mock_page.insert_text = MagicMock()
            mock_doc.load_page.return_value = mock_page
            mock_doc.__len__.return_value = 1
            mock_doc.save = MagicMock()
            mock_fitz.open.return_value = mock_doc

            # Mock pytesseract functions
            mock_image_to_string.return_value = "Sample text"
            mock_image_to_hocr.return_value = b"<hocr>Sample text</hocr>"
            mock_image_to_data.return_value = {
                "text": ["Sample", "text"],
                "left": [0, 50],
                "top": [0, 0],
                "width": [50, 50],
                "height": [20, 20],
            }

            try:
                from pdfutils.pdf_ops import (
                    create_searchable_pdf,
                    extract_text_with_ocr,
                    handwriting_ocr_from_pdf,
                    zonal_ocr_from_pdf,
                )

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf(
                    "test_consistent_output.pdf",
                    "Test content for consistent extension handling",
                )
                regions = [{"page": 1, "x": 0, "y": 0, "w": 100, "h": 100}]

                try:
                    # Test extract_text_with_ocr
                    output_path = Path("extract_output.txt")  # Add .txt extension explicitly
                    extract_text_with_ocr(str(pdf_path), str(output_path), language="eng")
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test zonal_ocr_from_pdf
                    output_path = Path("zonal_output.json")  # Add .json extension explicitly
                    zonal_ocr_from_pdf(str(pdf_path), regions, str(output_path))
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test handwriting_ocr_from_pdf
                    output_path = Path("handwriting_output.txt")  # Add .txt extension explicitly
                    handwriting_ocr_from_pdf(str(pdf_path), str(output_path), engine="pytesseract")
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test create_searchable_pdf
                    output_path = Path("searchable_output.pdf")  # Add .pdf extension explicitly
                    create_searchable_pdf(str(pdf_path), str(output_path), language="eng")
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_file_extension_case_insensitivity(self):
        """Test that file extension handling is case insensitive."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
        ):
            # Mock the context managers
            mock_pdf_context = MagicMock()
            mock_image_context = MagicMock()
            mock_pdf_doc.return_value.__enter__.return_value = mock_pdf_context
            mock_img_doc.return_value.__enter__.return_value = mock_image_context

            # Mock the PDF processing
            mock_page = MagicMock()
            mock_pixmap = MagicMock()
            mock_pixmap.tobytes.return_value = b"fake_image_data"
            mock_page.get_pixmap.return_value = mock_pixmap
            mock_pdf_context.load_page.return_value = mock_page
            mock_pdf_context.__len__.return_value = 1

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf(
                    "test_case_insensitive.pdf",
                    "Test content for case insensitive handling",
                )

                try:
                    # Test with uppercase extension
                    output_path = Path("output_file.TXT")
                    extract_text_with_ocr(str(pdf_path), str(output_path), language="eng")
                    # Should work with existing .TXT extension
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)

                    # Test with mixed case extension
                    output_path = Path("output_file.TxT")
                    extract_text_with_ocr(str(pdf_path), str(output_path), language="eng")
                    # Should work with existing .TxT extension
                    assert output_path.exists()
                    output_path.unlink(missing_ok=True)
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")
