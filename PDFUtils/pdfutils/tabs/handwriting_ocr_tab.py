"""Enhanced Handwriting OCR tab with improved UX/UI design.

Features:
- Clean, organized layout with proper visual hierarchy
- Enhanced validation and user feedback
- Engine-specific help and model recommendations
- Comprehensive error handling and user guidance
- Consistent styling and spacing throughout

Provides UI to select a PDF, choose engine (pytesseract/kraken), optionally specify
model, set output format, and run handwriting OCR via
pdf_ops.handwriting_ocr_from_pdf.
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
)
from .base_tab import WorkerTab

logger = logging.getLogger(__name__)


class HandwritingOcrTab(WorkerTab):
    """Enhanced tab for handwriting OCR operations with improved UX/UI.

    Features:
    - Comprehensive input validation with real-time feedback
    - Engine-specific help and model recommendations
    - Clear visual hierarchy and consistent styling
    - Enhanced error handling and user guidance
    """

    _ENGINES = ["pytesseract", "kraken"]  # pytesseract is default, kraken optional
    _FORMATS = ["text", "json"]

    # Engine-specific help text
    _ENGINE_HELP = {
        "pytesseract": "General-purpose OCR engine. Good for printed text and basic handwriting.",
        "kraken": "Specialized for historical documents and complex handwriting. Requires model files.",
    }

    # Model recommendations
    _MODEL_RECOMMENDATIONS = {
        "pytesseract": "No model file needed - uses built-in training data",
        "kraken": "Specify path to .mlmodel file for best results with handwriting",
    }

    def __init__(self, master: tk.Widget, app: Any):
        super().__init__(master, app)

        # Validation status tracking
        self.validation_status = {
            "input_file": False,
            "output_path": False,
            "pages": True,  # Optional field, valid by default
            "model": True,  # Optional field, valid by default
        }

        self._setup_ui()
        self._setup_validation()

    def _setup_ui(self):
        """Set up the enhanced UI components with improved layout."""
        self._create_input_output_sections()
        self._create_options_section()
        self._create_action_section()

    def _create_input_output_sections(self):
        """Create input and output sections in horizontal layout."""
        self._create_input_section()
        self._create_output_section()

    def _setup_validation(self):
        """Set up real-time validation for form fields."""
        # File selector validation
        if hasattr(self.file_selector, "path_var"):
            self.file_selector.path_var.trace("w", self._validate_input_file)

        # Output selector validation
        if hasattr(self.output_selector, "path_var"):
            self.output_selector.path_var.trace("w", self._validate_output_path)

        # Pages validation
        self.pages_var.trace("w", self._validate_pages)

        # Model validation
        self.model_var.trace("w", self._validate_model)

    def _validate_input_file(self, *args):
        """Validate input file selection."""
        file_path = self.file_selector.get_file()
        is_valid = bool(file_path and os.path.exists(file_path) and file_path.lower().endswith(".pdf"))
        self.validation_status["input_file"] = is_valid
        self._update_action_button_state()

    def _validate_output_path(self, *args):
        """Validate output path selection."""
        output_path = self.output_selector.get_path()
        is_valid = bool(output_path and len(output_path.strip()) > 0)
        self.validation_status["output_path"] = is_valid
        self._update_action_button_state()

    def _validate_pages(self, *args):
        """Validate pages input format."""
        pages_str = self.pages_var.get().strip()
        if not pages_str:
            self.validation_status["pages"] = True  # Empty is valid (means all pages)
            return

        try:
            # Check if it's a valid comma-separated list of integers
            pages = [int(p.strip()) for p in pages_str.split(",") if p.strip()]
            is_valid = len(pages) > 0 and all(p > 0 for p in pages)
            self.validation_status["pages"] = is_valid
        except ValueError:
            self.validation_status["pages"] = False

        self._update_action_button_state()

    def _validate_model(self, *args):
        """Validate model path if specified."""
        model_path = self.model_var.get().strip()
        if not model_path:
            self.validation_status["model"] = True  # Empty is valid (optional)
            return

        # Check if file exists and has appropriate extension for kraken
        engine = self.engine_var.get()
        if engine == "kraken":
            is_valid = os.path.exists(model_path) and model_path.lower().endswith(".mlmodel")
        else:
            is_valid = True  # pytesseract doesn't need model files

        self.validation_status["model"] = is_valid
        self._update_action_button_state()

    def _update_action_button_state(self):
        """Update the action button state based on validation status."""
        # Check if all required fields are valid
        required_valid = self.validation_status["input_file"] and self.validation_status["output_path"]
        optional_valid = self.validation_status["pages"] and self.validation_status["model"]

        all_valid = required_valid and optional_valid

        if hasattr(self, "action_button"):
            self.action_button.configure(state="normal" if all_valid else "disabled")

        # Update overall status
        self._update_overall_status(all_valid, required_valid)

    def _update_overall_status(self, all_valid: bool, required_valid: bool):
        """Update the overall status message based on validation state."""
        if not hasattr(self, "overall_status_label"):
            return

        if all_valid:
            self.overall_status_label.configure(
                text="✅ Ready to process handwriting OCR", foreground=COLORS.get("success", "green")
            )
        elif required_valid:
            self.overall_status_label.configure(
                text="⚠️ Check optional fields for optimal results", foreground=COLORS.get("warning", "orange")
            )
        else:
            missing = []
            if not self.validation_status["input_file"]:
                missing.append("PDF file")
            if not self.validation_status["output_path"]:
                missing.append("output path")

            self.overall_status_label.configure(
                text=f"❌ Missing: {', '.join(missing)}", foreground=COLORS.get("error", "red")
            )

    def _on_engine_changed(self, event=None):
        """Handle engine selection change."""
        engine = self.engine_var.get()

        # Update engine help text
        if hasattr(self, "engine_help_label"):
            self.engine_help_label.configure(text=self._ENGINE_HELP.get(engine, ""))

        # Update model help text
        if hasattr(self, "model_help_label"):
            self.model_help_label.configure(text=self._MODEL_RECOMMENDATIONS.get(engine, ""))

        # Update model browse button state
        if hasattr(self, "model_browse_btn"):
            # Enable browse button for kraken, disable for pytesseract
            state = "normal" if engine == "kraken" else "disabled"
            self.model_browse_btn.configure(state=state)

        # Re-validate model field
        self._validate_model()

    def _on_format_changed(self, event=None):
        """Handle output format change."""
        fmt = self.format_var.get()

        # Update output file extension if path is set
        current_path = self.output_selector.get_path()
        if current_path:
            ext_map = {"text": ".txt", "json": ".json"}
            desired_ext = ext_map.get(fmt, ".txt")

            # Remove old extension and add new one
            base_path = os.path.splitext(current_path)[0]
            new_path = base_path + desired_ext
            self.output_selector.set_path(new_path)

    def _browse_model_file(self):
        """Open file dialog to browse for model file."""
        from tkinter import filedialog

        filetypes = [("Kraken Model files", "*.mlmodel"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select Model File", filetypes=filetypes)

        if filename:
            self.model_var.set(filename)

    # ------------------------------------------------------------------
    def _create_input_section(self):
        """Create enhanced input section with validation feedback."""
        sec = ResponsiveSection(self.scrollable_frame, title="📄 Input Document", collapsible=False)
        sec.grid(row=0, column=0, sticky="ew", pady=SPACING["sm"], padx=(0, SPACING["sm"]))

        # Help text for input section
        help_frame = ttk.Frame(sec.content_frame)
        help_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=(SPACING["sm"], 0))

        help_label = ttk.Label(
            help_frame,
            text="Select a PDF document containing handwritten text for OCR processing.",
            foreground=COLORS["muted"],
        )
        help_label.pack(anchor="w")

        self.file_selector = FileSelector(
            sec.content_frame,
            file_types=[("PDF files", "*.pdf")],
            label_text="PDF Document:",
            multiple=False,
            show_preview=True,
        )
        self.file_selector.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])

        # Status indicator for input validation
        self.input_status_frame = ttk.Frame(sec.content_frame)
        self.input_status_frame.grid(row=2, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["sm"]))

        self.input_status_label = ttk.Label(self.input_status_frame, text="", foreground=COLORS["muted"])
        self.input_status_label.pack(anchor="w")

    def _create_options_section(self):
        """Create enhanced options section with engine-specific help and validation."""
        sec = ResponsiveSection(self.scrollable_frame, title="⚙️ OCR Configuration", collapsible=False)
        sec.grid(row=1, column=0, columnspan=2, sticky="ew", pady=SPACING["sm"])

        sec.content_frame.columnconfigure(1, weight=1)

        # Section help text
        help_frame = ttk.Frame(sec.content_frame)
        help_frame.grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=SPACING["md"], pady=(SPACING["sm"], SPACING["md"])
        )

        help_label = ttk.Label(
            help_frame,
            text="Configure OCR engine and processing options for optimal handwriting recognition.",
            foreground=COLORS["muted"],
        )
        help_label.pack(anchor="w")

        # Engine selection with enhanced styling
        engine_label = ttk.Label(sec.content_frame, text="OCR Engine:", font=("TkDefaultFont", 9, "bold"))
        engine_label.grid(row=1, column=0, sticky="w", padx=SPACING["md"])

        self.engine_var = tk.StringVar(value="pytesseract")
        self.engine_combo = ttk.Combobox(
            sec.content_frame,
            values=self._ENGINES,
            textvariable=self.engine_var,
            state="readonly",
        )
        self.engine_combo.grid(row=1, column=1, sticky="ew", padx=(0, SPACING["md"]))
        self.engine_combo.bind("<<ComboboxSelected>>", self._on_engine_changed)

        # Engine help text
        self.engine_help_label = ttk.Label(
            sec.content_frame,
            text=self._ENGINE_HELP["pytesseract"],
            foreground=COLORS["muted"],
            wraplength=400,
        )
        self.engine_help_label.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=SPACING["md"], pady=(SPACING["xs"], SPACING["sm"])
        )

        # Model path with enhanced validation
        model_label = ttk.Label(sec.content_frame, text="Model File (optional):", font=("TkDefaultFont", 9, "bold"))
        model_label.grid(row=3, column=0, sticky="w", padx=SPACING["md"], pady=(SPACING["sm"], 0))

        model_frame = ttk.Frame(sec.content_frame)
        model_frame.grid(row=3, column=1, sticky="ew", padx=(0, SPACING["md"]), pady=(SPACING["sm"], 0))
        model_frame.columnconfigure(0, weight=1)

        self.model_var = tk.StringVar()
        self.model_entry = ttk.Entry(model_frame, textvariable=self.model_var)
        self.model_entry.grid(row=0, column=0, sticky="ew", padx=(0, SPACING["xs"]))

        self.model_browse_btn = ttk.Button(model_frame, text="Browse...", command=self._browse_model_file, width=10)
        self.model_browse_btn.grid(row=0, column=1)

        # Model help text
        self.model_help_label = ttk.Label(
            sec.content_frame,
            text=self._MODEL_RECOMMENDATIONS["pytesseract"],
            foreground=COLORS["muted"],
            wraplength=400,
        )
        self.model_help_label.grid(
            row=4, column=0, columnspan=2, sticky="ew", padx=SPACING["md"], pady=(SPACING["xs"], SPACING["sm"])
        )

        # Output format with better styling
        format_label = ttk.Label(sec.content_frame, text="Output Format:", font=("TkDefaultFont", 9, "bold"))
        format_label.grid(row=5, column=0, sticky="w", padx=SPACING["md"], pady=(SPACING["sm"], 0))

        self.format_var = tk.StringVar(value="text")
        self.format_combo = ttk.Combobox(
            sec.content_frame,
            values=self._FORMATS,
            textvariable=self.format_var,
            state="readonly",
        )
        self.format_combo.grid(row=5, column=1, sticky="ew", padx=(0, SPACING["md"]), pady=(SPACING["sm"], 0))
        self.format_combo.bind("<<ComboboxSelected>>", self._on_format_changed)

        # Format help text
        format_help = ttk.Label(
            sec.content_frame,
            text="Text: Plain text output | JSON: Structured output with confidence scores",
            foreground=COLORS["muted"],
        )
        format_help.grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=SPACING["md"], pady=(SPACING["xs"], SPACING["sm"])
        )

        # Pages entry with validation feedback
        pages_label = ttk.Label(sec.content_frame, text="Pages to Process:", font=("TkDefaultFont", 9, "bold"))
        pages_label.grid(row=7, column=0, sticky="w", padx=SPACING["md"], pady=(SPACING["sm"], 0))

        self.pages_var = tk.StringVar()
        self.pages_entry = ttk.Entry(sec.content_frame, textvariable=self.pages_var)
        self.pages_entry.grid(row=7, column=1, sticky="ew", padx=(0, SPACING["md"]), pady=(SPACING["sm"], 0))

        # Pages help text
        pages_help = ttk.Label(
            sec.content_frame,
            text="Enter page numbers (e.g., '1,3,5' or '1-3,7') or leave empty for all pages",
            foreground=COLORS["muted"],
        )
        pages_help.grid(
            row=8, column=0, columnspan=2, sticky="ew", padx=SPACING["md"], pady=(SPACING["xs"], SPACING["sm"])
        )

        # Status indicators for validation
        self.options_status_frame = ttk.Frame(sec.content_frame)
        self.options_status_frame.grid(
            row=9, column=0, columnspan=2, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["sm"])
        )

        self.options_status_label = ttk.Label(self.options_status_frame, text="", foreground=COLORS["muted"])
        self.options_status_label.pack(anchor="w")

    def _create_output_section(self):
        """Create enhanced output section with format-aware file selection."""
        sec = ResponsiveSection(self.scrollable_frame, title="💾 Output Configuration", collapsible=False)
        sec.grid(row=0, column=1, sticky="ew", pady=SPACING["sm"], padx=(SPACING["sm"], 0))

        # Help text for output section
        help_frame = ttk.Frame(sec.content_frame)
        help_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=(SPACING["sm"], 0))

        help_label = ttk.Label(
            help_frame,
            text="Specify where to save the OCR results. File extension will be updated based on output format.",
            foreground=COLORS["muted"],
        )
        help_label.pack(anchor="w")

        self.output_selector = OutputFileSelector(
            sec.content_frame,
            file_types=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")],
            label_text="Output File:",
            default_extension=".txt",
        )
        self.output_selector.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])

        # Status indicator for output validation
        self.output_status_frame = ttk.Frame(sec.content_frame)
        self.output_status_frame.grid(row=2, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["sm"]))

        self.output_status_label = ttk.Label(self.output_status_frame, text="", foreground=COLORS["muted"])
        self.output_status_label.pack(anchor="w")

    def _create_action_section(self):
        """Create enhanced action section with better button styling and status."""
        sec = ResponsiveSection(self.scrollable_frame, title="🚀 Processing", collapsible=False)
        sec.grid(row=2, column=0, columnspan=2, sticky="ew", pady=SPACING["sm"])

        # Overall status indicator
        status_frame = ttk.Frame(sec.content_frame)
        status_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=(SPACING["sm"], 0))

        self.overall_status_label = ttk.Label(
            status_frame, text="Ready to process handwriting OCR", foreground=COLORS["muted"]
        )
        self.overall_status_label.pack(anchor="w")

        self.progress_tracker = ProgressTracker(sec.content_frame)
        self.progress_tracker.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["xs"])

        # Enhanced button frame with better styling
        btn_frame = ttk.Frame(sec.content_frame)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["sm"])
        btn_frame.columnconfigure(0, weight=1)  # Push buttons to the right

        # Button container for right alignment
        button_container = ttk.Frame(btn_frame)
        button_container.grid(row=0, column=1, sticky="e")

        self.action_button = ttk.Button(
            button_container,
            text="🔍 Run Handwriting OCR",
            command=self._on_ocr,
            state="disabled",  # Start disabled until validation passes
        )
        self.action_button.pack(side=tk.LEFT, padx=(0, SPACING["sm"]))

        self.clear_button = ttk.Button(button_container, text="🗑️ Clear All", command=self._on_clear)
        self.clear_button.pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    def _on_ocr(self, skip_confirmation=False):
        """Handle OCR button click with enhanced validation and user feedback.

        Args:
            skip_confirmation: If True, skip the confirmation dialog (for testing)
        """
        # Initialize validation status
        self.validation_status = {"input_file": False, "output_path": False, "pages": True, "model": True}

        # Enhanced validation with specific error messages
        pdf_path = self.file_selector.get_file()
        if not pdf_path:
            self._show_validation_error("Input Required", "Please select a PDF file to process.")
            return

        if not os.path.exists(pdf_path):
            self._show_validation_error("File Not Found", f"The selected PDF file does not exist:\n{pdf_path}")
            return

        if not pdf_path.lower().endswith(".pdf"):
            self._show_validation_error("Invalid File Type", "Please select a valid PDF file.")
            return

        self.validation_status["input_file"] = True

        out_path = self.output_selector.get_path()
        if not out_path:
            self._show_validation_error("Output Required", "Please specify an output file path.")
            return

        self.validation_status["output_path"] = True

        # Validate pages format
        pages_str = self.pages_var.get().strip()
        pages = None
        if pages_str:
            try:
                pages = [int(p.strip()) for p in pages_str.split(",") if p.strip()]
                if not pages or any(p <= 0 for p in pages):
                    self._show_validation_error(
                        "Invalid Pages", "Page numbers must be positive integers (e.g., '1,2,3')."
                    )
                    return
                self.validation_status["pages"] = True
            except ValueError:
                self._show_validation_error(
                    "Invalid Pages Format", "Please enter page numbers as comma-separated integers (e.g., '1,2,3')."
                )
                return

        # Validate engine and model
        engine = self.engine_var.get()
        model = self.model_var.get().strip() or None

        if engine == "kraken" and model and not os.path.exists(model):
            self._show_validation_error("Model File Not Found", f"The specified model file does not exist:\n{model}")
            return

        if engine == "kraken" and model and not model.lower().endswith(".mlmodel"):
            self._show_validation_error("Invalid Model File", "Kraken model files should have .mlmodel extension.")
            return

        self.validation_status["model"] = True

        # Update file extension based on format
        fmt = self.format_var.get()
        ext_map = {"text": ".txt", "json": ".json"}
        desired_ext = ext_map.get(fmt, ".txt")
        if not out_path.lower().endswith(desired_ext):
            out_path = os.path.splitext(out_path)[0] + desired_ext
            self.output_selector.set_path(out_path)

        # Show confirmation dialog with settings summary
        if not skip_confirmation:
            pages_text = f"Pages {', '.join(map(str, pages))}" if pages else "All pages"
            model_text = f"Model: {os.path.basename(model)}" if model else "Default model"

            settings_summary = (
                f"Input: {os.path.basename(pdf_path)}\n"
                f"Engine: {engine}\n"
                f"{model_text}\n"
                f"Format: {fmt.upper()}\n"
                f"Processing: {pages_text}\n"
                f"Output: {os.path.basename(out_path)}"
            )

            result = messagebox.askyesno(
                "Confirm Handwriting OCR",
                f"Ready to process handwriting OCR with these settings:\n\n{settings_summary}\n\nProceed?",
                icon="question",
            )

            if not result:
                return

        # Update status labels
        self._update_status_labels("processing")

        # Use WorkerTab pattern
        self._run_worker(
            lambda: self._ocr_worker(pdf_path, out_path, pages, engine, model, fmt),
            f"✅ Handwriting OCR completed successfully!\n\nResults saved to: {out_path}",
        )

    def _show_validation_error(self, title: str, message: str):
        """Show validation error message and update status."""
        messagebox.showerror(title, message)
        if hasattr(self, "overall_status_label"):
            self.overall_status_label.configure(text=f"❌ {title}", foreground=COLORS.get("error", "red"))

    def _update_status_labels(self, status: str):
        """Update various status labels based on current state."""
        if status == "processing":
            if hasattr(self, "overall_status_label"):
                self.overall_status_label.configure(
                    text="🔄 Processing handwriting OCR...", foreground=COLORS.get("info", "blue")
                )
        elif status == "ready":
            if hasattr(self, "overall_status_label"):
                self.overall_status_label.configure(
                    text="✅ Ready to process handwriting OCR", foreground=COLORS.get("success", "green")
                )

    def _ocr_worker(self, pdf_path: str, out_path: str, pages, engine: str, model, fmt: str):
        """Worker function to perform OCR operation."""
        pdf_ops.handwriting_ocr_from_pdf(
            input_file=pdf_path,
            output_file=out_path,
            pages=pages,
            engine=engine,
            model=model,
            output_format=fmt,
        )  # type: ignore[arg-type]

    # Public wrapper used by tests/backwards compatibility
    def perform_ocr(self) -> None:
        """Run the handwriting OCR action synchronously for testing."""
        pdf_path = self.file_selector.get_file()
        if not pdf_path:
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification("no file", "error")
            return

        out_path = self.output_selector.get_path()
        if not out_path:
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification("no output", "error")
            return

        fmt = self.format_var.get()
        ext_map = {"text": ".txt", "json": ".json"}
        desired_ext = ext_map.get(fmt, ".txt")
        if not out_path.lower().endswith(desired_ext):
            out_path += desired_ext
            self.output_selector.set_path(out_path)

        engine = self.engine_var.get()
        model = self.model_var.get() or None
        pages_str = self.pages_var.get().strip()
        pages = None if not pages_str else [int(p) for p in pages_str.split(",") if p.strip().isdigit()]

        try:
            pdf_ops.handwriting_ocr_from_pdf(
                input_file=pdf_path,
                output_file=out_path,
                pages=pages,
                engine=engine,
                model=model,
                output_format=fmt,
            )  # type: ignore[arg-type]
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification("ocr success", "success")
        except Exception as exc:  # pragma: no cover - error path
            if hasattr(self.app, "notification_panel"):
                self.app.notification_panel.show_notification(f"error: {exc}", "error")

    def _on_clear(self, skip_confirmation=False):
        """Clear all form fields with optional confirmation.

        Args:
            skip_confirmation: If True, skip the confirmation dialog (for testing)
        """
        # Check if there's any content to clear
        has_content = (
            bool(self.file_selector.get_file())
            or bool(self.output_selector.get_path())
            or bool(self.model_var.get())
            or bool(self.pages_var.get())
            or self.engine_var.get() != "pytesseract"
            or self.format_var.get() != "text"
        )

        if has_content and not skip_confirmation:
            result = messagebox.askyesno(
                "Clear All Fields",
                "This will clear all input fields and reset settings to defaults.\n\nAre you sure?",
                icon="question",
            )
            if not result:
                return

        # Comprehensive reset
        self.file_selector.set_files([])
        self.output_selector.set_path("")
        self.engine_var.set("pytesseract")
        self.model_var.set("")
        self.format_var.set("text")
        self.pages_var.set("")
        self.progress_tracker.reset()

        # Reset validation status
        self.validation_status = {"input_file": False, "output_path": False, "pages": True, "model": True}

        # Update UI elements safely
        self._safe_update_ui_after_clear()

    def _safe_update_ui_after_clear(self):
        """Safely update UI elements after clearing, handling missing widgets."""
        try:
            # Update engine-specific help text
            if hasattr(self, "engine_help_label"):
                self.engine_help_label.configure(text=self._ENGINE_HELP["pytesseract"])

            if hasattr(self, "model_help_label"):
                self.model_help_label.configure(text=self._MODEL_RECOMMENDATIONS["pytesseract"])

            # Update model browse button state
            if hasattr(self, "model_browse_btn"):
                self.model_browse_btn.configure(state="disabled")

            # Update status labels
            if hasattr(self, "overall_status_label"):
                self.overall_status_label.configure(
                    text="Ready to process handwriting OCR", foreground=COLORS.get("muted", "gray")
                )

            # Update action button state
            self._update_action_button_state()

        except Exception as e:
            # Log error but don't crash the application
            logging.warning(f"Error updating UI after clear: {e}")

    # ------------------------------------------------------------------
    def on_tab_activated(self):
        """Called when tab is activated - update validation status."""
        # Re-validate all fields when tab becomes active
        self._validate_input_file()
        self._validate_output_path()
        self._validate_pages()
        self._validate_model()

        # Update overall status
        self._update_action_button_state()
