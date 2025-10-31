"""
Core functionality for PhotoFilter application.
"""


# Lazy imports to avoid heavy torch dependencies at module level
def get_photo_organizer():
    from .recognition import PhotoOrganizer

    return PhotoOrganizer


def get_deduplication_engine():
    from .deduplication import DeduplicationEngine

    return DeduplicationEngine


def get_available_detectors():
    from .detectors import AVAILABLE_DETECTORS

    return AVAILABLE_DETECTORS


__all__ = ["get_photo_organizer", "get_deduplication_engine", "get_available_detectors"]
