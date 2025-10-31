"""Responsive section component for creating collapsible sections in the UI."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .constants import SPACING


class ResponsiveSection(ttk.Frame):
    """Section with header and content area that responds to size changes."""

    def __init__(self, master: tk.Widget, title: str, collapsible: bool = False, **kwargs):
        """Initialize responsive section.

        Args:
            master: Parent widget
            title: Section title
            collapsible: Whether section can be collapsed
            **kwargs: Additional ttk.Frame arguments
        """
        super().__init__(master, **kwargs)

        # Section state
        self.title = title
        self.collapsible = collapsible
        self.collapsed = False

        # Create header
        self.header_frame = ttk.Frame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["sm"])

        # Title label with optional toggle button
        if collapsible:
            self.toggle_btn = ttk.Button(self.header_frame, text="▼", width=2, command=self.toggle_collapse)
            self.toggle_btn.pack(side=tk.LEFT, padx=(0, SPACING["sm"]))

        self.title_label = ttk.Label(self.header_frame, text=title, font=("TkDefaultFont", 10, "bold"))
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Content frame
        self.content_frame = ttk.Frame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=SPACING["md"], pady=SPACING["sm"])

        # Configure content frame for expansion
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

        # Separator
        self.separator = ttk.Separator(self, orient="horizontal")
        self.separator.grid(row=2, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["sm"])

        # Configure grid weights for proper expansion
        self.columnconfigure(0, weight=1)  # Allow horizontal expansion
        self.rowconfigure(0, weight=0)  # Header - fixed height
        self.rowconfigure(1, weight=1)  # Content - expands
        self.rowconfigure(2, weight=0)  # Separator - fixed height

    def toggle_collapse(self):
        """Toggle section collapse state."""
        self.collapsed = not self.collapsed

        if self.collapsed:
            self.content_frame.grid_remove()
            self.toggle_btn.configure(text="▶")
        else:
            self.content_frame.grid()
            self.toggle_btn.configure(text="▼")
