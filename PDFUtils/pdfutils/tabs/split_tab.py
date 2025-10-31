"""Enhanced Split tab implementation with improved UX/UI design.

Provides an intuitive interface to select a PDF file and split it using various methods
(single pages, page ranges, bookmarks) with clear visual hierarchy and user feedback.
"""

from __future__ import annotations

import logging
import os
import tkinter as tk
from pathlib import Path
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


class SplitTab(WorkerTab):
    """Tab that splits a PDF into individual pages."""

    def __init__(self, master: tk.Widget, app: Any):
        super().__init__(master, app)

        # Initialize variables first for proper binding
        self.split_method = tk.StringVar(value="single")
        self.page_range = tk.StringVar(value="")
        # alias used in some tests
        self.page_ranges_var = self.page_range
        self.naming_pattern = tk.StringVar(value="page_{page}")
        self.compression_var = tk.BooleanVar(value=False)
        self.compression_level = tk.IntVar(value=0)
        self.password_var = tk.StringVar(value="")

        # Configure main grid for horizontal layout
        self.scrollable_frame.columnconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(1, weight=1)

        # Create UI sections with horizontal layout
        self._create_input_output_sections()
        self._create_options_section()
        self._create_action_section()

    # ------------------------------------------------------------------
    # Enhanced UI Sections with Better Visual Hierarchy
    # ------------------------------------------------------------------
    def _create_input_output_sections(self):
        """Create input and output sections side by side for horizontal layout."""
        # Left side - Input section
        self._create_input_section()
        # Right side - Output section
        self._create_output_section()

    def _create_input_section(self):
        """Create the input section with enhanced visual hierarchy and accessibility."""
        sec = ResponsiveSection(
            self.scrollable_frame,
            title="📄 Select PDF File to Split",
            collapsible=False,
        )
        sec.grid(row=0, column=0, sticky="nsew", pady=(0, SPACING["lg"]), padx=(0, SPACING["md"]))

        # Add descriptive help text
        help_label = ttk.Label(
            sec.content_frame,
            text="Choose a PDF file to split into separate pages or sections.",
            font=("TkDefaultFont", 9),
            foreground=COLORS["gray"],
        )
        help_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(SPACING["sm"], SPACING["md"]),
        )

        # Enhanced file selector with better spacing
        self.file_selector = FileSelector(
            sec.content_frame,
            file_types=[("PDF files", "*.pdf"), ("All files", "*.*")],
            label_text="Source PDF file:",
            multiple=False,
            show_preview=True,
        )
        self.file_selector.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["lg"]))

        # Bind file selection change for validation updates
        if hasattr(self.file_selector, "file_path_var"):
            self.file_selector.file_path_var.trace("w", lambda *args: self._update_validation_status())

    def _create_options_section(self):
        """Create the options section with improved layout and accessibility."""
        sec = ResponsiveSection(self.scrollable_frame, title="⚙️ Split Options", collapsible=False)
        sec.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, SPACING["lg"]))

        # Create a frame for better organization of options
        options_frame = ttk.LabelFrame(sec.content_frame, text="Split Method", padding=SPACING["md"])
        options_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["md"])
        options_frame.columnconfigure(0, weight=1)

        # Split method selection with enhanced descriptions
        method_frame = ttk.Frame(options_frame)
        method_frame.grid(row=0, column=0, sticky="ew", pady=(0, SPACING["md"]))
        method_frame.columnconfigure(1, weight=1)

        ttk.Label(method_frame, text="Split method:").grid(row=0, column=0, sticky="w")

        method_combo = ttk.Combobox(
            method_frame,
            textvariable=self.split_method,
            values=["single", "range", "bookmarks"],
            state="readonly",
            width=15,
        )
        method_combo.grid(row=0, column=1, sticky="w", padx=(SPACING["sm"], 0))
        method_combo.bind("<<ComboboxSelected>>", lambda e: self._on_method_changed())

        # Method descriptions
        method_desc = ttk.Label(
            method_frame,
            text="• single: One file per page • range: Specific pages • bookmarks: Split at bookmarks",
            font=("TkDefaultFont", 8),
            foreground=COLORS["gray"],
        )
        method_desc.grid(row=1, column=0, columnspan=2, sticky="w", pady=(SPACING["xs"], 0))

        # Page range input (initially hidden)
        self.range_frame = ttk.Frame(options_frame)
        self.range_frame.grid(row=1, column=0, sticky="ew", pady=(SPACING["md"], 0))
        self.range_frame.columnconfigure(1, weight=1)

        ttk.Label(self.range_frame, text="Page range:").grid(row=0, column=0, sticky="w")

        range_entry = ttk.Entry(self.range_frame, textvariable=self.page_range, width=20)
        range_entry.grid(row=0, column=1, sticky="w", padx=(SPACING["sm"], 0))
        range_entry.bind("<KeyRelease>", lambda e: self._update_validation_status())

        ttk.Label(
            self.range_frame,
            text="(e.g., 1-3,5,7-9)",
            font=("TkDefaultFont", 8),
            foreground=COLORS["gray"],
        ).grid(row=0, column=2, sticky="w", padx=(SPACING["sm"], 0))

        # Initially hide range frame
        self.range_frame.grid_remove()

        # Advanced options frame
        advanced_frame = ttk.LabelFrame(sec.content_frame, text="Advanced Options", padding=SPACING["md"])
        advanced_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        advanced_frame.columnconfigure(1, weight=1)

        # Naming pattern
        ttk.Label(advanced_frame, text="File naming:").grid(row=0, column=0, sticky="w")
        naming_entry = ttk.Entry(advanced_frame, textvariable=self.naming_pattern, width=25)
        naming_entry.grid(row=0, column=1, sticky="ew", padx=(SPACING["sm"], 0))

        ttk.Label(
            advanced_frame,
            text="Use {page} for page number",
            font=("TkDefaultFont", 8),
            foreground=COLORS["gray"],
        ).grid(
            row=1,
            column=1,
            sticky="w",
            padx=(SPACING["sm"], 0),
            pady=(SPACING["xs"], SPACING["md"]),
        )

        # Compression options
        compression_frame = ttk.Frame(advanced_frame)
        compression_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(SPACING["md"], 0))

        ttk.Checkbutton(
            compression_frame,
            text="Enable compression",
            variable=self.compression_var,
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(compression_frame, text="Level:").grid(
            row=0, column=1, sticky="w", padx=(SPACING["lg"], SPACING["xs"])
        )

        level_combo = ttk.Combobox(
            compression_frame,
            textvariable=self.compression_level,
            values=[0, 1, 2, 3],
            state="readonly",
            width=5,
        )
        level_combo.grid(row=0, column=2, sticky="w")

    def _create_output_section(self):
        """Create the output section with enhanced user guidance."""
        sec = ResponsiveSection(self.scrollable_frame, title="💾 Output Settings", collapsible=False)
        sec.grid(row=0, column=1, sticky="nsew", pady=(0, SPACING["lg"]), padx=(SPACING["md"], 0))

        # Add descriptive help text
        help_label = ttk.Label(
            sec.content_frame,
            text="Choose the destination folder where split PDF files will be saved.",
            font=("TkDefaultFont", 9),
            foreground=COLORS["gray"],
        )
        help_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(SPACING["sm"], SPACING["md"]),
        )

        # Enhanced output selector with better spacing
        self.output_selector = OutputFileSelector(
            sec.content_frame,
            file_types=[("Directory", "*")],
            label_text="Destination folder:",
        )
        self.output_selector.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["lg"]))

        # Bind output path change for validation updates
        if hasattr(self.output_selector, "output_path"):
            self.output_selector.output_path.trace("w", lambda *args: self._update_validation_status())

    def _create_action_section(self):
        """Create the action section with enhanced visual prominence and user feedback."""
        sec = ResponsiveSection(self.scrollable_frame, title="🚀 Execute Split", collapsible=False)
        sec.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, SPACING["xl"]))

        # Simplified progress tracking
        self.progress_tracker = ProgressTracker(sec.content_frame)
        self.progress_tracker.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["sm"])

        # Status indicator for real-time validation feedback
        status_frame = ttk.Frame(sec.content_frame)
        status_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))

        self.status_label = ttk.Label(
            status_frame,
            text="⚠️ Please select a PDF file to split",
            font=("TkDefaultFont", 9),
            foreground=COLORS["warning"],
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        # Enhanced button frame with better styling and spacing
        btn_frame = ttk.Frame(sec.content_frame)
        btn_frame.grid(
            row=2,
            column=0,
            sticky="e",
            padx=SPACING["lg"],
            pady=(SPACING["md"], SPACING["xl"]),
        )

        # Primary action button with enhanced styling
        self.action_button = ttk.Button(
            btn_frame,
            text="🔄 Split PDF",
            command=self._on_split,
            style="Accent.TButton",
        )
        self.action_button.pack(side=tk.LEFT, padx=(0, SPACING["md"]))

        # Backward compatibility alias for tests
        self.split_btn = self.action_button

        # Secondary action button
        ttk.Button(btn_frame, text="🗑️ Clear All", command=self._on_clear).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Enhanced Methods with Better User Feedback and Validation
    # ------------------------------------------------------------------
    def _update_validation_status(self):
        """Update the validation status indicator based on current inputs."""
        pdf_file = self.file_selector.get_file() if hasattr(self, "file_selector") else ""
        output_dir = self.output_selector.get_path() if hasattr(self, "output_selector") else ""
        method = self.split_method.get()
        page_range = self.page_range.get()

        if not hasattr(self, "status_label"):
            return

        if not pdf_file:
            self.status_label.config(text="⚠️ Please select a PDF file to split", foreground=COLORS["warning"])
        elif not output_dir:
            self.status_label.config(text="⚠️ Please specify an output folder", foreground=COLORS["warning"])
        elif method == "range" and not self._validate_page_range(page_range):
            self.status_label.config(
                text="⚠️ Please enter a valid page range (e.g., 1-3,5,7-9)",
                foreground=COLORS["warning"],
            )
        else:
            method_desc = {
                "single": "one file per page",
                "range": f"pages {page_range}" if page_range else "specified pages",
                "bookmarks": "split at bookmarks",
            }
            self.status_label.config(
                text=f"✅ Ready to split PDF into {method_desc.get(method, method)}",
                foreground=COLORS["success"],
            )

    def _on_method_changed(self):
        """Handle split method change to show/hide relevant options."""
        method = self.split_method.get()

        if method == "range":
            self.range_frame.grid()
        else:
            self.range_frame.grid_remove()

        self._update_validation_status()

    def _on_split(self):
        """Execute the PDF split operation with enhanced validation and feedback."""
        pdf_path = self.file_selector.get_file()

        # Enhanced validation with better user feedback
        if not pdf_path:
            messagebox.showwarning(
                "No File Selected",
                "Please select a PDF file to split.\n\nUse the 'Browse' button to choose a PDF file.",
            )
            self._update_validation_status()
            return

        out_dir = self.output_selector.get_path()
        if not out_dir:
            messagebox.showwarning(
                "No Output Folder",
                "Please specify where to save the split PDF files.\n\n"
                "Use the 'Browse' button to choose a destination folder.",
            )
            self._update_validation_status()
            return

        # Validate page range if using range method
        method = self.split_method.get()
        page_range = self.page_range.get()

        if method == "range" and not self._validate_page_range(page_range):
            messagebox.showwarning(
                "Invalid Page Range",
                "Please enter a valid page range.\n\n"
                "Examples:\n"
                "• 1-5 (pages 1 through 5)\n"
                "• 1,3,5 (pages 1, 3, and 5)\n"
                "• 1-3,7-9 (pages 1-3 and 7-9)",
            )
            self._update_validation_status()
            return

        # Create output directory if it doesn't exist
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        naming = self.naming_pattern.get()
        compress = self.compression_var.get()
        level = self.compression_level.get()
        password = self.password_var.get()

        # Show confirmation dialog with split details
        method_desc = {
            "single": "Split into individual pages",
            "range": f"Split pages: {page_range}",
            "bookmarks": "Split at bookmark locations",
        }

        confirm_msg = (
            f"Ready to split PDF file:\n\n"
            f"Source: {os.path.basename(pdf_path)}\n"
            f"Method: {method_desc.get(method, method)}\n"
            f"Output folder: {os.path.basename(out_dir)}\n\n"
            f"Proceed with split operation?"
        )

        if not messagebox.askyesno("Confirm Split Operation", confirm_msg):
            return

        # Update status and start split
        self.status_label.config(text="🔄 Splitting PDF file...", foreground=COLORS["info"])

        # Use the worker pattern from base class
        self._run_worker(
            lambda: self._split_worker(pdf_path, out_dir, method, page_range, naming, compress, level, password),
            f"Successfully split PDF using {method} method!",
        )

    def _split_worker(
        self,
        pdf_path: str,
        out_dir: str,
        method: str,
        page_range: str,
        naming: str,
        compress: bool,
        level: int,
        password: str,
    ):
        """Worker function to perform the split operation."""
        created = pdf_ops.split_pdf(
            pdf_path,
            output_dir=out_dir,
            method=method,
            page_range=page_range,
            naming_pattern=naming,
            compress=compress,
            compression_level=level,
            password=password,
        )  # type: ignore[arg-type]
        self.progress_tracker.update_progress(100, f"Created {len(created)} files")

    # Public wrapper used by tests/backwards compatibility
    def split_files(self) -> None:
        """Run the split action synchronously for testing."""
        pdf_path = self.file_selector.get_file()
        if not pdf_path:
            self.show_notification("no files", "error")
            return

        out_dir = self.output_selector.get_path()
        if not out_dir:
            self.show_notification("output directory required", "error")
            return

        method = self.split_method.get()
        page_range = self.page_range.get()
        naming = self.naming_pattern.get()
        compress = self.compression_var.get()
        level = self.compression_level.get()
        password = self.password_var.get()

        if method == "range" and not self._validate_page_range(page_range):
            self.show_notification("invalid page range", "error")
            return

        try:
            pdf_ops.split_pdf(
                pdf_path,
                output_dir=out_dir,
                method=method,
                page_range=page_range,
                naming_pattern=naming,
                compress=compress,
                compression_level=level,
                password=password,
            )  # type: ignore[arg-type]
            self.show_notification("split completed successfully", "success")
        except Exception as exc:  # pragma: no cover - error path
            self.show_notification(f"error: {exc}", "error")

    def _on_clear(self):
        """Clear all inputs with user confirmation for better UX."""
        if (
            self.file_selector.get_file()
            or self.output_selector.get_path()
            or self.page_range.get()
            or self.naming_pattern.get() != "page_{page}"
        ):
            if messagebox.askyesno(
                "Clear All Fields",
                "This will clear all settings and reset to defaults.\n\nAre you sure you want to continue?",
            ):
                self.file_selector.set_files([])
                self.output_selector.set_path("")
                self.progress_tracker.reset()

                # Reset options to defaults
                self.split_method.set("single")
                self.page_range.set("")
                self.naming_pattern.set("page_{page}")
                self.compression_var.set(False)
                self.compression_level.set(0)

                # Hide range frame if visible
                self.range_frame.grid_remove()

                self._update_validation_status()

                # Show feedback
                self.status_label.config(
                    text="🗑️ All fields cleared and reset to defaults",
                    foreground=COLORS["info"],
                )
                # Reset status after a delay
                self.after(2000, self._update_validation_status)
        else:
            # Nothing to clear, just update status
            self._update_validation_status()

    @staticmethod
    def _validate_page_range(value: str) -> bool:
        import re

        # Convert to string to handle MagicMock objects in tests
        str_value = str(value) if value is not None else ""
        return bool(re.fullmatch(r"[0-9,-]+", str_value))

    # ------------------------------------------------------------------
    # Enhanced Tab Lifecycle Hooks
    # ------------------------------------------------------------------
    def on_tab_activated(self):
        """Called when tab is activated - update validation status."""
        super().on_tab_activated()
        # Update validation status when tab becomes active
        self.after_idle(self._update_validation_status)
