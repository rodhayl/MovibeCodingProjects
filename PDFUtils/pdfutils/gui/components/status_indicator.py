"""Minimal StatusIndicator keeping public API and tests behavior."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from .constants import SPACING


class StatusIndicator(ttk.Frame):
    """Status indicator with a message and optional activity animation."""

    STATES = {
        "idle": {"icon": "⚪", "color": "gray"},
        "ready": {"icon": "✓", "color": "green"},
        "working": {"icon": "⟳", "color": "blue"},
        "warning": {"icon": "⚠", "color": "orange"},
        "error": {"icon": "✗", "color": "red"},
        "success": {"icon": "✓", "color": "green"},
    }

    def __init__(self, master: tk.Widget, **kwargs):
        super().__init__(master, **kwargs)

        self.current_state = "idle"

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

        # Use tk.Label to allow foreground color setting if needed
        self.icon_label = tk.Label(self, text="", fg=self.STATES["idle"]["color"], font=("TkDefaultFont", 12))
        self.icon_label.grid(row=0, column=0, padx=(0, SPACING["sm"]))

        self.message_var = tk.StringVar(master=master, value="")
        self.message_label = ttk.Label(self, textvariable=self.message_var)
        self.message_label.grid(row=0, column=1, sticky="w")

        # Animation bookkeeping compatible with tests
        self._animation_running: bool = False
        self._animation_after_id = None
        self._anim_frame_index = 0

    def set_status(self, state: str, message: Optional[str] = None):
        if state not in self.STATES:
            state = "idle"
        self.current_state = state
        info = self.STATES[state]
        self.icon_label.configure(text=info["icon"], fg=info["color"])
        if message is not None:
            self.message_var.set(message)
        if state == "working" and not self._animation_running:
            self._start_animation()
        elif state != "working" and self._animation_running:
            self._stop_animation()

    def _start_animation(self):
        self._animation_running = True
        self._anim_frame_index = 0
        self._animate()

    def _animate(self):
        if not self._animation_running:
            return
        # Simple animation by showing the working icon
        self._anim_frame_index += 1
        self.icon_label.configure(text=self.STATES["working"]["icon"])
        self._animation_after_id = self.after(300, self._animate)

    def _stop_animation(self):
        self._animation_running = False
        if self._animation_after_id:
            self.after_cancel(self._animation_after_id)
            self._animation_after_id = None
        # Restore static icon
        self.icon_label.configure(text=self.STATES[self.current_state]["icon"])
