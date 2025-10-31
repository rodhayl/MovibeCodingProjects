"""Main responsive application for PDFUtils.

This module provides the main entry point for the responsive PDFUtils application,
integrating all tabs and the responsive UI components.
"""

from __future__ import annotations

import logging
import sys
import tkinter as tk
from tkinter import ttk

try:
    import ttkbootstrap as tb

    _HAVE_TTKBOOTSTRAP = True
except ModuleNotFoundError:
    _HAVE_TTKBOOTSTRAP = False

from .responsive_app import ResponsiveApp
from .tabs import (
    AboutTab,
    BarcodeTab,
    CompressTab,
    ExtractTab,
    HandwritingOcrTab,
    MergeTab,
    OcrTab,
    SplitTab,
    TableExtractionTab,
)
from .utils import (
    configure_logging,
    set_dpi_awareness_windows,
)

logger = logging.getLogger(__name__)


class PDFUtilsApp(ResponsiveApp):
    """Main PDFUtils application with all tabs."""

    def __init__(self, master: tk.Tk):
        """Initialize PDFUtils application.

        Args:
            master: Tk root window
        """
        super().__init__(master)

        # Set window title
        master.title("PDF Utilities - Responsive")

        # Create all tabs
        self._create_tabs()

        # Finalize setup
        self.finalize_setup()

    def _create_tabs(self):
        """Create and add all tabs to the application."""
        # Define tab configurations
        tab_configs = [
            ("merge", "Merge", MergeTab),
            ("split", "Split", SplitTab),
            ("compress", "Compress", CompressTab),
            ("extract", "Extract", ExtractTab),
            ("ocr", "OCR", OcrTab),
            ("table", "Table Extraction", TableExtractionTab),
            ("barcode", "Barcode/QR", BarcodeTab),
            ("handwriting", "Handwriting OCR", HandwritingOcrTab),
            ("about", "About", AboutTab),
        ]

        # Create tabs immediately (no lazy loading for simplicity)
        for tab_id, tab_title, tab_class in tab_configs:
            try:
                tab_frame = tab_class(self.notebook, self)
            except Exception:
                # Fallback to empty frame if tab fails to construct
                tab_frame = ttk.Frame(self.notebook)
            tab_frame.columnconfigure(0, weight=1)
            tab_frame.rowconfigure(0, weight=1)
            self.add_tab(tab_id, tab_title, tab_frame)
            logger.info(f"Added tab: {tab_title}")


def run_responsive():
    """Run the responsive PDFUtils application."""
    configure_logging()
    logger.info("Starting responsive PDFUtils application")

    try:
        # Improve rendering on Windows
        try:
            set_dpi_awareness_windows()
        except Exception:
            pass

        # Create root window
        if _HAVE_TTKBOOTSTRAP:
            root = tb.Window(themename="flatly")
            logger.info("Using ttkbootstrap theme: flatly")
        else:
            root = tk.Tk()
            logger.info("Using standard ttk theme")

        # Set window properties with better defaults for full width utilization
        root.title("PDF Utilities")
        DEFAULT_W, DEFAULT_H = 1200, 800  # Increased width, reduced height
        root.minsize(1000, 700)  # Increased minimum width

        # Configure root window grid for proper expansion
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Center window on screen with better sizing algorithm
        root.update_idletasks()
        width = max(root.winfo_width(), DEFAULT_W)
        height = max(root.winfo_height(), DEFAULT_H)
        x = max(0, (root.winfo_screenwidth() // 2) - (width // 2))
        y = max(0, (root.winfo_screenheight() // 2) - (height // 2))
        root.geometry(f"{width}x{height}+{x}+{y}")

        # Enable window resizing with proper behavior
        root.resizable(True, True)

        # Create and initialize application
        PDFUtilsApp(root)

        logger.info("Application initialized successfully")
        root.mainloop()

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_responsive()
