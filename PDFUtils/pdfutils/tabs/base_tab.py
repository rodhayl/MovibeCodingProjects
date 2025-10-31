"""Base class for all tab implementations in PDFUtils."""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Any, Callable, Optional

from ..gui.components import TabContentFrame

logger = logging.getLogger(__name__)


class BaseTab(TabContentFrame):
    """Base class for all tab implementations.

    This class provides common functionality and interface that all tabs should implement.
    It inherits from TabContentFrame to provide the scrolling UI container functionality.
    """

    def __init__(self, master: tk.Widget, app: Any):
        """Initialize the base tab.

        Args:
            master: The parent widget for this tab.
            app: Reference to the main application instance.
        """
        # Initialize the TabContentFrame (UI container)
        TabContentFrame.__init__(self, master)

        # Store app reference
        self.app = app

        # Setup UI (to be overridden by subclasses)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface for this tab.

        Subclasses should override this method to create their specific UI elements.
        """
        pass

    def show_notification(self, message: str, level: str = "info") -> None:
        """Show a notification to the user.

        Args:
            message: The message to display.
            level: The severity level ('info', 'warning', 'error').
        """
        self.notification_panel.show_notification(message, level)

    def set_status(self, state: str, message: Optional[str] = None) -> None:
        """Set the status indicator state and message.

        Args:
            state: Status state ('idle', 'ready', 'working', 'warning', 'error', 'success')
            message: Optional status message
        """
        self.status_indicator.set_status(state, message)

    def on_tab_activated(self) -> None:
        """Called when this tab is activated.

        Subclasses can override this to perform actions when the tab is activated.
        """
        pass

    def on_tab_deactivated(self) -> None:
        """Called when this tab is deactivated.

        Subclasses can override this to perform cleanup when the tab is deactivated.
        """
        pass


class WorkerTab(BaseTab):
    """Enhanced base class for tabs that perform background operations.

    This class provides common functionality for tabs that use threading to perform
    background operations while updating UI state and progress.
    """

    def __init__(self, master: tk.Widget, app: Any):
        """Initialize the worker tab.

        Args:
            master: The parent widget for this tab.
            app: Reference to the main application instance.
        """
        super().__init__(master, app)
        self.action_button = None  # Reference to the main action button

    def _set_ui_state(self, *, disabled: bool):
        """Set the UI state (enabled/disabled) for interactive elements.

        Args:
            disabled: If True, disable UI elements; if False, enable them.
        """
        state = tk.DISABLED if disabled else tk.NORMAL
        if self.action_button:
            self.action_button.config(state=state)

    def _run_worker(
        self,
        worker_func: Callable,
        success_message: str = "Operation completed successfully",
    ):
        """Run a worker function in a background thread.

        Args:
            worker_func: The function to run in the background thread.
            success_message: Message to display on successful completion.
        """

        def worker():
            try:
                worker_func()
                self.set_status("success", "Done")
                messagebox.showinfo("Success", success_message)
            except Exception as exc:
                logger.exception("Operation failed")
                self.set_status("error", f"Failed: {exc}")
                messagebox.showerror("Error", f"Operation failed: {exc}")
            finally:
                self._set_ui_state(disabled=False)

        self._set_ui_state(disabled=True)
        self.set_status("working", "Processing...")

        threading.Thread(target=worker, daemon=True).start()
