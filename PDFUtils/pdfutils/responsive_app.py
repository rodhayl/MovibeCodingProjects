"""Minimal responsive application scaffold for PDFUtils.

This simplified implementation focuses on stability and clarity:
- No menus, diagnostics, or theme toggles
- No lazy-loading of tabs or resize gymnastics
- A basic global notification bar and status label
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class _SimpleNotificationPanel(ttk.Frame):
    """Lightweight notification bar with optional auto-hide."""

    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self._label_var = tk.StringVar(master=self, value="")
        self._label = ttk.Label(self, textvariable=self._label_var)
        self._label.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        self._after_id: Optional[str] = None
        self.grid_remove()

    def show_notification(self, message: str, _type: str = "info", auto_hide: int = 4000):
        """Show a notification message with optional auto-hide."""
        prefix = {
            "info": "Info",
            "success": "Success",
            "warning": "Warning",
            "error": "Error",
        }.get(_type, "Info")
        self._label_var.set(f"{prefix}: {message}")
        self.grid()

        # Cancel any existing auto-hide timer
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

        # Set new auto-hide timer if requested
        if auto_hide > 0:
            self._after_id = self.after(auto_hide, self.clear_notification)

    def clear_notification(self):
        """Clear the notification and hide the panel."""
        self._label_var.set("")
        self.grid_remove()


class ResponsiveApp(ttk.Frame):
    """Slim app frame with a `ttk.Notebook`, a notification bar, and a status label."""

    def __init__(self, master: tk.Tk):
        super().__init__(master)

        self.master = master
        self.master.title("PDF Utilities")
        self.master.minsize(1450, 1000)  # Extra wide window for compact horizontal layouts  # Optimized for Full HD (1920x1080) displays
        self.master.resizable(True, True)

        # Configure grid weights for proper expansion
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)  # notebook - expands
        self.rowconfigure(1, weight=0)  # notifications - fixed height
        self.rowconfigure(2, weight=0)  # status bar - fixed height

        # Configure master grid to ensure this frame expands
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        # Tabs with enhanced styling for better selection visibility
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Configure notebook styling for better tab selection visibility
        self._configure_notebook_styling()

        # Global notification bar
        self.notification_panel = _SimpleNotificationPanel(self)
        self.notification_panel.grid(row=1, column=0, sticky="ew")

        # Status bar
        status_frame = ttk.Frame(self)
        status_frame.grid(row=2, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)
        self._status_var = tk.StringVar(master=self, value="")
        self._status_label = ttk.Label(status_frame, textvariable=self._status_var)
        self._status_label.grid(row=0, column=0, sticky="w", padx=8, pady=4)

        # Bookkeeping
        self.tabs: Dict[str, ttk.Frame] = {}

        # Layout root - ensure this frame fills the entire window
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_propagate(False)  # Allow manual size control

        # Close handler
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)

    def add_tab(self, tab_id: str, tab_title: str, tab_content: ttk.Frame):
        """Add a tab to the notebook."""
        self.notebook.add(tab_content, text=tab_title)
        self.tabs[tab_id] = tab_content

    def set_status(self, _state: str, message: Optional[str] = None):
        """Set the status message. State parameter is ignored in simplified app."""
        if message:
            self._status_var.set(message)

    def show_notification(self, message: str, notification_type: str = "info", auto_hide: int = 4000):
        """Show a notification message."""
        self.notification_panel.show_notification(message, notification_type, auto_hide)

    def finalize_setup(self):
        """Finalize application setup. No special actions needed in simplified app."""
        pass

    def _configure_notebook_styling(self):
        """Configure notebook styling for better tab selection visibility."""
        try:
            # Create a custom style for the notebook
            style = ttk.Style()

            # Configure tab styling for better visibility
            style.configure(
                "TNotebook.Tab",
                padding=[20, 8],  # Increase padding for better appearance
                focuscolor="none",  # Remove focus outline
            )

            # Configure selected tab to be more obvious
            style.map(
                "TNotebook.Tab",
                background=[
                    ("selected", "#0078d4"),  # Blue background for selected tab
                    ("active", "#e1ecf4"),  # Light blue for hover
                    ("", "#f0f0f0"),  # Light gray for unselected
                ],
                foreground=[
                    ("selected", "white"),  # White text for selected tab
                    ("active", "black"),  # Black text for hover
                    ("", "black"),  # Black text for unselected
                ],
                relief=[
                    ("selected", "solid"),  # Solid border for selected
                    ("", "flat"),  # Flat for unselected
                ],
            )

        except Exception:
            # Fallback if styling fails - continue without custom styling
            pass

    def _on_closing(self):
        """Handle application closing."""
        try:
            self.destroy()
        finally:
            self.master.destroy()
