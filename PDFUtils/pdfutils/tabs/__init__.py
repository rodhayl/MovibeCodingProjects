"""Tab implementations for PDFUtils.

This package contains the implementations of the various tabs in the PDFUtils
application using the responsive UI components.
"""

from .about_tab import AboutTab
from .barcode_tab import BarcodeTab
from .compress_tab import CompressTab
from .extract_tab import ExtractTab
from .handwriting_ocr_tab import HandwritingOcrTab
from .merge_tab import MergeTab
from .ocr_tab import OcrTab
from .split_tab import SplitTab
from .table_extraction_tab import TableExtractionTab

__all__ = [
    "MergeTab",
    "SplitTab",
    "CompressTab",
    "ExtractTab",
    "OcrTab",
    "TableExtractionTab",
    "BarcodeTab",
    "AboutTab",
    "HandwritingOcrTab",
]
