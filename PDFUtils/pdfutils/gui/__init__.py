"""Wrapper package for GUI components.

This module provides access to the modern GUI components that have replaced
the legacy gui.py module.
"""

# Import modern GUI components
from .components import FileSelector, OutputFileSelector

__all__ = ["FileSelector", "OutputFileSelector"]
