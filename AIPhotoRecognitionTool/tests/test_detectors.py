"""
Unit tests for photofilter.core.detectors.YOLOv5Detector focused on:
- get_info() content
- initialize_model() graceful failure when core dependencies (torch) are missing
"""

import sys
import logging
from pathlib import Path

# Ensure src/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from photofilter.core.detectors import YOLOv5Detector
import photofilter.core.detectors as detectors_module


class TestYOLOv5Detector:
    def test_get_info_returns_expected_values(self):
        """get_info should reflect the model size configuration accurately."""
        det = YOLOv5Detector(model_size="s")
        info = det.get_info()

        # Expected keys
        for key in ("name", "description", "accuracy", "speed", "memory"):
            assert key in info

        # Expected values for 's' as defined in detectors.YOLOv5Detector.model_configs
        assert info["name"] == "YOLOv5S"
        assert info["description"] == "Small - Balanced speed/accuracy"
        assert info["accuracy"] == "⭐⭐⭐⭐"
        assert info["speed"] == "⭐⭐⭐⭐"
        assert info["memory"] == "⭐⭐⭐⭐"

    def test_initialize_model_without_torch_returns_false_and_logs_error(self, monkeypatch, caplog):
        """initialize_model should return False and log an error when torch is unavailable."""
        # Remove 'torch' from module namespace to simulate missing dependency
        monkeypatch.delattr(detectors_module, "torch", raising=False)

        det = YOLOv5Detector(model_size="n")
        with caplog.at_level(logging.ERROR):
            ok = det.initialize_model()

        assert ok is False
        # Ensure an error about initialization failure was logged
        assert any(
            "Failed to initialize YOLOv5" in rec.getMessage() for rec in caplog.records
        )
