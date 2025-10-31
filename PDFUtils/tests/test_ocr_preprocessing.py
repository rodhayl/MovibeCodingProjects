"""Tests for OCR preprocessing options."""

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


class TestOCRPreprocessing:
    """Test class for OCR preprocessing options."""

    @pytest.mark.timeout(10)
    def test_binarize_preprocessing(self):
        """Test OCR with binarize preprocessing option."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
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

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_binarize.pdf", "Test content for binarize")
                output_path = "output_binarize.txt"

                try:
                    extract_text_with_ocr(
                        str(pdf_path),
                        output_path,
                        language="eng",
                        binarize=True,
                        threshold=128,
                    )
                    # Verify pytesseract was called
                    mock_image_to_string.assert_called_once()
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
                    Path(output_path).unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_resize_preprocessing(self):
        """Test OCR with resize preprocessing option."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
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

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_resize.pdf", "Test content for resize")
                output_path = "output_resize.txt"

                try:
                    extract_text_with_ocr(str(pdf_path), output_path, language="eng", resize_factor=1.5)
                    # Verify pytesseract was called
                    mock_image_to_string.assert_called_once()
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
                    Path(output_path).unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_deskew_preprocessing(self):
        """Test OCR with deskew preprocessing option."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
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

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_deskew.pdf", "Test content for deskew")
                output_path = "output_deskew.txt"

                try:
                    extract_text_with_ocr(str(pdf_path), output_path, language="eng", deskew=True)
                    # Verify pytesseract was called
                    mock_image_to_string.assert_called_once()
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
                    Path(output_path).unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_denoise_preprocessing(self):
        """Test OCR with denoise preprocessing option."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
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

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_denoise.pdf", "Test content for denoise")
                output_path = "output_denoise.txt"

                try:
                    extract_text_with_ocr(str(pdf_path), output_path, language="eng", denoise=True)
                    # Verify pytesseract was called
                    mock_image_to_string.assert_called_once()
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
                    Path(output_path).unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_contrast_preprocessing(self):
        """Test OCR with contrast preprocessing option."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
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

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_contrast.pdf", "Test content for contrast")
                output_path = "output_contrast.txt"

                try:
                    extract_text_with_ocr(str(pdf_path), output_path, language="eng", contrast_factor=1.5)
                    # Verify pytesseract was called
                    mock_image_to_string.assert_called_once()
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
                    Path(output_path).unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_brightness_preprocessing(self):
        """Test OCR with brightness preprocessing option."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
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

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_brightness.pdf", "Test content for brightness")
                output_path = "output_brightness.txt"

                try:
                    extract_text_with_ocr(
                        str(pdf_path),
                        output_path,
                        language="eng",
                        brightness_factor=1.5,
                    )
                    # Verify pytesseract was called
                    mock_image_to_string.assert_called_once()
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
                    Path(output_path).unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_sharpen_preprocessing(self):
        """Test OCR with sharpen preprocessing option."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
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

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_sharpen.pdf", "Test content for sharpen")
                output_path = "output_sharpen.txt"

                try:
                    extract_text_with_ocr(str(pdf_path), output_path, language="eng", sharpen=True)
                    # Verify pytesseract was called
                    mock_image_to_string.assert_called_once()
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
                    Path(output_path).unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_blur_preprocessing(self):
        """Test OCR with blur preprocessing option."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
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

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_blur.pdf", "Test content for blur")
                output_path = "output_blur.txt"

                try:
                    extract_text_with_ocr(str(pdf_path), output_path, language="eng", blur=1.0)
                    # Verify pytesseract was called
                    mock_image_to_string.assert_called_once()
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
                    Path(output_path).unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_morphological_preprocessing(self):
        """Test OCR with morphological preprocessing options."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
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

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_morph.pdf", "Test content for morphological")
                output_path = "output_morph.txt"

                try:
                    extract_text_with_ocr(
                        str(pdf_path),
                        output_path,
                        language="eng",
                        morph_op="open",
                        morph_kernel=3,
                    )
                    # Verify pytesseract was called
                    mock_image_to_string.assert_called_once()
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
                    Path(output_path).unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_combined_preprocessing(self):
        """Test OCR with multiple preprocessing options combined."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
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

            # Mock pytesseract to return sample text
            mock_image_to_string.return_value = "Sample text"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_combined.pdf", "Test content for combined preprocessing")
                output_path = "output_combined.txt"

                try:
                    extract_text_with_ocr(
                        str(pdf_path),
                        output_path,
                        language="eng",
                        binarize=True,
                        threshold=128,
                        resize_factor=1.2,
                        deskew=True,
                        denoise=True,
                        contrast_factor=1.2,
                        brightness_factor=1.1,
                        sharpen=True,
                        blur=0.5,
                    )
                    # Verify pytesseract was called
                    mock_image_to_string.assert_called_once()
                finally:
                    # Clean up test files
                    pdf_path.unlink(missing_ok=True)
                    Path(output_path).unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")

    @pytest.mark.timeout(10)
    def test_preprocessing_with_different_output_formats(self):
        """Test preprocessing with different output formats."""
        with (
            patch("pdfutils.pdf_ops._HAVE_PYMUPDF", True),
            patch("pdfutils.pdf_ops._HAVE_TESSERACT", True),
            patch("pdfutils.pdf_ops._TESSERACT_INSTALLED", True),
            patch("pdfutils.pdf_ops.pdf_document") as mock_pdf_doc,
            patch("pdfutils.pdf_ops.image_document") as mock_img_doc,
            patch("pdfutils.pdf_ops.pytesseract.image_to_string") as mock_image_to_string,
            patch("pdfutils.pdf_ops.pytesseract.image_to_pdf_or_hocr") as mock_image_to_hocr,
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
            mock_image_to_hocr.return_value = b"<hocr>Sample text</hocr>"

            try:
                from pdfutils.pdf_ops import extract_text_with_ocr

                # Create a proper test PDF file instead of using empty temporary file
                pdf_path = create_test_pdf("test_formats.pdf", "Test content for formats")

                # Test text format
                output_path_text = "output_text.txt"
                try:
                    extract_text_with_ocr(
                        str(pdf_path),
                        output_path_text,
                        language="eng",
                        output_format="text",
                        binarize=True,
                    )
                    # Verify pytesseract was called
                    mock_image_to_string.assert_called_once()
                finally:
                    Path(output_path_text).unlink(missing_ok=True)

                # Reset the mock for the next call
                mock_image_to_string.reset_mock()

                # Test hOCR format
                output_path_hocr = "output_hocr.html"
                try:
                    extract_text_with_ocr(
                        str(pdf_path),
                        output_path_hocr,
                        language="eng",
                        output_format="hocr",
                        binarize=True,
                    )
                    # Verify pytesseract was called
                    mock_image_to_hocr.assert_called_once()
                finally:
                    Path(output_path_hocr).unlink(missing_ok=True)

                # Clean up test PDF
                pdf_path.unlink(missing_ok=True)
            except ImportError:
                pytest.skip("OCR functions not available")
