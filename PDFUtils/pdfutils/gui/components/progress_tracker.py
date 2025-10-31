"""Progress tracker component for displaying progress information."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from .constants import SPACING


class ProgressTracker(ttk.Frame):
    """Progress tracker with progress bar and status message."""

    def __init__(self, master: tk.Widget, **kwargs):
        """Initialize progress tracker.

        Args:
            master: Parent widget
            **kwargs: Additional ttk.Frame arguments
        """
        super().__init__(master, **kwargs)

        # Progress variables - use master for proper memory management
        # This helps prevent memory leaks by ensuring variables are properly
        # destroyed when the parent widget is destroyed
        self.progress_var = tk.DoubleVar(master=master, value=0)
        self.status_var = tk.StringVar(master=master, value="Ready")
        self.percent_var = tk.StringVar(master=master, value="0%")

        # Track variables for cleanup
        self._tk_vars = [self.progress_var, self.status_var, self.percent_var]

        # Create single-line horizontal layout
        self.columnconfigure(0, weight=0)  # Status label - fixed width
        self.columnconfigure(1, weight=1)  # Progress bar - expands
        self.columnconfigure(2, weight=0)  # Percentage label - fixed width

        # All elements in single row
        self.status_label = ttk.Label(self, textvariable=self.status_var, width=12)
        self.status_label.grid(row=0, column=0, sticky="w", padx=(0, SPACING["sm"]))

        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100, mode="determinate")
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=SPACING["sm"])

        self.percent_label = ttk.Label(self, textvariable=self.percent_var, width=5)
        self.percent_label.grid(row=0, column=2, sticky="e", padx=(SPACING["sm"], 0))

        # Bind destruction event for cleanup
        self.bind("<Destroy>", self._on_destroy)

    def update_progress(self, value: float, status: Optional[str] = None):
        """Update progress value and optionally status.

        Args:
            value: Progress value (0-100)
            status: Optional status message
        """
        # Convert to float and clamp the value to 0-100 range
        clamped_value = float(value)
        if clamped_value < 0:
            clamped_value = 0.0
        elif clamped_value > 100:
            clamped_value = 100.0

        # Update progress bar value (using the exact value for smooth animation)
        self.progress_var.set(clamped_value)

        # Update percentage display with proper rounding
        # Note: We use round() which rounds to nearest even number for .5 values
        percent_value = round(clamped_value)
        self.percent_var.set(f"{percent_value}%")

        # Update status if provided
        if status is not None:
            self.status_var.set(status)

    def reset(self):
        """Reset progress tracker."""
        self.progress_var.set(0)
        self.percent_var.set("0%")
        self.status_var.set("Ready")

    def is_running(self):
        """Check if progress is currently running (not at 0 or 100)."""
        current_progress = self.progress_var.get()
        return 0 < current_progress < 100

    def _on_destroy(self, event):
        """Clean up resources when widget is destroyed.

        This prevents memory leaks by explicitly releasing references to tkinter variables
        and other resources that might otherwise be kept alive in circular references.
        """
        if event.widget is not self:
            return

        # Clear references to all tkinter variables
        for var in self._tk_vars:
            if hasattr(var, "set"):
                try:
                    # Reset the variable to default value
                    if isinstance(var, tk.StringVar):
                        var.set("")
                    elif isinstance(var, (tk.DoubleVar, tk.IntVar)):
                        var.set(0)
                    elif isinstance(var, tk.BooleanVar):
                        var.set(False)
                except Exception:
                    pass  # Ignore errors during cleanup

        # Clear the variables list itself
        self._tk_vars.clear()

        # Remove other circular references
        self.progress_bar = None
        self.status_label = None
        self.percent_label = None
