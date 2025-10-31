"""Enhanced Compress tab implementation with improved UX/UI design.

Provides an intuitive interface to select a PDF file, choose compression settings,
and execute PDF compression with clear visual hierarchy and user feedback.
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


class CompressTab(WorkerTab, TabContentFrame):
    """Tab that compresses a PDF to a smaller size."""

    _QUALITIES = ["screen", "ebook", "printer", "prepress"]

    def __init__(self, master: tk.Widget, app: Any):
        WorkerTab.__init__(self, master, app)
        TabContentFrame.__init__(self, master)

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
            title="📄 Select PDF File to Compress",
            collapsible=False,
        )
        sec.grid(row=0, column=0, sticky="nsew", pady=(0, SPACING["sm"]), padx=(0, SPACING["md"]))

        # Add descriptive help text
        help_label = ttk.Label(
            sec.content_frame,
            text="Choose a PDF file to reduce its file size while maintaining quality.",
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
        sec = ResponsiveSection(self.scrollable_frame, title="⚙️ Compression Settings", collapsible=False)
        sec.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, SPACING["sm"]))

        # Create a frame for better organization of options
        options_frame = ttk.LabelFrame(sec.content_frame, text="Quality Settings", padding=SPACING["md"])
        options_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["md"])
        options_frame.columnconfigure(1, weight=1)

        # Quality preset selection with enhanced descriptions
        ttk.Label(options_frame, text="Quality preset:").grid(row=0, column=0, sticky="w", pady=(0, SPACING["sm"]))

        self.quality_var = tk.StringVar(value="screen")
        quality_combo = ttk.Combobox(
            options_frame,
            textvariable=self.quality_var,
            values=self._QUALITIES,
            state="readonly",
            width=15,
        )
        quality_combo.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(SPACING["sm"], 0),
            pady=(0, SPACING["sm"]),
        )
        quality_combo.bind("<<ComboboxSelected>>", lambda e: self._update_validation_status())

        # Quality descriptions with better formatting
        quality_descriptions = {
            "screen": "Lowest file size, suitable for screen viewing (72 DPI)",
            "ebook": "Good balance of size and quality for e-readers (150 DPI)",
            "printer": "Higher quality for printing (300 DPI)",
            "prepress": "Highest quality for professional printing (300+ DPI)",
        }

        # Description label that updates based on selection
        self.quality_desc_label = ttk.Label(
            options_frame,
            text=quality_descriptions["screen"],
            font=("TkDefaultFont", 8),
            foreground=COLORS["gray"],
            wraplength=400,
        )
        self.quality_desc_label.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(SPACING["xs"], SPACING["md"]),
        )

        # Bind quality change to update description
        def update_description(*args):
            selected = self.quality_var.get()
            if selected in quality_descriptions:
                self.quality_desc_label.config(text=quality_descriptions[selected])
            self._update_validation_status()

        self.quality_var.trace("w", update_description)

        # File size estimation frame
        estimation_frame = ttk.LabelFrame(sec.content_frame, text="Compression Preview", padding=SPACING["md"])
        estimation_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["sm"]))

        self.size_info_label = ttk.Label(
            estimation_frame,
            text="Select a file to see estimated compression results",
            font=("TkDefaultFont", 9),
            foreground=COLORS["gray"],
        )
        self.size_info_label.grid(row=0, column=0, sticky="w")

    def _create_output_section(self):
        """Create the output section with enhanced user guidance."""
        sec = ResponsiveSection(self.scrollable_frame, title="💾 Output Settings", collapsible=False)
        sec.grid(row=0, column=1, sticky="nsew", pady=(0, SPACING["lg"]), padx=(SPACING["md"], 0))

        # Add descriptive help text
        help_label = ttk.Label(
            sec.content_frame,
            text="Specify where to save the compressed PDF file.",
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

        # Post-compression options frame
        completion_frame = ttk.LabelFrame(sec.content_frame, text="After Compression", padding=SPACING["md"])
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
            text="Automatically open the compressed PDF file",
            variable=self.open_after_var,
        ).grid(row=0, column=0, sticky="w")

        self.show_comparison_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            completion_frame,
            text="Show file size comparison after compression",
            variable=self.show_comparison_var,
        ).grid(row=1, column=0, sticky="w", pady=(SPACING["xs"], 0))

    def _create_action_section(self):
        """Create the action section with enhanced visual prominence and user feedback."""
        sec = ResponsiveSection(self.scrollable_frame, title="🚀 Execute Compression", collapsible=False)
        sec.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, SPACING["xl"]))

        # Simplified progress tracking
        self.progress_tracker = ProgressTracker(sec.content_frame)
        self.progress_tracker.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["sm"])

        # Status indicator for real-time validation feedback
        status_frame = ttk.Frame(sec.content_frame)
        status_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))

        self.status_label = ttk.Label(
            status_frame,
            text="⚠️ Please select a PDF file to compress",
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
            text="🗜️ Compress PDF",
            command=self._on_compress,
            style="Accent.TButton",
        )
        self.action_button.pack(side=tk.LEFT, padx=(0, SPACING["md"]))

        # Backward compatibility alias for tests
        self.compress_btn = self.action_button

        # Secondary action button
        ttk.Button(btn_frame, text="🗑️ Clear All", command=self._on_clear).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Enhanced Methods with Better User Feedback and Validation
    # ------------------------------------------------------------------
    def _update_validation_status(self):
        """Update the validation status indicator based on current inputs."""
        pdf_file = self.file_selector.get_file() if hasattr(self, "file_selector") else ""
        output_path = self.output_selector.get_path() if hasattr(self, "output_selector") else ""
        quality = self.quality_var.get() if hasattr(self, "quality_var") else ""

        if not hasattr(self, "status_label"):
            return

        if not pdf_file:
            self.status_label.config(
                text="⚠️ Please select a PDF file to compress",
                foreground=COLORS["warning"],
            )
        elif not output_path:
            self.status_label.config(
                text="⚠️ Please specify an output file location",
                foreground=COLORS["warning"],
            )
        elif quality not in self._QUALITIES:
            self.status_label.config(
                text="⚠️ Please select a valid quality preset",
                foreground=COLORS["warning"],
            )
        else:
            quality_desc = {
                "screen": "screen viewing quality",
                "ebook": "e-book quality",
                "printer": "print quality",
                "prepress": "professional print quality",
            }
            self.status_label.config(
                text=f"✅ Ready to compress PDF with {quality_desc.get(quality, quality)}",
                foreground=COLORS["success"],
            )

        # Update file size estimation if file is selected
        self._update_size_estimation()

    def _update_size_estimation(self):
        """Update the file size estimation based on selected file and quality."""
        if not hasattr(self, "size_info_label"):
            return

        pdf_file = self.file_selector.get_file() if hasattr(self, "file_selector") else ""

        if not pdf_file or not os.path.exists(pdf_file):
            self.size_info_label.config(
                text="Select a file to see estimated compression results",
                foreground=COLORS["gray"],
            )
            return

        try:
            # Get current file size
            current_size = os.path.getsize(pdf_file)
            current_size_mb = current_size / (1024 * 1024)

            # Estimate compression ratios based on quality
            compression_ratios = {
                "screen": 0.3,  # 70% reduction
                "ebook": 0.5,  # 50% reduction
                "printer": 0.7,  # 30% reduction
                "prepress": 0.85,  # 15% reduction
            }

            quality = self.quality_var.get()
            ratio = compression_ratios.get(quality, 0.5)
            estimated_size_mb = current_size_mb * ratio
            reduction_percent = int((1 - ratio) * 100)

            self.size_info_label.config(
                text=f"Current: {current_size_mb:.1f} MB → Estimated: {estimated_size_mb:.1f} MB "
                f"({reduction_percent}% reduction)",
                foreground=COLORS["info"],
            )
        except (OSError, ValueError):
            self.size_info_label.config(text="Unable to estimate file size", foreground=COLORS["warning"])

    def _on_compress(self):
        """Execute the PDF compression operation with enhanced validation and feedback."""
        pdf_path = self.file_selector.get_file()

        # Enhanced validation with better user feedback
        if not pdf_path:
            messagebox.showwarning(
                "No File Selected",
                "Please select a PDF file to compress.\n\nUse the 'Browse' button to choose a PDF file.",
            )
            self._update_validation_status()
            return

        out_path = self.output_selector.get_path()
        if not out_path:
            messagebox.showwarning(
                "No Output Location",
                "Please specify where to save the compressed PDF file.\n\n"
                "Use the 'Browse' button to choose a save location.",
            )
            self._update_validation_status()
            return

        # Ensure .pdf extension
        if not out_path.lower().endswith(".pdf"):
            out_path += ".pdf"
            self.output_selector.set_path(out_path)

        quality = self.quality_var.get()
        if quality not in self._QUALITIES:
            messagebox.showerror(
                "Invalid Quality Setting",
                "Please select a valid quality preset from the dropdown.\n\n"
                f"Available options: {', '.join(self._QUALITIES)}",
            )
            self._update_validation_status()
            return

        # Show confirmation dialog with compression details
        try:
            file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            quality_desc = {
                "screen": "Screen viewing (smallest file size)",
                "ebook": "E-book reading (balanced size/quality)",
                "printer": "Printing (higher quality)",
                "prepress": "Professional printing (highest quality)",
            }

            confirm_msg = (
                f"Ready to compress PDF file:\n\n"
                f"Source: {os.path.basename(pdf_path)} ({file_size_mb:.1f} MB)\n"
                f"Quality: {quality_desc.get(quality, quality)}\n"
                f"Output: {os.path.basename(out_path)}\n\n"
                f"Proceed with compression?"
            )
        except OSError:
            confirm_msg = (
                f"Ready to compress PDF file:\n\n"
                f"Source: {os.path.basename(pdf_path)}\n"
                f"Quality: {quality}\n"
                f"Output: {os.path.basename(out_path)}\n\n"
                f"Proceed with compression?"
            )

        if not messagebox.askyesno("Confirm Compression", confirm_msg):
            return

        # Update status and start compression
        self.status_label.config(text="🗜️ Compressing PDF file...", foreground=COLORS["info"])

        # Store original file size for comparison
        try:
            self.original_size = os.path.getsize(pdf_path)
        except OSError:
            self.original_size = None

        # Use the worker pattern from base class
        self._run_worker(
            lambda: self._compress_worker(pdf_path, out_path, quality),
            f"Successfully compressed PDF with {quality} quality!",
        )

    def _compress_worker(self, pdf_path: str, out_path: str, quality: str):
        """Worker function to perform the compression operation."""
        pdf_ops.compress_pdf(pdf_path, out_path, quality)  # type: ignore[arg-type]

    def _on_clear(self):
        """Clear all inputs with user confirmation for better UX."""
        if self.file_selector.get_file() or self.output_selector.get_path() or self.quality_var.get() != "screen":
            if messagebox.askyesno(
                "Clear All Fields",
                "This will clear all settings and reset to defaults.\n\nAre you sure you want to continue?",
            ):
                self.file_selector.set_files([])
                self.output_selector.set_path("")
                self.progress_tracker.reset()

                # Reset quality to default
                self.quality_var.set("screen")

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
