"""Scrollable tab content with status and notifications (simplified)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional, Tuple

from .constants import SPACING
from .notification_panel import NotificationPanel
from .status_indicator import StatusIndicator


class TabContentFrame(ttk.Frame):
    """Base class for tab content with a scrollable area."""

    def __init__(self, master: tk.Widget, **kwargs):
        super().__init__(master, **kwargs)

        # Note: Do not call self.grid() here as the parent (notebook) manages layout

        # Grid: content, status, notification
        self.columnconfigure(0, weight=1)  # Canvas column - expands
        self.columnconfigure(1, weight=0)  # Scrollbar column - fixed width
        self.rowconfigure(0, weight=1)  # Content row - expands
        self.rowconfigure(1, weight=0)  # Status row - fixed height
        self.rowconfigure(2, weight=0)  # Notification row - fixed height

        # Canvas + scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Scrollable inner frame
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.columnconfigure(0, weight=1)

        # Update scroll region when inner frame changes
        def _update_region(event=None):
            try:
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            except Exception:
                pass

        self.scrollable_frame.bind("<Configure>", _update_region)

        # Create window and keep width synced to canvas
        self._canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def _sync_width(event=None):
            try:
                # Force update to get accurate measurements
                self.canvas.update_idletasks()
                canvas_width = max(1, self.canvas.winfo_width())

                # Account for scrollbar width only when it's actually taking up space
                if self.scrollbar.winfo_ismapped() and self.scrollbar.winfo_width() > 0:
                    canvas_width = max(1, canvas_width - self.scrollbar.winfo_width())

                # Update the canvas item width
                self.canvas.itemconfigure(self._canvas_window, width=canvas_width)

                # Also update the scrollable frame width to match
                self.scrollable_frame.configure(width=canvas_width)

                # Update all child frames to use the full width
                self._update_child_frames_width(canvas_width)
            except Exception:
                pass

        self.canvas.bind("<Configure>", _sync_width)

        # Force initial update after widget is mapped
        def _initial_update():
            try:
                self.canvas.update_idletasks()
                _sync_width()
                _update_region()
            except Exception:
                pass

        self.bind("<Map>", lambda e: self.after_idle(_initial_update))

        # Layout scroll area
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Mouse wheel support (best effort across platforms)
        def _on_mousewheel(event):
            delta = 1
            if getattr(event, "delta", 0) != 0:
                delta = -1 if event.delta > 0 else 1
            elif getattr(event, "num", 0) in (4, 5):
                delta = -1 if event.num == 4 else 1
            self.canvas.yview_scroll(delta, "units")

        for widget in (self.canvas, self.scrollable_frame):
            try:
                widget.bind("<MouseWheel>", _on_mousewheel)
                widget.bind("<Button-4>", _on_mousewheel)
                widget.bind("<Button-5>", _on_mousewheel)
            except Exception:
                pass

        # Status + notification
        status_frame = ttk.Frame(self)
        status_frame.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=SPACING["md"],
            pady=SPACING["md"],
        )
        status_frame.columnconfigure(0, weight=1)
        self.status_indicator = StatusIndicator(status_frame)
        self.status_indicator.grid(row=0, column=0, sticky="ew")

        self.notification_panel = NotificationPanel(self)
        self.notification_panel.grid(row=2, column=0, columnspan=2, sticky="ew")

        # Simple destroy hook
        self.bind("<Destroy>", lambda e: None)

    def _update_child_frames_width(self, width):
        """Recursively update child frame widths."""
        try:
            for child in self.scrollable_frame.winfo_children():
                if isinstance(child, (ttk.Frame, tk.Frame)):
                    child.configure(width=width)
                    # Propagate to grandchildren
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, (ttk.Frame, tk.Frame)):
                            grandchild.configure(width=width)
        except Exception:
            pass

    def set_status(self, state: str, message: Optional[str] = None) -> None:
        self.status_indicator.set_status(state, message)

    def show_notification(
        self,
        message: str,
        level: str = "info",
        auto_hide: int = 5000,
        actions: Optional[List[Tuple[str, Callable]]] = None,
    ) -> None:
        self.notification_panel.show_notification(message, level, auto_hide, actions)
