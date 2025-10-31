"""
PhotoFilter - AI-powered photo organization system.

A comprehensive tool for photo recognition, deduplication, and organization
using advanced machine learning models and computer vision techniques.
"""

__version__ = "1.0.0"
__author__ = "PhotoFilter Development Team"

# Lazy imports to avoid circular dependencies and heavy torch loading
__version__ = "1.0.0"
__author__ = "PhotoFilter Development Team"


def get_photo_organizer():
    """Lazy import PhotoOrganizer to avoid heavy dependencies at package level."""
    from .core.recognition import PhotoOrganizer

    return PhotoOrganizer


def get_deduplication_engine():
    """Lazy import DeduplicationEngine to avoid heavy dependencies at package level."""
    from .core.deduplication import DeduplicationEngine

    return DeduplicationEngine


def get_gui():
    """Lazy import GUI to avoid heavy dependencies at package level."""
    from .gui.main_window import PhotoRecognitionGUI

    return PhotoRecognitionGUI


__all__ = ["get_photo_organizer", "get_deduplication_engine", "get_gui"]
