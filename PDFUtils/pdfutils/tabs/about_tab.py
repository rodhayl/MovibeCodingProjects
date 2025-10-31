"""Enhanced About tab with modern design and comprehensive information.

Features:
- Modern, visually appealing layout with proper hierarchy
- Comprehensive system and version information
- Enhanced dependency information with status indicators
- Interactive links with better styling
- Responsive design with consistent spacing
- Professional presentation of application details

Displays project information, version, dependencies, and links.
"""

from __future__ import annotations

import importlib.util
import platform
import sys
import tkinter as tk
import webbrowser
from tkinter import ttk
from typing import Any

from ..gui.components import COLORS, SPACING, ResponsiveSection, TabContentFrame


class AboutTab(TabContentFrame):
    """Enhanced tab that displays comprehensive information about PDFUtils.

    Features:
    - Modern visual design with proper hierarchy
    - System and version information
    - Dependency status checking
    - Interactive links with enhanced styling
    - Professional information presentation
    """

    def __init__(self, master: tk.Widget, app: Any):
        super().__init__(master)
        self.app = app
        self.app_icon = None

        # Cache system information
        self._system_info = self._get_system_info()
        self._dependency_status = self._check_dependencies()

        self._create_header_section()
        self._create_system_info_section()
        self._create_features_section()
        self._create_dependencies_section()
        self._create_links_section()

    def _get_system_info(self) -> dict:
        """Get comprehensive system information."""
        try:
            return {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "python_implementation": platform.python_implementation(),
                "platform": platform.platform(),
                "system": platform.system(),
                "machine": platform.machine(),
                "processor": platform.processor() or "Unknown",
                "architecture": platform.architecture()[0],
            }
        except Exception:
            return {
                "python_version": "Unknown",
                "python_implementation": "Unknown",
                "platform": "Unknown",
                "system": "Unknown",
                "machine": "Unknown",
                "processor": "Unknown",
                "architecture": "Unknown",
            }

    def _check_dependencies(self) -> dict:
        """Check status of optional dependencies."""
        dependencies = {
            "PyMuPDF": "fitz",
            "pytesseract": "pytesseract",
            "camelot-py": "camelot",
            "pdfplumber": "pdfplumber",
            "pyzbar": "pyzbar",
            "kraken": "kraken",
            "pandas": "pandas",
            "opencv-python": "cv2",
            "scikit-image": "skimage",
            "Pillow": "PIL",
        }

        status = {}
        for display_name, module_name in dependencies.items():
            try:
                spec = importlib.util.find_spec(module_name)
                if spec is not None:
                    # Try to get version if possible
                    try:
                        module = importlib.import_module(module_name)
                        version = getattr(module, "__version__", "Unknown version")
                        status[display_name] = {"installed": True, "version": version}
                    except Exception:
                        status[display_name] = {"installed": True, "version": "Unknown version"}
                else:
                    status[display_name] = {"installed": False, "version": None}
            except Exception:
                status[display_name] = {"installed": False, "version": None}

        return status

    # ------------------------------------------------------------------
    def open_url(self, url: str) -> None:
        """Open a URL in the default browser."""
        try:
            webbrowser.open(url)
        except Exception:
            pass

    def _create_header_section(self):
        """Create enhanced header section with application branding."""
        sec = ResponsiveSection(self.scrollable_frame, title="📄 PDFUtils - PDF Processing Toolkit", collapsible=False)
        sec.grid(row=0, column=0, sticky="ew", pady=SPACING["sm"])
        sec.content_frame.columnconfigure(0, weight=1)

        # Application header with icon and title
        header_frame = ttk.Frame(sec.content_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=(SPACING["sm"], SPACING["xs"]))
        header_frame.columnconfigure(1, weight=1)

        # App icon placeholder (could be enhanced with actual icon)
        icon_label = ttk.Label(header_frame, text="📄", font=("TkDefaultFont", 24))
        icon_label.grid(row=0, column=0, padx=(0, SPACING["md"]), sticky="w")

        # Title and version info
        title_frame = ttk.Frame(header_frame)
        title_frame.grid(row=0, column=1, sticky="ew")

        title_label = ttk.Label(title_frame, text="PDFUtils", font=("TkDefaultFont", 16, "bold"))
        title_label.pack(anchor="w")

        subtitle_label = ttk.Label(
            title_frame,
            text="Professional PDF Processing Toolkit",
            font=("TkDefaultFont", 10),
            foreground=COLORS.get("text_secondary", "gray"),
        )
        subtitle_label.pack(anchor="w")

        version_label = ttk.Label(
            title_frame,
            text="Version 1.0.0 • Built with Python",
            font=("TkDefaultFont", 9),
            foreground=COLORS.get("text_secondary", "gray"),
        )
        version_label.pack(anchor="w", pady=(SPACING["xs"], 0))

        # Description with better formatting
        desc_frame = ttk.Frame(sec.content_frame)
        desc_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["sm"]))

        description = (
            "A comprehensive PDF processing toolkit featuring a modern, responsive GUI. "
            "PDFUtils provides professional-grade PDF operations with an intuitive interface, "
            "real-time progress tracking, and extensive format support."
        )

        desc_label = ttk.Label(
            desc_frame,
            text=description,
            wraplength=500,
            justify=tk.LEFT,
            foreground=COLORS.get("text_primary", "black"),
        )
        desc_label.pack(anchor="w")

        # Key highlights
        highlights_frame = ttk.Frame(sec.content_frame)
        highlights_frame.grid(row=2, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["sm"]))

        highlights = [
            "🚀 Fast and efficient PDF processing",
            "🎨 Modern, responsive user interface",
            "📊 Real-time progress tracking",
            "🔧 Extensive customization options",
        ]

        for i, highlight in enumerate(highlights):
            highlight_label = ttk.Label(
                highlights_frame, text=highlight, foreground=COLORS.get("text_secondary", "gray")
            )
            highlight_label.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, SPACING["lg"]), pady=SPACING["xs"])

    def _create_system_info_section(self):
        """Create system information section with detailed environment info."""
        sec = ResponsiveSection(self.scrollable_frame, title="💻 System Information", collapsible=False)
        sec.grid(row=1, column=0, sticky="ew", pady=SPACING["sm"])
        sec.content_frame.columnconfigure(1, weight=1)

        # System info grid
        info_items = [
            ("Python Version:", self._system_info["python_version"]),
            ("Python Implementation:", self._system_info["python_implementation"]),
            ("Operating System:", self._system_info["system"]),
            ("Platform:", self._system_info["platform"]),
            ("Architecture:", self._system_info["architecture"]),
            ("Machine Type:", self._system_info["machine"]),
            ("Processor:", self._system_info["processor"]),
        ]

        for i, (label, value) in enumerate(info_items):
            # Label
            label_widget = ttk.Label(sec.content_frame, text=label, font=("TkDefaultFont", 9, "bold"))
            label_widget.grid(row=i, column=0, sticky="w", padx=SPACING["md"], pady=SPACING["xs"])

            # Value
            value_widget = ttk.Label(sec.content_frame, text=value, foreground=COLORS.get("text_secondary", "gray"))
            value_widget.grid(row=i, column=1, sticky="w", padx=(SPACING["sm"], SPACING["md"]), pady=SPACING["xs"])

    def _create_features_section(self):
        """Create enhanced features section with categorized functionality."""
        sec = ResponsiveSection(self.scrollable_frame, title="🚀 Key Features", collapsible=False)
        sec.grid(row=2, column=0, sticky="ew", pady=SPACING["sm"])
        sec.content_frame.columnconfigure(0, weight=1)
        sec.content_frame.columnconfigure(1, weight=1)

        # Feature categories with better organization
        feature_categories = {
            "Core PDF Operations": [
                ("📄", "PDF Merge", "Combine multiple PDFs in order with bookmarks"),
                ("✂️", "PDF Split", "Split into individual pages or page ranges"),
                ("🗜️", "PDF Compression", "Reduce file size with quality presets"),
                ("📑", "Page Extraction", "Extract specific page ranges efficiently"),
            ],
            "Advanced Processing": [
                ("🔍", "OCR Text Extraction", "Extract text from scanned documents"),
                ("📊", "Table Extraction", "Extract tables to CSV/JSON/Excel formats"),
                ("📱", "Barcode Detection", "Find and decode barcodes/QR codes"),
                ("✍️", "Handwriting OCR", "Recognize handwritten text with Kraken"),
            ],
            "User Experience": [
                ("⚡", "Responsive GUI", "Modern, responsive interface design"),
                ("📈", "Progress Tracking", "Real-time progress for all operations"),
                ("🧵", "Threaded Operations", "Non-blocking UI during processing"),
                ("🔎", "Searchable PDFs", "Create searchable PDFs from images"),
            ],
        }

        row = 0
        for category, features in feature_categories.items():
            # Category header
            category_label = ttk.Label(
                sec.content_frame,
                text=category,
                font=("TkDefaultFont", 10, "bold"),
                foreground=COLORS.get("primary", "blue"),
            )
            category_label.grid(
                row=row,
                column=0,
                columnspan=2,
                sticky="w",
                padx=SPACING["md"],
                pady=(SPACING["md"] if row > 0 else SPACING["sm"], SPACING["xs"]),
            )
            row += 1

            # Features in this category
            for i, (icon, title, description) in enumerate(features):
                # Create feature frame
                feature_frame = ttk.Frame(sec.content_frame)
                feature_frame.grid(
                    row=row,
                    column=i % 2,
                    sticky="ew",
                    padx=(SPACING["md"], SPACING["sm"] if i % 2 == 0 else SPACING["md"]),
                    pady=SPACING["xs"],
                )
                feature_frame.columnconfigure(1, weight=1)

                # Icon
                icon_label = ttk.Label(feature_frame, text=icon, font=("TkDefaultFont", 12))
                icon_label.grid(row=0, column=0, padx=(0, SPACING["sm"]), sticky="nw")

                # Title and description
                text_frame = ttk.Frame(feature_frame)
                text_frame.grid(row=0, column=1, sticky="ew")

                title_label = ttk.Label(text_frame, text=title, font=("TkDefaultFont", 9, "bold"))
                title_label.pack(anchor="w")

                desc_label = ttk.Label(
                    text_frame,
                    text=description,
                    font=("TkDefaultFont", 8),
                    foreground=COLORS.get("text_secondary", "gray"),
                    wraplength=200,
                )
                desc_label.pack(anchor="w")

                if i % 2 == 1:  # After every two features, move to next row
                    row += 1

            if len(features) % 2 == 1:  # If odd number of features, move to next row
                row += 1

    def _create_dependencies_section(self):
        """Create compact dependencies section with status indicators."""
        sec = ResponsiveSection(self.scrollable_frame, title="📦 Dependencies", collapsible=False)
        sec.grid(row=3, column=0, sticky="ew", pady=SPACING["sm"])
        sec.content_frame.columnconfigure(0, weight=1)
        sec.content_frame.columnconfigure(1, weight=1)
        
        # Core dependencies
        core_frame = ttk.LabelFrame(sec.content_frame, text="Core Dependencies", padding=SPACING["sm"])
        core_frame.grid(row=0, column=0, sticky="ew", padx=(SPACING["md"], SPACING["sm"]), pady=SPACING["sm"])
        
        core_deps = [("pypdf", "✅"), ("tkinter", "✅"), ("Python", "✅")]
        for i, (name, status) in enumerate(core_deps):
            ttk.Label(core_frame, text=f"{status} {name}", font=("TkDefaultFont", 9)).grid(
                row=i, column=0, sticky="w", pady=2)
        
        # Optional dependencies
        optional_frame = ttk.LabelFrame(sec.content_frame, text="Optional Dependencies", padding=SPACING["sm"])
        optional_frame.grid(row=0, column=1, sticky="ew", padx=(SPACING["sm"], SPACING["md"]), pady=SPACING["sm"])
        
        # Check key optional dependencies
        key_deps = ["PyMuPDF", "pytesseract", "pyzbar", "kraken"]
        for i, dep_name in enumerate(key_deps):
            dep_info = self._dependency_status.get(dep_name, {"installed": False})
            status = "✅" if dep_info["installed"] else "❌"
            ttk.Label(optional_frame, text=f"{status} {dep_name}", font=("TkDefaultFont", 9)).grid(
                row=i, column=0, sticky="w", pady=2)

    def _create_links_section(self):
        """Create compact links section spanning both columns."""
        links_frame = ttk.LabelFrame(self.scrollable_frame, text="🔗 Links & Resources", padding=SPACING["md"])
        links_frame.grid(row=4, column=0, sticky="ew", 
                        padx=SPACING["md"], pady=SPACING["md"])
        
        # Configure for 3-column layout
        for i in range(3):
            links_frame.columnconfigure(i, weight=1)
        
        # Essential links only
        links = [
            ("📚", "Documentation", "https://github.com/user/pdfutils/wiki"),
            ("🐛", "Report Issues", "https://github.com/user/pdfutils/issues"),
            ("⭐", "GitHub Repo", "https://github.com/user/pdfutils"),
            ("📄", "PyPDF Docs", "https://pypdf.readthedocs.io/"),
            ("🔧", "Tesseract OCR", "https://tesseract-ocr.github.io/"),
            ("💬", "Discussions", "https://github.com/user/pdfutils/discussions"),
        ]
        
        # Create 3-column grid of links
        for i, (icon, title, url) in enumerate(links):
            row, col = divmod(i, 3)
            
            link_frame = ttk.Frame(links_frame)
            link_frame.grid(row=row, column=col, sticky="ew", padx=SPACING["sm"], pady=2)
            
            # Icon and title as clickable link
            link_label = ttk.Label(link_frame, text=f"{icon} {title}", 
                                  font=("TkDefaultFont", 9), 
                                  foreground=COLORS.get("primary", "blue"),
                                  cursor="hand2")
            link_label.pack(anchor="w")
            link_label.bind("<Button-1>", lambda e, url=url: self.open_url(url))
        
        # Compact footer
        footer_label = ttk.Label(links_frame, 
                               text="© 2024 PDFUtils • Open Source • MIT License",
                               font=("TkDefaultFont", 8),
                               foreground=COLORS.get("text_secondary", "gray"))
        footer_label.grid(row=2, column=0, columnspan=3, pady=(SPACING["md"], 0))



    def on_tab_activated(self):
        """Called when this tab is activated - refresh system information."""
        # Refresh system information in case anything has changed
        try:
            self._system_info = self._get_system_info()
            self._dependency_status = self._check_dependencies()
        except Exception:
            # Don't crash if system info refresh fails
            pass
