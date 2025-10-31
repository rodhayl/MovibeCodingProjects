"""Enhanced OCR tab implementation with improved UX/UI design.

Provides an intuitive interface to select PDF files, configure OCR settings,
and extract text with clear visual hierarchy and user feedback.
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


class OcrTab(WorkerTab, TabContentFrame):
    """Tab that performs OCR on a PDF."""

    _LANGS = ["eng", "spa", "fra", "deu"]  # example subset

    def __init__(self, master: tk.Widget, app: Any):
        WorkerTab.__init__(self, master, app)
        TabContentFrame.__init__(self, master)

        # Initialize variables for OCR settings
        self.lang_var = tk.StringVar(value="eng")
        self.binarize_var = tk.BooleanVar(value=False)
        self.threshold_var = tk.StringVar(value="128")
        self.resize_factor_var = tk.StringVar(value="1.0")
        self.deskew_var = tk.BooleanVar(value=False)
        self.denoise_var = tk.BooleanVar(value=False)
        self.contrast_factor_var = tk.StringVar(value="1.0")
        self.brightness_factor_var = tk.StringVar(value="1.0")
        self.sharpen_var = tk.BooleanVar(value=False)
        self.blur_var = tk.StringVar(value="0.0")

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
        sec = ResponsiveSection(self.scrollable_frame, title="📄 Select PDF File for OCR", collapsible=False)
        sec.grid(row=0, column=0, sticky="nsew", pady=(0, SPACING["lg"]), padx=(0, SPACING["md"]))

        # Add descriptive help text
        help_label = ttk.Label(
            sec.content_frame,
            text="Choose a PDF file to extract text using Optical Character Recognition (OCR).",
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
        sec = ResponsiveSection(self.scrollable_frame, title="⚙️ OCR Configuration", collapsible=False)
        sec.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, SPACING["lg"]))

        # Language settings frame
        lang_frame = ttk.LabelFrame(sec.content_frame, text="Language Settings", padding=SPACING["md"])
        lang_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["md"])
        lang_frame.columnconfigure(1, weight=1)

        # Language selection with enhanced description
        ttk.Label(lang_frame, text="OCR Language:").grid(row=0, column=0, sticky="w", pady=(0, SPACING["sm"]))

        # Create combobox with enhanced options
        lang_options = {
            "eng": "English",
            "spa": "Spanish (Español)",
            "fra": "French (Français)",
            "deu": "German (Deutsch)",
        }

        lang_combo = ttk.Combobox(
            lang_frame,
            values=list(lang_options.values()),
            state="readonly",
            width=20,
        )
        lang_combo.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(SPACING["sm"], 0),
            pady=(0, SPACING["sm"]),
        )

        # Set default and bind change event
        lang_combo.set(lang_options["eng"])

        def on_lang_change(event):
            selected = lang_combo.get()
            for code, name in lang_options.items():
                if name == selected:
                    self.lang_var.set(code)
                    break
            self._update_validation_status()

        lang_combo.bind("<<ComboboxSelected>>", on_lang_change)

        ttk.Label(
            lang_frame,
            text="Select the primary language of text in your PDF for better accuracy",
            font=("TkDefaultFont", 8),
            foreground=COLORS["gray"],
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(SPACING["xs"], 0))

        # Image preprocessing frame
        preprocess_frame = ttk.LabelFrame(sec.content_frame, text="Image Preprocessing", padding=SPACING["md"])
        preprocess_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        preprocess_frame.columnconfigure(1, weight=1)
        preprocess_frame.columnconfigure(3, weight=1)

        # Add help text for preprocessing
        ttk.Label(
            preprocess_frame,
            text="Adjust these settings to improve OCR accuracy for your specific document type",
            font=("TkDefaultFont", 9),
            foreground=COLORS["gray"],
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, SPACING["md"]))

        # Basic preprocessing options (row 1)
        ttk.Checkbutton(
            preprocess_frame,
            text="Binarize (convert to black & white)",
            variable=self.binarize_var,
            command=self._update_validation_status,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, SPACING["sm"]))

        ttk.Checkbutton(
            preprocess_frame,
            text="Deskew (straighten tilted text)",
            variable=self.deskew_var,
            command=self._update_validation_status,
        ).grid(row=1, column=2, columnspan=2, sticky="w", pady=(0, SPACING["sm"]))

        # Threshold setting (row 2)
        ttk.Label(preprocess_frame, text="Threshold (0-255):").grid(
            row=2, column=0, sticky="w", pady=(SPACING["sm"], 0)
        )
        threshold_entry = ttk.Entry(preprocess_frame, textvariable=self.threshold_var, width=8)
        threshold_entry.grid(
            row=2,
            column=1,
            sticky="w",
            padx=(SPACING["sm"], SPACING["lg"]),
            pady=(SPACING["sm"], 0),
        )
        threshold_entry.bind("<KeyRelease>", lambda e: self._update_validation_status())

        # Resize factor (row 2, right side)
        ttk.Label(preprocess_frame, text="Resize factor:").grid(row=2, column=2, sticky="w", pady=(SPACING["sm"], 0))
        resize_entry = ttk.Entry(preprocess_frame, textvariable=self.resize_factor_var, width=8)
        resize_entry.grid(
            row=2,
            column=3,
            sticky="w",
            padx=(SPACING["sm"], 0),
            pady=(SPACING["sm"], 0),
        )
        resize_entry.bind("<KeyRelease>", lambda e: self._update_validation_status())

        # Enhancement options frame
        enhance_frame = ttk.LabelFrame(sec.content_frame, text="Image Enhancement", padding=SPACING["md"])
        enhance_frame.grid(row=2, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        enhance_frame.columnconfigure(1, weight=1)
        enhance_frame.columnconfigure(3, weight=1)

        # Enhancement checkboxes (row 0)
        ttk.Checkbutton(
            enhance_frame,
            text="Denoise (remove noise)",
            variable=self.denoise_var,
            command=self._update_validation_status,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, SPACING["sm"]))

        ttk.Checkbutton(
            enhance_frame,
            text="Sharpen (enhance edges)",
            variable=self.sharpen_var,
            command=self._update_validation_status,
        ).grid(row=0, column=2, columnspan=2, sticky="w", pady=(0, SPACING["sm"]))

        # Contrast adjustment (row 1)
        ttk.Label(enhance_frame, text="Contrast (0.5-2.0):").grid(row=1, column=0, sticky="w", pady=(SPACING["sm"], 0))
        contrast_entry = ttk.Entry(enhance_frame, textvariable=self.contrast_factor_var, width=8)
        contrast_entry.grid(
            row=1,
            column=1,
            sticky="w",
            padx=(SPACING["sm"], SPACING["lg"]),
            pady=(SPACING["sm"], 0),
        )
        contrast_entry.bind("<KeyRelease>", lambda e: self._update_validation_status())

        # Brightness adjustment (row 1, right side)
        ttk.Label(enhance_frame, text="Brightness (0.5-2.0):").grid(
            row=1, column=2, sticky="w", pady=(SPACING["sm"], 0)
        )
        brightness_entry = ttk.Entry(enhance_frame, textvariable=self.brightness_factor_var, width=8)
        brightness_entry.grid(
            row=1,
            column=3,
            sticky="w",
            padx=(SPACING["sm"], 0),
            pady=(SPACING["sm"], 0),
        )
        brightness_entry.bind("<KeyRelease>", lambda e: self._update_validation_status())

        # Blur setting (row 2)
        ttk.Label(enhance_frame, text="Blur (0.0-5.0):").grid(row=2, column=0, sticky="w", pady=(SPACING["sm"], 0))
        blur_entry = ttk.Entry(enhance_frame, textvariable=self.blur_var, width=8)
        blur_entry.grid(
            row=2,
            column=1,
            sticky="w",
            padx=(SPACING["sm"], 0),
            pady=(SPACING["sm"], 0),
        )
        blur_entry.bind("<KeyRelease>", lambda e: self._update_validation_status())

        # Preset buttons frame
        preset_frame = ttk.LabelFrame(sec.content_frame, text="Quick Presets", padding=SPACING["md"])
        preset_frame.grid(row=3, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))

        ttk.Label(
            preset_frame,
            text="Apply common settings for different document types:",
            font=("TkDefaultFont", 9),
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, SPACING["sm"]))

        ttk.Button(
            preset_frame,
            text="📄 Clean Text",
            command=self._apply_clean_preset,
            width=12,
        ).grid(row=1, column=0, sticky="w", padx=(0, SPACING["xs"]))

        ttk.Button(
            preset_frame,
            text="📰 Newspaper",
            command=self._apply_newspaper_preset,
            width=12,
        ).grid(row=1, column=1, sticky="w", padx=(SPACING["xs"], SPACING["xs"]))

        ttk.Button(
            preset_frame,
            text="📋 Handwritten",
            command=self._apply_handwritten_preset,
            width=12,
        ).grid(row=1, column=2, sticky="w", padx=(SPACING["xs"], SPACING["xs"]))

        ttk.Button(preset_frame, text="🔄 Reset", command=self._reset_preprocessing, width=12).grid(
            row=1, column=3, sticky="w", padx=(SPACING["xs"], 0)
        )

    def _create_output_section(self):
        """Create the output section with enhanced user guidance."""
        sec = ResponsiveSection(self.scrollable_frame, title="💾 Output Settings", collapsible=False)
        sec.grid(row=0, column=1, sticky="nsew", pady=(0, SPACING["lg"]), padx=(SPACING["md"], 0))

        # Add descriptive help text
        help_label = ttk.Label(
            sec.content_frame,
            text="Specify where to save the extracted text from the PDF.",
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
            file_types=[("Text files", "*.txt"), ("All files", "*.*")],
            label_text="Output text file:",
            default_extension=".txt",
        )
        self.output_selector.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["lg"]))

        # Bind output path change for validation updates
        if hasattr(self.output_selector, "output_path"):
            self.output_selector.output_path.trace("w", lambda *args: self._update_validation_status())

        # Post-OCR options frame
        completion_frame = ttk.LabelFrame(sec.content_frame, text="After OCR Completion", padding=SPACING["md"])
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
            text="Automatically open the extracted text file",
            variable=self.open_after_var,
        ).grid(row=0, column=0, sticky="w")

        self.show_preview_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            completion_frame,
            text="Show text preview in a popup window",
            variable=self.show_preview_var,
        ).grid(row=1, column=0, sticky="w", pady=(SPACING["xs"], 0))

    def _create_action_section(self):
        """Create the action section with enhanced visual prominence and user feedback."""
        sec = ResponsiveSection(self.scrollable_frame, title="🚀 Execute OCR", collapsible=False)
        sec.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, SPACING["xl"]))

        # Simplified progress tracking
        self.progress_tracker = ProgressTracker(sec.content_frame)
        self.progress_tracker.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["sm"])

        # Status indicator for real-time validation feedback
        status_frame = ttk.Frame(sec.content_frame)
        status_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))

        self.status_label = ttk.Label(
            status_frame,
            text="⚠️ Please select a PDF file and output location",
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
        self.action_button = ttk.Button(btn_frame, text="🔍 Run OCR", command=self._on_ocr, style="Accent.TButton")
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

        if not hasattr(self, "status_label"):
            return

        if not pdf_file:
            self.status_label.config(
                text="⚠️ Please select a PDF file for OCR processing",
                foreground=COLORS["warning"],
            )
        elif not output_path:
            self.status_label.config(
                text="⚠️ Please specify an output text file location",
                foreground=COLORS["warning"],
            )
        elif not self._validate_preprocessing_values():
            self.status_label.config(
                text="⚠️ Please check preprocessing values (numbers should be valid)",
                foreground=COLORS["warning"],
            )
        else:
            lang_name = {
                "eng": "English",
                "spa": "Spanish",
                "fra": "French",
                "deu": "German",
            }.get(self.lang_var.get(), self.lang_var.get())

            self.status_label.config(
                text=f"✅ Ready to perform OCR in {lang_name}",
                foreground=COLORS["success"],
            )

    def _validate_preprocessing_values(self):
        """Validate that all preprocessing numeric values are valid."""
        try:
            threshold = int(self.threshold_var.get())
            if not (0 <= threshold <= 255):
                return False

            resize_factor = float(self.resize_factor_var.get())
            if not (0.1 <= resize_factor <= 5.0):
                return False

            contrast_factor = float(self.contrast_factor_var.get())
            if not (0.1 <= contrast_factor <= 5.0):
                return False

            brightness_factor = float(self.brightness_factor_var.get())
            if not (0.1 <= brightness_factor <= 5.0):
                return False

            blur = float(self.blur_var.get())
            if not (0.0 <= blur <= 10.0):
                return False

            return True
        except ValueError:
            return False

    def _apply_clean_preset(self):
        """Apply preset for clean, high-quality documents."""
        self.binarize_var.set(False)
        self.threshold_var.set("128")
        self.resize_factor_var.set("1.0")
        self.deskew_var.set(True)
        self.denoise_var.set(False)
        self.contrast_factor_var.set("1.0")
        self.brightness_factor_var.set("1.0")
        self.sharpen_var.set(False)
        self.blur_var.set("0.0")
        self._update_validation_status()

    def _apply_newspaper_preset(self):
        """Apply preset for newspaper or low-quality scanned documents."""
        self.binarize_var.set(True)
        self.threshold_var.set("140")
        self.resize_factor_var.set("1.5")
        self.deskew_var.set(True)
        self.denoise_var.set(True)
        self.contrast_factor_var.set("1.3")
        self.brightness_factor_var.set("1.1")
        self.sharpen_var.set(True)
        self.blur_var.set("0.5")
        self._update_validation_status()

    def _apply_handwritten_preset(self):
        """Apply preset for handwritten documents."""
        self.binarize_var.set(True)
        self.threshold_var.set("120")
        self.resize_factor_var.set("2.0")
        self.deskew_var.set(True)
        self.denoise_var.set(True)
        self.contrast_factor_var.set("1.5")
        self.brightness_factor_var.set("1.2")
        self.sharpen_var.set(True)
        self.blur_var.set("0.3")
        self._update_validation_status()

    def _reset_preprocessing(self):
        """Reset all preprocessing options to defaults."""
        self.binarize_var.set(False)
        self.threshold_var.set("128")
        self.resize_factor_var.set("1.0")
        self.deskew_var.set(False)
        self.denoise_var.set(False)
        self.contrast_factor_var.set("1.0")
        self.brightness_factor_var.set("1.0")
        self.sharpen_var.set(False)
        self.blur_var.set("0.0")
        self._update_validation_status()

    def _on_ocr(self):
        """Enhanced OCR execution with comprehensive validation and user feedback."""
        pdf_path = self.file_selector.get_file()
        out_path = self.output_selector.get_path()

        # Enhanced validation with specific error messages
        if not pdf_path:
            messagebox.showerror(
                "Input Required",
                "Please select a PDF file to perform OCR on.\n\nUse the 'Browse...' button to choose your PDF file.",
            )
            return

        if not out_path:
            messagebox.showerror(
                "Output Required",
                "Please specify where to save the extracted text.\n\n"
                "Use the 'Browse...' button to choose the output location.",
            )
            return

        # Validate file existence and permissions
        if not os.path.exists(pdf_path):
            messagebox.showerror(
                "File Not Found",
                f"The selected PDF file could not be found:\n{pdf_path}\n\nPlease select a valid PDF file.",
            )
            return

        # Validate preprocessing values
        if not self._validate_preprocessing_values():
            messagebox.showerror(
                "Invalid Settings",
                "Some preprocessing values are invalid.\n\n"
                "Please check that all numeric values are within valid ranges:\n"
                "• Threshold: 0-255\n"
                "• Resize Factor: 0.1-5.0\n"
                "• Contrast/Brightness: 0.1-5.0\n"
                "• Blur: 0.0-10.0",
            )
            return

        if not out_path.lower().endswith(".txt"):
            out_path += ".txt"
            self.output_selector.set_path(out_path)

        # Show confirmation dialog with OCR settings summary
        lang_name = {
            "eng": "English",
            "spa": "Spanish",
            "fra": "French",
            "deu": "German",
        }.get(self.lang_var.get(), self.lang_var.get())

        preprocessing_info = []
        if self.binarize_var.get():
            preprocessing_info.append(f"Binarization (threshold: {self.threshold_var.get()})")
        if float(self.resize_factor_var.get()) != 1.0:
            preprocessing_info.append(f"Resize factor: {self.resize_factor_var.get()}")
        if self.deskew_var.get():
            preprocessing_info.append("Deskewing")
        if self.denoise_var.get():
            preprocessing_info.append("Noise removal")
        if self.sharpen_var.get():
            preprocessing_info.append("Sharpening")

        preprocessing_text = "\n• ".join(preprocessing_info) if preprocessing_info else "None"

        confirm_message = (
            f"Ready to perform OCR with the following settings:\n\n"
            f"📄 Input: {os.path.basename(pdf_path)}\n"
            f"💾 Output: {os.path.basename(out_path)}\n"
            f"🌐 Language: {lang_name}\n"
            f"⚙️ Preprocessing: {preprocessing_text}\n\n"
            f"This may take several minutes for large documents.\n"
            f"Do you want to continue?"
        )

        if not messagebox.askyesno("Confirm OCR Processing", confirm_message):
            return

        # Update status and start OCR
        if hasattr(self, "status_label"):
            self.status_label.config(text="🔄 Starting OCR processing...", foreground=COLORS["info"])

        language = self.lang_var.get()

        # Get preprocessing options
        binarize = self.binarize_var.get()
        try:
            threshold = int(self.threshold_var.get())
        except ValueError:
            threshold = 128
        try:
            resize_factor = float(self.resize_factor_var.get())
        except ValueError:
            resize_factor = 1.0
        deskew = self.deskew_var.get()
        denoise = self.denoise_var.get()
        try:
            contrast_factor = float(self.contrast_factor_var.get())
        except ValueError:
            contrast_factor = 1.0
        try:
            brightness_factor = float(self.brightness_factor_var.get())
        except ValueError:
            brightness_factor = 1.0
        sharpen = self.sharpen_var.get()
        try:
            blur = float(self.blur_var.get())
        except ValueError:
            blur = 0.0

        # Use the worker pattern from base class
        self._run_worker(
            lambda: self._ocr_worker(
                pdf_path,
                out_path,
                language,
                binarize,
                threshold,
                resize_factor,
                deskew,
                denoise,
                contrast_factor,
                brightness_factor,
                sharpen,
                blur,
            ),
            "OCR completed successfully",
        )

    def _ocr_worker(
        self,
        pdf_path: str,
        out_path: str,
        language: str,
        binarize: bool,
        threshold: int,
        resize_factor: float,
        deskew: bool,
        denoise: bool,
        contrast_factor: float,
        brightness_factor: float,
        sharpen: bool,
        blur: float,
    ):
        """Worker function to perform the OCR operation."""
        pdf_ops.extract_text_with_ocr(
            pdf_path,
            out_path,
            language=language,
            binarize=binarize,
            threshold=threshold,
            resize_factor=resize_factor,
            deskew=deskew,
            denoise=denoise,
            contrast_factor=contrast_factor,
            brightness_factor=brightness_factor,
            sharpen=sharpen,
            blur=blur,
            progress_callback=None,
        )  # type: ignore[arg-type]
        self.progress_tracker.update_progress(100, "Done")

    # Public wrapper used by tests/backwards compatibility
    def perform_ocr(self) -> None:
        """Run the OCR action synchronously for testing."""
        pdf_path = self.file_selector.get_file()
        if not pdf_path:
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification("no file", "error")
            return

        out_path = self.output_selector.get_path()
        if not out_path:
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification("output path required", "error")
            return

        if not out_path.lower().endswith(".txt"):
            out_path += ".txt"
            self.output_selector.set_path(out_path)

        language = self.lang_var.get()

        # Get preprocessing options
        binarize = self.binarize_var.get()
        try:
            threshold = int(self.threshold_var.get())
        except ValueError:
            threshold = 128
        try:
            resize_factor = float(self.resize_factor_var.get())
        except ValueError:
            resize_factor = 1.0
        deskew = self.deskew_var.get()
        denoise = self.denoise_var.get()
        try:
            contrast_factor = float(self.contrast_factor_var.get())
        except ValueError:
            contrast_factor = 1.0
        try:
            brightness_factor = float(self.brightness_factor_var.get())
        except ValueError:
            brightness_factor = 1.0
        sharpen = self.sharpen_var.get()
        try:
            blur = float(self.blur_var.get())
        except ValueError:
            blur = 0.0

        try:
            pdf_ops.extract_text_with_ocr(
                pdf_path,
                out_path,
                language=language,
                binarize=binarize,
                threshold=threshold,
                resize_factor=resize_factor,
                deskew=deskew,
                denoise=denoise,
                contrast_factor=contrast_factor,
                brightness_factor=brightness_factor,
                sharpen=sharpen,
                blur=blur,
                progress_callback=None,
            )  # type: ignore[arg-type]
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification("ocr success", "success")
        except Exception as exc:  # pragma: no cover - error path
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification(f"error: {exc}", "error")

    def _on_clear(self):
        """Enhanced clear method with user confirmation and comprehensive reset."""
        # Check if there's anything to clear
        has_content = (
            self.file_selector.get_file()
            or self.output_selector.get_path()
            or any(
                [
                    self.binarize_var.get(),
                    float(self.resize_factor_var.get()) != 1.0,
                    self.deskew_var.get(),
                    self.denoise_var.get(),
                    self.sharpen_var.get(),
                    float(self.blur_var.get()) != 0.0,
                    float(self.contrast_factor_var.get()) != 1.0,
                    float(self.brightness_factor_var.get()) != 1.0,
                    int(self.threshold_var.get()) != 128,
                ]
            )
        )

        if not has_content:
            messagebox.showinfo("Nothing to Clear", "The form is already empty. No changes to make.")
            return

        # Ask for confirmation
        if not messagebox.askyesno(
            "Confirm Clear",
            "This will clear all current inputs and reset OCR settings to defaults.\n\n"
            "Are you sure you want to continue?",
        ):
            return

        # Clear all inputs and reset settings
        self.file_selector.set_files([])
        self.output_selector.set_path("")
        self.lang_var.set("eng")
        # Reset preprocessing options
        self.binarize_var.set(False)
        self.threshold_var.set("128")
        self.resize_factor_var.set("1.0")
        self.deskew_var.set(False)
        self.denoise_var.set(False)
        self.contrast_factor_var.set("1.0")
        self.brightness_factor_var.set("1.0")
        self.sharpen_var.set(False)
        self.blur_var.set("0.0")
        self.progress_tracker.reset()

        # Update status
        if hasattr(self, "status_label"):
            self.status_label.config(
                text="✨ Form cleared successfully. Ready for new OCR task.",
                foreground=COLORS["success"],
            )

            # Reset status after a delay
            self.after(
                3000,
                lambda: (
                    self.status_label.config(
                        text="📄 Select a PDF file to begin OCR processing",
                        foreground=COLORS["muted"],
                    )
                    if hasattr(self, "status_label")
                    else None
                ),
            )

    def on_tab_activated(self):
        """Called when the OCR tab is activated - update validation status."""
        super().on_tab_activated()
        # Update validation status when tab becomes active
        self._update_validation_status()


# Alias for backward compatibility
OCRTab = OcrTab
