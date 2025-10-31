"""Output file selector component for selecting output directories or files."""

from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import StringVar, filedialog, ttk
from typing import List, Optional, Tuple


class OutputFileSelector(ttk.Frame):
    """A component for selecting output files or directories."""

    def __init__(
        self,
        parent: ttk.Widget,
        file_types: Optional[List[Tuple[str, str]]] = None,  # Old parameter name
        title: str = "Select Output",
        initialdir: Optional[str] = None,
        filetypes: Optional[List[Tuple[str, str]]] = None,  # New parameter name
        textvariable: Optional[StringVar] = None,
        label_text: Optional[str] = None,  # Old parameter (not used)
        default_extension: str = ".pdf",  # Old parameter (not used)
        **kwargs,
    ) -> None:
        """Initialize the OutputFileSelector.

        Args:
            parent: Parent widget
            file_types: List of (label, pattern) tuples for file filtering (old parameter)
            title: Title for file dialogs
            initialdir: Initial directory for file dialogs
            filetypes: List of (label, pattern) tuples for file filtering (new parameter)
            textvariable: StringVar to bind to the entry field
            label_text: Label text (old parameter, not used)
            default_extension: Default file extension (old parameter, not used)
            **kwargs: Additional arguments to pass to ttk.Frame
        """
        # Handle backward compatibility for parameter names
        if file_types is not None:
            filetypes = file_types

        super().__init__(parent, **kwargs)

        self.title = title
        self.initialdir = initialdir or str(Path.home())
        self.filetypes = filetypes or [("All files", "*")]
        self._disabled = False

        # Create a variable to hold the current path
        self._path_var = textvariable if textvariable is not None else StringVar()

        # Configure grid
        self.columnconfigure(1, weight=1)

        # Create widgets
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create and layout the widgets."""
        # Create entry
        self.entry = ttk.Entry(self, textvariable=self._path_var, width=40)
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Set initial state
        self._update_entry_state()

        # Store the current path
        self._current_path = ""

        # Browse button
        self.browse_button = ttk.Button(self, text="Browse...", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, sticky="e", padx=(0, 5))

        # Context menu
        self._setup_context_menu()

        # Bind right-click for context menu
        self.entry.bind("<Button-3>", self._show_context_menu)

        # Enable drag and drop
        self._setup_drag_and_drop()

    def _setup_context_menu(self) -> None:
        """Set up the context menu for the entry."""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Clear", command=lambda: self.set_output_path(""))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy Path", command=self._copy_to_clipboard)

        # Bind right-click to show context menu
        if hasattr(self, "entry") and self.entry:
            self.entry.bind("<Button-3>", self._show_context_menu)

    def _clear_path(self) -> None:
        """Clear the current path."""
        # Clear the path variable if it exists
        if hasattr(self, "_path_var") and self._path_var is not None:
            self._path_var.set("")

        # Clear the entry widget if it exists
        if hasattr(self, "entry") and self.entry:
            current_state = self.entry["state"]
            self.entry.config(state="normal")
            self.entry.delete(0, "end")
            self.entry.config(state=current_state)

        # Clear any stored path
        if hasattr(self, "_current_path"):
            self._current_path = ""

        # Update the entry state
        if hasattr(self, "_update_entry_state"):
            self._update_entry_state()

    def _update_entry_state(self) -> None:
        """Update the entry state based on the current disabled state."""
        if hasattr(self, "entry") and self.entry:
            if self._disabled:
                self.entry.config(state="disabled")
            else:
                # If we have a path variable, make it readonly, otherwise normal
                state = "readonly" if hasattr(self, "_path_var") and self._path_var else "normal"
                self.entry.config(state=state)

    def _setup_drag_and_drop(self) -> None:
        """Set up drag and drop functionality.

        Note: This is a simplified implementation that works on Windows.
        For full cross-platform drag and drop support, consider using a more
        robust solution like tkinterdnd2 or a custom implementation.
        """
        try:
            # Try to import tkinterdnd2 if available
            from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore[import-not-found]  # noqa: F401

            # If we get here, tkinterdnd2 is available
            self.entry.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
            self.entry.dnd_bind("<<Drop>>", self._on_drop)  # type: ignore[attr-defined]

        except ImportError:
            # Fall back to a basic implementation that handles Windows file paths
            def on_drop(event):
                """Handle drop event (Windows-specific)."""
                try:
                    # Get the dropped text (Windows provides file paths as text)
                    data = event.data
                    if not data:
                        return

                    # Clean up the path (remove curly braces and quotes)
                    path = data.strip("{}").replace('"', "")
                    if path:
                        self.set_output_path(path)
                except Exception as e:
                    print(f"Error handling drop event: {e}")

            # Bind the drop event
            self.entry.bind("<<Paste>>", on_drop)

            # Also handle direct text entry
            self.entry.bind("<Control-v>", on_drop)

    def _on_drop(self, event):
        """Handle drop event for tkinterdnd2."""
        try:
            # Get the dropped data
            data = event.data
            if not data:
                return

            # Handle different data formats
            if isinstance(data, dict) and "text/uri-list" in data:
                # Handle file URI from file manager
                uri = data["text/uri-list"]
                if uri.startswith("file://"):
                    # Remove 'file://' prefix and any trailing whitespace or newlines
                    path = uri[7:].strip()
                    # Take only the first path if multiple
                    path = path.split("\n", 1)[0]
                    # Remove any URL encoding
                    path = path.replace("%20", " ")
                    # Normalize path
                    # Fix for Windows drive letter paths with leading slash (e.g., /C:/...)
                    if path.startswith("/") and len(path) > 2 and path[2] == ":":
                        path = path[1:]
                    path = os.path.normpath(path)
                    path = path.replace("\\", "/")
                    self.set_output_path(path)
                    return

            # Handle direct path string (fallback)
            if isinstance(data, str):
                # Check if it's a JSON string
                if data.strip().startswith("{") and "text/uri-list" in data:
                    try:
                        import json

                        json_data = json.loads(data)
                        if "text/uri-list" in json_data:
                            uri = json_data["text/uri-list"]
                            if uri.startswith("file://"):
                                path = uri[7:].strip().split("\n", 1)[0].replace("%20", " ")
                                path = os.path.normpath(path)
                                if path.startswith("/") and len(path) > 2 and path[2] == ":":
                                    path = path[1:]
                                path = path.replace("\\", "/")
                                self.set_output_path(path)
                                return
                    except json.JSONDecodeError:
                        pass

                # Clean up the path (remove curly braces, quotes, and URL encoding)
                path = data.strip("{}").replace('"', "").replace("%20", " ")
                if path.startswith("file://"):
                    path = path[7:]
                if path:
                    path = os.path.normpath(path)
                    if path.startswith("/") and len(path) > 2 and path[2] == ":":
                        path = path[1:]
                    path = path.replace("\\", "/")
                    self.set_output_path(path)
        except Exception as e:
            print(f"Error handling drop event: {e}")
            import traceback

            traceback.print_exc()

    def _show_context_menu(self, event: tk.Event) -> None:
        """Show the context menu."""
        if hasattr(self, "context_menu"):
            try:
                # Update the state of menu items based on current state
                if hasattr(self, "entry") and self.entry:
                    has_text = bool(self.entry.get())
                    self.context_menu.entryconfig(0, state="normal" if has_text else "disabled")  # Clear
                    self.context_menu.entryconfig(2, state="normal" if has_text else "disabled")  # Copy Path

                # Show the context menu
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def _copy_to_clipboard(self) -> None:
        """Copy the current path to the clipboard."""
        path = self.get_output_path()
        if path:
            self.clipboard_clear()
            self.clipboard_append(path)

    def browse_file(self) -> None:
        """Open a file dialog to select an output file."""
        # Get the initial directory
        initial_dir = self.initialdir
        current_path = self.get_output_path()
        if current_path and os.path.exists(os.path.dirname(current_path)):
            initial_dir = os.path.dirname(current_path)

        # Determine the default extension
        default_ext = ""  # Default to no extension
        if self.filetypes and len(self.filetypes) > 0 and len(self.filetypes[0]) > 1:
            # Extract extension from the first filetype pattern (e.g., "*.pdf" -> ".pdf")
            pattern = self.filetypes[0][1]
            if pattern.startswith("*") and pattern != "*":
                default_ext = pattern[1:]

        # Open the file dialog
        file_path = filedialog.asksaveasfilename(
            title=self.title,
            defaultextension=default_ext,
            filetypes=self.filetypes,
            initialdir=initial_dir,
        )

        # Update the path if a file was selected
        if file_path:
            # Ensure the path has the correct extension
            if not file_path.lower().endswith(default_ext.lower()):
                file_path += default_ext
            self.set_output_path(file_path)

    def browse_directory(self) -> None:
        """Open a directory dialog to select an output directory."""
        # Get the initial directory
        initial_dir = self.initialdir
        current_path = self.get_output_path()
        if current_path and os.path.exists(os.path.dirname(current_path)):
            initial_dir = os.path.dirname(current_path)

        # Open the directory dialog
        dir_path = filedialog.askdirectory(title=self.title, initialdir=initial_dir)

        # Update the path if a directory was selected
        if dir_path:
            self.set_output_path(dir_path)

    def set_output_path(self, path: str) -> None:
        """Set the output path.

        Args:
            path: Path to the output file or directory
        """
        if path:
            # Normalize the path
            path = os.path.normpath(path)

            # Update the entry
            if hasattr(self, "_path_var") and self._path_var is not None:
                self._path_var.set(path)

            # Update the entry's text
            if hasattr(self, "entry") and self.entry:
                current_state = self.entry["state"]
                self.entry.config(state="normal")
                self.entry.delete(0, "end")
                self.entry.insert(0, path)
                self.entry.config(state=current_state)
        else:
            # Clear the path
            if hasattr(self, "_path_var") and self._path_var is not None:
                self._path_var.set("")
            if hasattr(self, "entry") and self.entry:
                current_state = self.entry["state"]
                self.entry.config(state="normal")
                self.entry.delete(0, "end")
                self.entry.config(state=current_state)

        # Update the entry state
        if hasattr(self, "_update_entry_state"):
            self._update_entry_state()

    def get_output_path(self) -> str:
        """Get the current output path.

        Returns:
            The current output path as a string
        """
        return self._path_var.get()

    def get_path(self) -> str:
        """Get the current output path (alias for backward compatibility).

        Returns:
            The current output path as a string
        """
        return self.get_output_path()

    def set_path(self, path: str) -> None:
        """Set the output path (alias for backward compatibility).

        Args:
            path: Path to the output file or directory
        """
        self.set_output_path(path)

    def has_path(self) -> bool:
        """Check if a path has been selected.

        Returns:
            True if a path has been selected, False otherwise
        """
        return bool(self.get_output_path())

    def clear(self) -> None:
        """Clear the current selection."""
        self.set_output_path("")

    def disable(self) -> None:
        """Disable the component."""
        self._disabled = True
        if hasattr(self, "browse_button") and self.browse_button:
            self.browse_button.config(state="disabled")
        if hasattr(self, "dir_button") and self.dir_button:
            self.dir_button.config(state="disabled")
        self._update_entry_state()

    def enable(self) -> None:
        """Enable the component."""
        self._disabled = False
        if hasattr(self, "browse_button") and self.browse_button:
            self.browse_button.config(state="normal")
        if hasattr(self, "dir_button") and self.dir_button:
            self.dir_button.config(state="normal")
        self._update_entry_state()

    def set_initial_dir(self, directory: str) -> None:
        """Set the initial directory for file dialogs.

        Args:
            directory: Path to the initial directory
        """
        self.initialdir = str(directory) if directory else str(Path.home())

    def validate_path(self) -> bool:
        """Validate the current path.

        Returns:
            True if the path is valid, False otherwise
        """
        path = self.get_output_path()
        if not path:
            return False

        # Check if the parent directory exists
        parent_dir = os.path.dirname(path)
        if not parent_dir:  # If it's just a filename with no path
            parent_dir = "."

        return os.path.isdir(parent_dir)

    def path_exists(self) -> bool:
        """Check if the current path exists.

        Returns:
            True if the path exists, False otherwise
        """
        path = self.get_output_path()
        return bool(path) and os.path.exists(path)
