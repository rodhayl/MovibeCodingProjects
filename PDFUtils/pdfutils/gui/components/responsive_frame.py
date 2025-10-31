"""Responsive frame component for creating responsive layouts."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ResponsiveFrame(ttk.Frame):
    """Frame with responsive layout capabilities."""

    def __init__(self, master: tk.Widget, **kwargs):
        """Initialize responsive frame.

        Args:
            master: Parent widget
            **kwargs: Additional ttk.Frame arguments
        """
        super().__init__(master, **kwargs)

        # Configure grid weights for responsiveness
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Minimum sizes
        self.min_width = 300
        self.min_height = 200

        # Current size
        self.current_width = self.winfo_width()
        self.current_height = self.winfo_height()

        # Track resources for cleanup
        self._configure_callbacks = []

        # Bind to configure event to detect size changes
        # Use lambda to avoid issues with mocked bind methods
        try:
            self.bind("<Configure>", lambda event: self._on_configure(event))
        except (TypeError, AttributeError):
            # If bind fails (e.g., in tests with mocks), ignore
            pass

        # Bind to destroy event for cleanup
        try:
            self.bind("<Destroy>", lambda event: self._on_destroy(event))
        except (TypeError, AttributeError):
            # If bind fails (e.g., in tests with mocks), ignore
            pass

    def _on_configure(self, event):
        """Handle configure event (resize)."""
        # Only respond to size changes
        if event.width != self.current_width or event.height != self.current_height:
            self.current_width = max(event.width, self.min_width)
            self.current_height = max(event.height, self.min_height)

            # Call resize handler
            self.on_resize(self.current_width, self.current_height)

    def _on_destroy(self, event):
        """Clean up resources when widget is destroyed."""
        if event.widget is not self:
            return

        # Unbind events to prevent memory leaks
        try:
            self.unbind("<Configure>")
            self.unbind("<Destroy>")
        except Exception:
            pass

        # Clear callback references (no longer needed)
        if hasattr(self, "_configure_callbacks"):
            self._configure_callbacks.clear()

    def on_resize(self, width, height):
        """Handle resize event - override in subclasses."""
        pass
