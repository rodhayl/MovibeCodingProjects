"""Enhanced Extract tab implementation with improved UX/UI design.

Provides an intuitive interface to select a PDF file, specify page ranges,
and extract pages with clear visual hierarchy and user feedback.
"""

from __future__ import annotations

import logging
import os
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
    TabContentFrame,
)
from .base_tab import WorkerTab

logger = logging.getLogger(__name__)


class ExtractTab(WorkerTab, TabContentFrame):
    """Tab that extracts a page range from a PDF."""

    def __init__(self, master: tk.Widget, app: Any):
        WorkerTab.__init__(self, master, app)
        TabContentFrame.__init__(self, master)

        # Initialize variables for page range
        self.start_page_var = tk.IntVar(value=1)
        self.end_page_var = tk.IntVar(value=1)

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
            title="📄 Select PDF File to Extract From",
            collapsible=False,
        )
        sec.grid(row=0, column=0, sticky="nsew", pady=(0, SPACING["lg"]), padx=(0, SPACING["md"]))

        # Add descriptive help text
        help_label = ttk.Label(
            sec.content_frame,
            text="Choose a PDF file to extract specific pages from.",
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
        sec = ResponsiveSection(self.scrollable_frame, title="📄 Page Range Selection", collapsible=False)
        sec.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, SPACING["lg"]))

        # Create a frame for better organization of options
        range_frame = ttk.LabelFrame(sec.content_frame, text="Page Range Settings", padding=SPACING["md"])
        range_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["md"])
        range_frame.columnconfigure(1, weight=1)
        range_frame.columnconfigure(3, weight=1)

        # Add descriptive help text
        help_label = ttk.Label(
            range_frame,
            text="Specify which pages to extract from the PDF document.",
            font=("TkDefaultFont", 9),
            foreground=COLORS["gray"],
        )
        help_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, SPACING["md"]))

        # Start page input with enhanced layout
        ttk.Label(range_frame, text="Start page:").grid(row=1, column=0, sticky="w", pady=(0, SPACING["sm"]))

        start_spinbox = ttk.Spinbox(
            range_frame,
            from_=1,
            to=9999,
            textvariable=self.start_page_var,
            width=8,
        )
        start_spinbox.grid(
            row=1,
            column=1,
            sticky="w",
            padx=(SPACING["sm"], SPACING["lg"]),
            pady=(0, SPACING["sm"]),
        )
        start_spinbox.bind("<KeyRelease>", lambda e: self._update_validation_status())
        start_spinbox.bind("<<Increment>>", lambda e: self._update_validation_status())
        start_spinbox.bind("<<Decrement>>", lambda e: self._update_validation_status())

        # End page input with enhanced layout
        ttk.Label(range_frame, text="End page:").grid(row=1, column=2, sticky="w", pady=(0, SPACING["sm"]))

        end_spinbox = ttk.Spinbox(range_frame, from_=1, to=9999, textvariable=self.end_page_var, width=8)
        end_spinbox.grid(
            row=1,
            column=3,
            sticky="w",
            padx=(SPACING["sm"], 0),
            pady=(0, SPACING["sm"]),
        )
        end_spinbox.bind("<KeyRelease>", lambda e: self._update_validation_status())
        end_spinbox.bind("<<Increment>>", lambda e: self._update_validation_status())
        end_spinbox.bind("<<Decrement>>", lambda e: self._update_validation_status())

        # Quick selection buttons
        quick_frame = ttk.Frame(range_frame)
        quick_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(SPACING["md"], 0))

        ttk.Label(quick_frame, text="Quick selections:", font=("TkDefaultFont", 9)).grid(row=0, column=0, sticky="w")

        ttk.Button(
            quick_frame,
            text="First Page",
            command=lambda: self._set_page_range(1, 1),
            width=10,
        ).grid(row=0, column=1, sticky="w", padx=(SPACING["sm"], SPACING["xs"]))

        ttk.Button(quick_frame, text="All Pages", command=self._set_all_pages, width=10).grid(
            row=0, column=2, sticky="w", padx=(SPACING["xs"], SPACING["xs"])
        )

        ttk.Button(quick_frame, text="Last Page", command=self._set_last_page, width=10).grid(
            row=0, column=3, sticky="w", padx=(SPACING["xs"], 0)
        )

        # Page range preview
        preview_frame = ttk.LabelFrame(sec.content_frame, text="Extraction Preview", padding=SPACING["md"])
        preview_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))

        self.range_info_label = ttk.Label(
            preview_frame,
            text="Select a file and page range to see extraction details",
            font=("TkDefaultFont", 9),
            foreground=COLORS["gray"],
        )
        self.range_info_label.grid(row=0, column=0, sticky="w")

    def _create_output_section(self):
        """Create the output section with enhanced user guidance."""
        sec = ResponsiveSection(self.scrollable_frame, title="💾 Output Settings", collapsible=False)
        sec.grid(row=0, column=1, sticky="nsew", pady=(0, SPACING["lg"]), padx=(SPACING["md"], 0))

        # Add descriptive help text
        help_label = ttk.Label(
            sec.content_frame,
            text="Specify where to save the extracted pages as a new PDF file.",
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
            file_types=[("PDF files", "*.pdf")],
            label_text="Output file:",
        )
        self.output_selector.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["lg"]))

        # Bind output path change for validation updates
        if hasattr(self.output_selector, "output_path"):
            self.output_selector.output_path.trace("w", lambda *args: self._update_validation_status())

        # Post-extraction options frame
        completion_frame = ttk.LabelFrame(sec.content_frame, text="After Extraction", padding=SPACING["md"])
        completion_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(SPACING["md"], SPACING["lg"]),
        )

        self.open_after_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            completion_frame,
            text="Automatically open the extracted PDF file",
            variable=self.open_after_var,
        ).grid(row=0, column=0, sticky="w")

        self.preserve_bookmarks_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            completion_frame,
            text="Preserve bookmarks within the extracted range",
            variable=self.preserve_bookmarks_var,
        ).grid(row=1, column=0, sticky="w", pady=(SPACING["xs"], 0))

    def _create_action_section(self):
        """Create the action section with enhanced visual prominence and user feedback."""
        sec = ResponsiveSection(self.scrollable_frame, title="🚀 Execute Extraction", collapsible=False)
        sec.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, SPACING["xl"]))

        # Simplified progress tracking
        self.progress_tracker = ProgressTracker(sec.content_frame)
        self.progress_tracker.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["sm"])

        # Status indicator for real-time validation feedback
        status_frame = ttk.Frame(sec.content_frame)
        status_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))

        self.status_label = ttk.Label(
            status_frame,
            text="⚠️ Please select a PDF file and page range",
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
            text="📄 Extract Pages",
            command=self._on_extract,
            style="Accent.TButton",
        )
        self.action_button.pack(side=tk.LEFT, padx=(0, SPACING["md"]))

        # Secondary action button
        ttk.Button(btn_frame, text="🗑️ Clear All", command=self._on_clear).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Enhanced Methods with Better User Feedback and Validation
    # ------------------------------------------------------------------
    def _update_validation_status(self):
        """Update the validation status indicator based on current inputs."""
        pdf_file = self.file_selector.get_file() if hasattr(self, "file_selector") else ""
        output_path = self.output_selector.get_path() if hasattr(self, "output_selector") else ""
        start_page = self.start_page_var.get()
        end_page = self.end_page_var.get()

        if not hasattr(self, "status_label"):
            return

        if not pdf_file:
            self.status_label.config(
                text="⚠️ Please select a PDF file to extract from",
                foreground=COLORS["warning"],
            )
        elif not output_path:
            self.status_label.config(
                text="⚠️ Please specify an output file location",
                foreground=COLORS["warning"],
            )
        elif start_page < 1:
            self.status_label.config(text="⚠️ Start page must be 1 or greater", foreground=COLORS["warning"])
        elif end_page < start_page:
            self.status_label.config(
                text="⚠️ End page must be greater than or equal to start page",
                foreground=COLORS["warning"],
            )
        else:
            page_count = end_page - start_page + 1
            if page_count == 1:
                self.status_label.config(
                    text=f"✅ Ready to extract page {start_page}",
                    foreground=COLORS["success"],
                )
            else:
                self.status_label.config(
                    text=f"✅ Ready to extract {page_count} pages ({start_page}-{end_page})",
                    foreground=COLORS["success"],
                )

        # Update range preview
        self._update_range_preview()

    def _update_range_preview(self):
        """Update the range preview information."""
        if not hasattr(self, "range_info_label"):
            return

        pdf_file = self.file_selector.get_file() if hasattr(self, "file_selector") else ""
        start_page = self.start_page_var.get()
        end_page = self.end_page_var.get()

        if not pdf_file:
            self.range_info_label.config(
                text="Select a file and page range to see extraction details",
                foreground=COLORS["gray"],
            )
            return

        if start_page < 1 or end_page < start_page:
            self.range_info_label.config(text="Invalid page range specified", foreground=COLORS["warning"])
            return

        page_count = end_page - start_page + 1
        if page_count == 1:
            preview_text = f"Will extract page {start_page} from {os.path.basename(pdf_file)}"
        else:
            preview_text = (
                f"Will extract {page_count} pages ({start_page}-{end_page}) from {os.path.basename(pdf_file)}"
            )

        self.range_info_label.config(text=preview_text, foreground=COLORS["info"])

    def _set_page_range(self, start: int, end: int):
        """Set the page range to specific values."""
        self.start_page_var.set(start)
        self.end_page_var.set(end)
        self._update_validation_status()

    def _set_all_pages(self):
        """Set the page range to extract all pages."""
        # For now, set a reasonable default range
        # In a real implementation, you'd get the actual page count from the PDF
        self.start_page_var.set(1)
        self.end_page_var.set(999)  # Large number as placeholder
        self._update_validation_status()

    def _set_last_page(self):
        """Set the page range to extract only the last page."""
        # For now, set a reasonable default
        # In a real implementation, you'd get the actual page count from the PDF
        last_page = 999  # Placeholder
        self.start_page_var.set(last_page)
        self.end_page_var.set(last_page)
        self._update_validation_status()

    def _on_extract(self):
        """Execute the PDF extraction operation with enhanced validation and feedback."""
        pdf_path = self.file_selector.get_file()

        # Enhanced validation with better user feedback
        if not pdf_path:
            messagebox.showwarning(
                "No File Selected",
                "Please select a PDF file to extract pages from.\n\nUse the 'Browse' button to choose a PDF file.",
            )
            self._update_validation_status()
            return

        start_page = self.start_page_var.get()
        end_page = self.end_page_var.get()

        if start_page < 1:
            messagebox.showerror(
                "Invalid Start Page",
                "Start page must be 1 or greater.\n\nPlease enter a valid page number.",
            )
            self._update_validation_status()
            return

        if end_page < start_page:
            messagebox.showerror(
                "Invalid Page Range",
                "End page must be greater than or equal to start page.\n\n"
                f"Current range: {start_page} to {end_page}\n"
                "Please adjust the page range.",
            )
            self._update_validation_status()
            return

        out_path = self.output_selector.get_path()
        if not out_path:
            messagebox.showwarning(
                "No Output Location",
                "Please specify where to save the extracted pages.\n\n"
                "Use the 'Browse' button to choose a save location.",
            )
            self._update_validation_status()
            return

        # Ensure .pdf extension
        if not out_path.lower().endswith(".pdf"):
            out_path += ".pdf"
            self.output_selector.set_path(out_path)

        # Show confirmation dialog with extraction details
        page_count = end_page - start_page + 1
        if page_count == 1:
            page_desc = f"page {start_page}"
        else:
            page_desc = f"{page_count} pages ({start_page}-{end_page})"

        confirm_msg = (
            f"Ready to extract {page_desc}:\n\n"
            f"Source: {os.path.basename(pdf_path)}\n"
            f"Pages: {page_desc}\n"
            f"Output: {os.path.basename(out_path)}\n\n"
            f"Proceed with extraction?"
        )

        if not messagebox.askyesno("Confirm Extraction", confirm_msg):
            return

        # Update status and start extraction
        self.status_label.config(text="📄 Extracting pages from PDF...", foreground=COLORS["info"])

        # Use the worker pattern from base class
        self._run_worker(
            lambda: self._extract_worker(pdf_path, out_path, start_page, end_page),
            f"Successfully extracted {page_desc} from PDF!",
        )

    def _extract_worker(self, pdf_path: str, out_path: str, start_page: int, end_page: int):
        """Worker function to perform the extraction operation."""
        pdf_ops.extract_page_range(pdf_path, out_path, start_page, end_page)  # type: ignore[arg-type]
        self.progress_tracker.update_progress(100, "Done")

    # Public wrapper used by tests/backwards compatibility
    def extract_pages(self) -> None:
        """Run the extract action synchronously for testing."""
        pdf_path = self.file_selector.get_file()
        if not pdf_path:
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification("no file", "error")
            return

        start_page = self.start_page_var.get()
        end_page = self.end_page_var.get()
        if start_page < 1 or end_page < start_page:
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification("page range error", "error")
            return

        out_path = self.output_selector.get_path()
        if not out_path:
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification("output path required", "error")
            return

        try:
            pdf_ops.extract_page_range(pdf_path, out_path, start_page, end_page)  # type: ignore[arg-type]
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification("extract success", "success")
        except Exception as exc:  # pragma: no cover - error path
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification(f"error: {exc}", "error")

    def _on_clear(self):
        """Clear all inputs with user confirmation for better UX."""
        if (
            self.file_selector.get_file()
            or self.output_selector.get_path()
            or self.start_page_var.get() != 1
            or self.end_page_var.get() != 1
        ):
            if messagebox.askyesno(
                "Clear All Fields",
                "This will clear all settings and reset to defaults.\n\nAre you sure you want to continue?",
            ):
                self.file_selector.set_files([])
                self.output_selector.set_path("")
                self.start_page_var.set(1)
                self.end_page_var.set(1)
                self.progress_tracker.reset()

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

    # ------------------------------------------------------------------
    # Enhanced Tab Lifecycle Hooks
    # ------------------------------------------------------------------
    def on_tab_activated(self):
        """Called when tab is activated - update validation status."""
        super().on_tab_activated()
        # Update validation status when tab becomes active
        self.after_idle(self._update_validation_status)
