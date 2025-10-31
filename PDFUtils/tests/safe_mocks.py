"""
Mock implementations for tkinter variables that prevent memory leaks.
This module provides leak-free mock implementations of tkinter variables
for use in tests.
"""

from unittest import mock


class SafeMockVariable:
    """Memory-efficient mock implementation of tkinter variables."""

    def __init__(self, value=None, **kwargs):
        """Initialize with a default value."""
        # Store the value directly without complex processing
        self._value = value

        # Empty trace callbacks - won't be called in tests
        self._trace_callbacks = {}

    def get(self):
        """Return the stored value."""
        return self._value

    def set(self, value):
        """Set the stored value."""
        self._value = value

    def trace(self, mode, callback):
        """Store callback but don't actually call it."""
        return "dummy_trace_id"

    def trace_add(self, mode, callback):
        """Store callback but don't actually call it."""
        return "dummy_trace_id"

    def trace_remove(self, mode, trace_id):
        """Remove callback (no-op)."""
        pass

    def cleanup(self):
        """Explicitly clean up any resources."""
        self._value = None
        self._trace_callbacks.clear()


class SafeMockStringVar(SafeMockVariable):
    """String variable that doesn't leak memory."""

    def __init__(self, value="", **kwargs):
        super().__init__(value if value is not None else "", **kwargs)

    def get(self):
        """Return string value."""
        return str(self._value) if self._value is not None else ""


class SafeMockIntVar(SafeMockVariable):
    """Int variable that doesn't leak memory."""

    def __init__(self, value=0, **kwargs):
        super().__init__(int(value) if value is not None else 0, **kwargs)

    def get(self):
        """Return int value."""
        return int(self._value) if self._value is not None else 0


class SafeMockDoubleVar(SafeMockVariable):
    """Double variable that doesn't leak memory."""

    def __init__(self, value=0.0, **kwargs):
        super().__init__(float(value) if value is not None else 0.0, **kwargs)

    def get(self):
        """Return float value."""
        return float(self._value) if self._value is not None else 0.0


class SafeMockBooleanVar(SafeMockVariable):
    """Boolean variable that doesn't leak memory."""

    def __init__(self, value=False, **kwargs):
        super().__init__(bool(value) if value is not None else False, **kwargs)

    def get(self):
        """Return boolean value."""
        return bool(self._value) if self._value is not None else False


def patch_tkinter_variables():
    """Patch tkinter variable classes with our memory-safe versions."""
    patches = [
        mock.patch("tkinter.StringVar", SafeMockStringVar),
        mock.patch("tkinter.IntVar", SafeMockIntVar),
        mock.patch("tkinter.DoubleVar", SafeMockDoubleVar),
        mock.patch("tkinter.BooleanVar", SafeMockBooleanVar),
        mock.patch("tkinter.Variable", SafeMockVariable),
    ]

    for p in patches:
        p.start()

    return patches


def cleanup_mock_variables(mock_vars):
    """Clean up a list of mock variables."""
    if not mock_vars:
        return

    for var in mock_vars:
        if hasattr(var, "cleanup"):
            var.cleanup()

    # Clear the list and force garbage collection
    mock_vars.clear()


def cleanup_tkinter_instance(instance):
    """Clean up a tkinter widget instance to prevent memory leaks.

    This function thoroughly cleans up a tkinter widget by:
    1. Destroying all children
    2. Resetting all tkinter variables
    3. Breaking circular references
    4. Unbinding all events

    Args:
        instance: The tkinter widget instance to clean up
    """
    if instance is None:
        return

    # Destroy all children first
    if hasattr(instance, "winfo_children"):
        for child in list(instance.winfo_children()):
            cleanup_tkinter_instance(child)

    # Clean up tkinter variables
    for attr_name in dir(instance):
        if attr_name.startswith("_"):
            continue

        attr = getattr(instance, attr_name)
        # Clean up tkinter variables
        if hasattr(attr, "set") and hasattr(attr, "get"):
            try:
                if hasattr(attr, "cleanup"):
                    attr.cleanup()
                elif isinstance(attr, mock.MagicMock):
                    pass  # Skip mocks
                else:
                    # Reset to default value
                    attr.set("")
            except Exception:
                pass

        # Break circular references
        if attr_name != "master" and not attr_name.startswith("_"):
            try:
                setattr(instance, attr_name, None)
            except (AttributeError, TypeError):
                pass

    # Unbind all events
    if hasattr(instance, "bind"):
        try:
            instance.bind("<Button>", "")
            instance.bind("<Configure>", "")
            instance.bind("<Key>", "")
            instance.bind("<Destroy>", "")
        except Exception:
            pass

    # Finally destroy the widget if possible
    if hasattr(instance, "destroy") and not isinstance(instance, mock.MagicMock):
        try:
            instance.destroy()
        except Exception:
            pass
