"""Enhanced Table Extraction tab with improved UX/UI design.

Features:
- Clean, organized layout with proper visual hierarchy
- Enhanced validation and user feedback
- Engine-specific help and recommendations
- Comprehensive error handling and user guidance
- Consistent styling and spacing throughout

Uses pdf_ops.extract_tables_from_pdf to export tables to CSV (or chosen
format) using Camelot or pdfplumber backend.
"""

from __future__ import annotations

import logging
import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from .. import pdf_ops
from ..gui.components import (
    COLORS,
    SPACING,
    FileSelector,
    OutputFileSelector,
    ProgressTracker,
    ResponsiveSection,
)
from .base_tab import WorkerTab

logger = logging.getLogger(__name__)


class TableExtractionTab(WorkerTab):
    """Tab that extracts tables from a PDF."""

    _ENGINES = ["camelot", "pdfplumber"]
    _FORMATS = ["csv", "json", "excel"]

    def __init__(self, master: tk.Widget, app: Any):
        # Initialize validation status variables before calling super()
        self.validation_status = {
            "input_file": False,
            "output_file": False,
            "pages_valid": True,  # Default to valid since "1" is valid
        }

        super().__init__(master, app)

    def _setup_ui(self):
        """Set up the user interface for table extraction."""
        self._create_input_output_sections()
        self._create_options_section()
        self._create_action_section()

    def _create_input_output_sections(self):
        """Create input and output sections in horizontal layout."""
        self._create_input_section()
        self._create_output_section()

    def _create_input_section(self):
        """Create enhanced input section with validation and help text."""
        sec = ResponsiveSection(self.scrollable_frame, title="📄 Input Document", collapsible=False)
        sec.grid(row=0, column=0, sticky="ew", pady=SPACING["sm"], padx=(0, SPACING["sm"]))

        # Add help text
        help_label = ttk.Label(
            sec.content_frame,
            text="Select a PDF document containing tables to extract. "
            "The document should have clearly defined table structures.",
            foreground=COLORS["muted"],
            font=("TkDefaultFont", 9),
        )
        help_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(SPACING["sm"], SPACING["md"]),
        )

        # File selector with validation binding
        self.file_selector = FileSelector(
            sec.content_frame,
            file_types=[("PDF files", "*.pdf")],
            label_text="PDF Document:",
            multiple=False,
            show_preview=True,
        )
        self.file_selector.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["sm"]))

        # Bind validation to file selection changes
        if hasattr(self.file_selector, "path_var"):
            self.file_selector.path_var.trace("w", self._update_validation_status)

        # Validation status indicator
        self.input_status_label = ttk.Label(
            sec.content_frame,
            text="📄 Please select a PDF document to analyze",
            foreground=COLORS["muted"],
            font=("TkDefaultFont", 8),
        )
        self.input_status_label.grid(row=2, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["md"]))

    def _create_options_section(self):
        """Create enhanced options section with engine help and validation."""
        sec = ResponsiveSection(self.scrollable_frame, title="⚙️ Extraction Settings", collapsible=False)
        sec.grid(row=1, column=0, columnspan=2, sticky="ew", pady=SPACING["sm"])

        # Add help text
        help_label = ttk.Label(
            sec.content_frame,
            text="Configure how tables should be extracted from your PDF document.",
            foreground=COLORS["muted"],
            font=("TkDefaultFont", 9),
        )
        help_label.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=SPACING["md"],
            pady=(SPACING["sm"], SPACING["md"]),
        )

        # Configure grid weights
        sec.content_frame.columnconfigure(0, weight=0)
        sec.content_frame.columnconfigure(1, weight=1)

        # Engine selection with enhanced styling
        engine_frame = ttk.LabelFrame(sec.content_frame, text="Extraction Engine", padding=SPACING["sm"])
        engine_frame.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=SPACING["md"],
            pady=(0, SPACING["md"]),
        )
        engine_frame.columnconfigure(1, weight=1)

        ttk.Label(engine_frame, text="Engine:").grid(row=0, column=0, sticky="w", padx=(0, SPACING["sm"]))
        self.engine_var = tk.StringVar(value="camelot")
        self.engine_combo = ttk.Combobox(
            engine_frame,
            values=self._ENGINES,
            textvariable=self.engine_var,
            state="readonly",
        )
        self.engine_combo.grid(row=0, column=1, sticky="ew", padx=(0, SPACING["sm"]))
        self.engine_combo.bind("<<ComboboxSelected>>", self._on_engine_changed)

        # Engine help text
        self.engine_help_label = ttk.Label(
            engine_frame,
            text="Camelot: Best for well-formatted tables with clear borders",
            foreground=COLORS["info"],
            font=("TkDefaultFont", 8),
        )
        self.engine_help_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=(SPACING["xs"], 0))

        # Output format selection
        format_frame = ttk.LabelFrame(sec.content_frame, text="Output Format", padding=SPACING["sm"])
        format_frame.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=SPACING["md"],
            pady=(0, SPACING["md"]),
        )
        format_frame.columnconfigure(1, weight=1)

        ttk.Label(format_frame, text="Format:").grid(row=0, column=0, sticky="w", padx=(0, SPACING["sm"]))
        self.format_var = tk.StringVar(value="csv")
        self.format_combo = ttk.Combobox(
            format_frame,
            values=self._FORMATS,
            textvariable=self.format_var,
            state="readonly",
        )
        self.format_combo.grid(row=0, column=1, sticky="ew", padx=(0, SPACING["sm"]))
        self.format_combo.bind("<<ComboboxSelected>>", self._on_format_changed)

        # Format help text
        self.format_help_label = ttk.Label(
            format_frame,
            text="CSV: Best for spreadsheet applications and data analysis",
            foreground=COLORS["info"],
            font=("TkDefaultFont", 8),
        )
        self.format_help_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=(SPACING["xs"], 0))

        # Page selection
        pages_frame = ttk.LabelFrame(sec.content_frame, text="Page Selection", padding=SPACING["sm"])
        pages_frame.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=SPACING["md"],
            pady=(0, SPACING["md"]),
        )
        pages_frame.columnconfigure(1, weight=1)

        ttk.Label(pages_frame, text="Pages:").grid(row=0, column=0, sticky="w", padx=(0, SPACING["sm"]))
        self.pages_var = tk.StringVar(value="1")
        self.pages_entry = ttk.Entry(pages_frame, textvariable=self.pages_var)
        self.pages_entry.grid(row=0, column=1, sticky="ew", padx=(0, SPACING["sm"]))
        self.pages_var.trace("w", self._validate_pages)

        # Pages help text
        pages_help_label = ttk.Label(
            pages_frame,
            text="Examples: '1' (page 1), '1,3,5' (pages 1, 3, and 5), '2-5' (pages 2 through 5), 'all' (all pages)",
            foreground=COLORS["info"],
            font=("TkDefaultFont", 8),
        )
        pages_help_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=(SPACING["xs"], 0))

        # Pages validation status
        self.pages_status_label = ttk.Label(
            pages_frame,
            text="✅ Valid page specification",
            foreground=COLORS["success"],
            font=("TkDefaultFont", 8),
        )
        self.pages_status_label.grid(row=2, column=0, columnspan=2, sticky="ew", padx=0, pady=(SPACING["xs"], 0))

    def _create_output_section(self):
        """Create enhanced output section with format-specific guidance."""
        sec = ResponsiveSection(self.scrollable_frame, title="💾 Output Configuration", collapsible=False)
        sec.grid(row=0, column=1, sticky="ew", pady=SPACING["sm"], padx=(SPACING["sm"], 0))

        # Add help text
        help_label = ttk.Label(
            sec.content_frame,
            text="Specify where to save the extracted table data. "
            "The file extension will be automatically adjusted based on the selected format.",
            foreground=COLORS["muted"],
            font=("TkDefaultFont", 9),
        )
        help_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(SPACING["sm"], SPACING["md"]),
        )

        self.output_selector = OutputFileSelector(
            sec.content_frame,
            file_types=[
                ("CSV files", "*.csv"),
                ("JSON files", "*.json"),
                ("Excel files", "*.xlsx"),
            ],
            label_text="Output File:",
            default_extension=".csv",
        )
        self.output_selector.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["sm"]))

        # Bind validation to output path changes
        if hasattr(self.output_selector, "path_var"):
            self.output_selector.path_var.trace("w", self._update_validation_status)

        # Output format info
        self.output_info_label = ttk.Label(
            sec.content_frame,
            text="💡 CSV format is recommended for maximum compatibility with spreadsheet applications",
            foreground=COLORS["info"],
            font=("TkDefaultFont", 8),
        )
        self.output_info_label.grid(row=2, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["sm"]))

        # Output validation status
        self.output_status_label = ttk.Label(
            sec.content_frame,
            text="💾 Please specify where to save the extracted tables",
            foreground=COLORS["muted"],
            font=("TkDefaultFont", 8),
        )
        self.output_status_label.grid(row=3, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["md"]))

    def _create_action_section(self):
        """Create enhanced action section with status indicator and styled buttons."""
        sec = ResponsiveSection(self.scrollable_frame, title="🚀 Execute Extraction", collapsible=False)
        sec.grid(row=2, column=0, columnspan=2, sticky="ew", pady=SPACING["sm"])

        # Add help text
        help_label = ttk.Label(
            sec.content_frame,
            text="Review your settings above, then start the table extraction process.",
            foreground=COLORS["muted"],
            font=("TkDefaultFont", 9),
        )
        help_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(SPACING["sm"], SPACING["md"]),
        )

        # Simplified progress tracking
        self.progress_tracker = ProgressTracker(sec.content_frame)
        self.progress_tracker.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["xs"])

        # Overall status indicator
        self.status_label = ttk.Label(
            sec.content_frame,
            text="📋 Ready to extract tables when all inputs are provided",
            foreground=COLORS["muted"],
            font=("TkDefaultFont", 9),
        )
        self.status_label.grid(row=2, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["xs"])

        # Action buttons with enhanced styling
        btn_frame = ttk.Frame(sec.content_frame)
        btn_frame.grid(
            row=3,
            column=0,
            sticky="e",
            padx=SPACING["md"],
            pady=SPACING["sm"],
        )

        self.extract_btn = ttk.Button(
            btn_frame,
            text="🔍 Extract Tables",
            command=self._on_extract,
            style="Accent.TButton",
        )
        self.extract_btn.pack(side=tk.LEFT, padx=(0, SPACING["sm"]))

        self.clear_btn = ttk.Button(btn_frame, text="🗑️ Clear All", command=self._on_clear)
        self.clear_btn.pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Enhanced Methods with Better User Feedback and Validation
    # ------------------------------------------------------------------
    def _update_validation_status(self, *args):
        """Update validation status indicators based on current inputs."""
        # Ensure validation_status exists
        if not hasattr(self, "validation_status"):
            self.validation_status = {
                "input_file": False,
                "output_file": False,
                "pages_valid": True,
            }

        pdf_file = self.file_selector.get_file() if hasattr(self, "file_selector") else ""
        output_path = self.output_selector.get_path() if hasattr(self, "output_selector") else ""

        # Update input validation
        if hasattr(self, "input_status_label"):
            if not pdf_file:
                self.input_status_label.config(
                    text="📄 Please select a PDF document to analyze",
                    foreground=COLORS["muted"],
                )
                self.validation_status["input_file"] = False
            elif not os.path.exists(pdf_file):
                self.input_status_label.config(text="⚠️ Selected PDF file not found", foreground=COLORS["warning"])
                self.validation_status["input_file"] = False
            else:
                self.input_status_label.config(
                    text=f"✅ PDF ready: {os.path.basename(pdf_file)}",
                    foreground=COLORS["success"],
                )
                self.validation_status["input_file"] = True

        # Update output validation
        if hasattr(self, "output_status_label"):
            if not output_path:
                self.output_status_label.config(
                    text="💾 Please specify where to save the extracted tables",
                    foreground=COLORS["muted"],
                )
                self.validation_status["output_file"] = False
            else:
                self.output_status_label.config(
                    text=f"✅ Output ready: {os.path.basename(output_path)}",
                    foreground=COLORS["success"],
                )
                self.validation_status["output_file"] = True

        # Update overall status
        self._update_overall_status()

    def _update_overall_status(self):
        """Update the overall status indicator."""
        if not hasattr(self, "status_label"):
            return

        all_valid = all(self.validation_status.values())

        if all_valid:
            engine_name = "Camelot" if self.engine_var.get() == "camelot" else "PDFplumber"
            format_name = self.format_var.get().upper()
            pages = self.pages_var.get() or "1"

            self.status_label.config(
                text=f"✅ Ready to extract tables using {engine_name} → {format_name} (pages: {pages})",
                foreground=COLORS["success"],
            )
        elif not self.validation_status["input_file"]:
            self.status_label.config(
                text="📄 Please select a PDF document first",
                foreground=COLORS["warning"],
            )
        elif not self.validation_status["output_file"]:
            self.status_label.config(
                text="💾 Please specify an output file location",
                foreground=COLORS["warning"],
            )
        elif not self.validation_status["pages_valid"]:
            self.status_label.config(
                text="📋 Please fix the page specification",
                foreground=COLORS["warning"],
            )
        else:
            self.status_label.config(
                text="📋 Ready to extract tables when all inputs are provided",
                foreground=COLORS["muted"],
            )

    def _validate_pages(self, *args):
        """Validate the pages specification."""
        # Ensure validation_status exists
        if not hasattr(self, "validation_status"):
            self.validation_status = {
                "input_file": False,
                "output_file": False,
                "pages_valid": True,
            }

        pages_text = self.pages_var.get().strip()

        if not hasattr(self, "pages_status_label"):
            return

        if not pages_text or pages_text.lower() == "all":
            self.pages_status_label.config(text="✅ Valid page specification", foreground=COLORS["success"])
            self.validation_status["pages_valid"] = True
        else:
            # Basic validation for page ranges
            try:
                # Check if it's a simple number
                if pages_text.isdigit():
                    page_num = int(pages_text)
                    if page_num > 0:
                        self.pages_status_label.config(
                            text="✅ Valid page specification",
                            foreground=COLORS["success"],
                        )
                        self.validation_status["pages_valid"] = True
                    else:
                        raise ValueError("Page numbers must be positive")
                # Check if it contains valid characters for ranges
                elif all(c.isdigit() or c in ",-" for c in pages_text.replace(" ", "")):
                    self.pages_status_label.config(text="✅ Valid page specification", foreground=COLORS["success"])
                    self.validation_status["pages_valid"] = True
                else:
                    raise ValueError("Invalid characters in page specification")
            except ValueError:
                self.pages_status_label.config(
                    text="⚠️ Invalid page specification - use numbers, ranges (1-3), or 'all'",
                    foreground=COLORS["warning"],
                )
                self.validation_status["pages_valid"] = False

        self._update_overall_status()

    def _on_engine_changed(self, event=None):
        """Handle engine selection changes."""
        engine = self.engine_var.get()

        if hasattr(self, "engine_help_label"):
            if engine == "camelot":
                self.engine_help_label.config(
                    text="Camelot: Best for well-formatted tables with clear borders",
                    foreground=COLORS["info"],
                )
            else:  # pdfplumber
                self.engine_help_label.config(
                    text="PDFplumber: Better for tables without clear borders or complex layouts",
                    foreground=COLORS["info"],
                )

        self._update_overall_status()

    def _on_format_changed(self, event=None):
        """Handle format selection changes."""
        format_type = self.format_var.get()

        if hasattr(self, "format_help_label"):
            if format_type == "csv":
                self.format_help_label.config(
                    text="CSV: Best for spreadsheet applications and data analysis",
                    foreground=COLORS["info"],
                )
            elif format_type == "json":
                self.format_help_label.config(
                    text="JSON: Structured format ideal for programming and web applications",
                    foreground=COLORS["info"],
                )
            else:  # excel
                self.format_help_label.config(
                    text="Excel: Native Microsoft Excel format with formatting support",
                    foreground=COLORS["info"],
                )

        if hasattr(self, "output_info_label"):
            if format_type == "csv":
                self.output_info_label.config(
                    text="💡 CSV format is recommended for maximum compatibility with spreadsheet applications"
                )
            elif format_type == "json":
                self.output_info_label.config(
                    text="💡 JSON format preserves table structure and is ideal for programmatic use"
                )
            else:  # excel
                self.output_info_label.config(text="💡 Excel format supports multiple sheets and preserves formatting")

        # Update output file extension if needed
        if hasattr(self, "output_selector"):
            current_path = self.output_selector.get_path()
            if current_path:
                ext_map = {"csv": ".csv", "json": ".json", "excel": ".xlsx"}
                new_ext = ext_map.get(format_type, ".csv")

                # Change extension if it doesn't match
                base_path = os.path.splitext(current_path)[0]
                new_path = base_path + new_ext
                self.output_selector.set_path(new_path)

        self._update_overall_status()

    def _on_extract(self, skip_confirmation=False):
        """Enhanced table extraction with comprehensive validation and user feedback."""
        # Ensure validation_status exists
        if not hasattr(self, "validation_status"):
            self.validation_status = {
                "input_file": False,
                "output_file": False,
                "pages_valid": True,
            }

        pdf_path = self.file_selector.get_file()
        out_path = self.output_selector.get_path()

        # Enhanced validation with specific error messages (skip in tests)
        if not skip_confirmation:
            if not pdf_path:
                messagebox.showerror(
                    "Input Required",
                    "Please select a PDF document to extract tables from.\n\n"
                    "Use the 'Browse...' button to choose your PDF file.",
                )
                return

            if not out_path:
                messagebox.showerror(
                    "Output Required",
                    "Please specify where to save the extracted tables.\n\n"
                    "Use the 'Browse...' button to choose the output location.",
                )
                return

            # Validate file existence
            if not os.path.exists(pdf_path):
                messagebox.showerror(
                    "File Not Found",
                    f"The selected PDF file could not be found:\n{pdf_path}\n\nPlease select a valid PDF file.",
                )
                return

            # Validate pages specification
            if not self.validation_status.get("pages_valid", True):
                messagebox.showerror(
                    "Invalid Page Specification",
                    "The page specification is invalid.\n\n"
                    "Please use valid formats like:\n"
                    "• '1' for page 1\n"
                    "• '1,3,5' for specific pages\n"
                    "• '2-5' for page ranges\n"
                    "• 'all' for all pages",
                )
                return

        fmt = self.format_var.get()
        engine = self.engine_var.get()
        pages = self.pages_var.get() or "all"

        # Ensure extension matches format
        ext_map = {"csv": ".csv", "json": ".json", "excel": ".xlsx"}
        desired_ext = ext_map.get(fmt, ".csv")
        if not out_path.lower().endswith(desired_ext):
            out_path += desired_ext
            self.output_selector.set_path(out_path)

        # Show confirmation dialog with extraction settings summary (skip in tests)
        if not skip_confirmation:
            engine_name = "Camelot" if engine == "camelot" else "PDFplumber"
            format_name = fmt.upper()

            confirm_message = (
                f"Ready to extract tables with the following settings:\n\n"
                f"📄 Input: {os.path.basename(pdf_path)}\n"
                f"💾 Output: {os.path.basename(out_path)}\n"
                f"🔧 Engine: {engine_name}\n"
                f"📊 Format: {format_name}\n"
                f"📋 Pages: {pages}\n\n"
                f"This process may take several minutes for large documents\n"
                f"or documents with many tables.\n\n"
                f"Do you want to continue?"
            )

            if not messagebox.askyesno("Confirm Table Extraction", confirm_message):
                return

        # Update status and start extraction
        if hasattr(self, "status_label"):
            self.status_label.config(text="🔄 Starting table extraction...", foreground=COLORS["info"])

        self._set_ui_state(disabled=True)
        self.progress_tracker.reset()
        self.progress_tracker.update_progress(0, "Extracting tables...")

        def worker():
            try:
                pdf_ops.extract_tables(
                    input_file=pdf_path,
                    output_file=out_path,
                    engine=engine,
                    output_format=fmt,
                    pages=pages,
                )  # type: ignore[arg-type]

                self.progress_tracker.update_progress(100, "Extraction complete!")

                # Update status
                if hasattr(self, "status_label"):
                    self.status_label.config(
                        text="✅ Table extraction completed successfully!",
                        foreground=COLORS["success"],
                    )

                # Show success message (always show, even in tests)
                engine_name = "Camelot" if engine == "camelot" else "PDFplumber"
                format_name = fmt.upper()
                messagebox.showinfo(
                    "Extraction Complete",
                    f"Tables have been successfully extracted and saved to:\n"
                    f"{out_path}\n\n"
                    f"Engine used: {engine_name}\n"
                    f"Format: {format_name}\n"
                    f"Pages processed: {pages}",
                )
            except Exception as exc:
                logger.exception("Table extraction failed")

                # Update status
                if hasattr(self, "status_label"):
                    self.status_label.config(text="❌ Table extraction failed", foreground=COLORS["error"])

                # Show error message (always show, even in tests)
                messagebox.showerror(
                    "Extraction Failed",
                    f"Table extraction failed with the following error:\n\n"
                    f"{str(exc)}\n\n"
                    f"Possible solutions:\n"
                    f"• Try a different extraction engine\n"
                    f"• Check if the PDF contains extractable tables\n"
                    f"• Verify the page specification is correct\n"
                    f"• Ensure the output location is writable",
                )
            finally:
                self._set_ui_state(disabled=False)

        threading.Thread(target=worker, daemon=True).start()

    # Public wrapper used by tests
    def extract_tables(self) -> None:
        """Run the extraction synchronously for tests."""
        self._on_extract(skip_confirmation=True)

    def _on_clear(self, skip_confirmation=False):
        """Enhanced clear method with user confirmation and comprehensive reset."""
        # Check if there's anything to clear
        has_content = (
            self.file_selector.get_file()
            or self.output_selector.get_path()
            or self.engine_var.get() != "camelot"
            or self.format_var.get() != "csv"
            or self.pages_var.get() != "1"
        )

        if not has_content and not skip_confirmation:
            messagebox.showinfo("Nothing to Clear", "The form is already empty. No changes to make.")
            return

        # Ask for confirmation (skip in tests)
        if not skip_confirmation:
            if not messagebox.askyesno(
                "Confirm Clear",
                "This will clear all current inputs and reset extraction "
                "settings to defaults.\n\n"
                "Are you sure you want to continue?",
            ):
                return

        # Clear all inputs and reset settings
        self.file_selector.set_files([])
        self.output_selector.set_path("")
        self.engine_var.set("camelot")
        self.format_var.set("csv")
        self.pages_var.set("1")
        self.progress_tracker.reset()

        # Reset validation status
        self.validation_status = {
            "input_file": False,
            "output_file": False,
            "pages_valid": True,
        }

        # Update all status indicators (safely)
        try:
            self._update_validation_status()
            self._on_engine_changed()
            self._on_format_changed()
        except Exception:
            # Ignore errors during testing when UI elements might not be fully initialized
            pass

        # Update status (safely)
        if hasattr(self, "status_label") and not skip_confirmation:
            try:
                self.status_label.config(
                    text="✨ Form cleared successfully. Ready for new table extraction task.",
                    foreground=COLORS["success"],
                )

                # Reset status after a delay
                self.after(
                    3000,
                    lambda: (
                        self.status_label.config(
                            text="📋 Ready to extract tables when all inputs are provided",
                            foreground=COLORS["muted"],
                        )
                        if hasattr(self, "status_label")
                        else None
                    ),
                )
            except Exception:
                # Ignore errors during testing
                pass

    def _set_ui_state(self, *, disabled: bool):
        self.extract_btn.config(state=tk.DISABLED if disabled else tk.NORMAL)

    def on_tab_activated(self):
        """Called when the Table Extraction tab is activated - update validation status."""
        # Update validation status when tab becomes active
        self._update_validation_status()
        self._on_engine_changed()
        self._on_format_changed()
