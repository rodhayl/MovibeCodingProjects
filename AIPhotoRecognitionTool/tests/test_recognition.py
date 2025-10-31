"""
Test cases for photo recognition functionality.
"""

import pytest
import sys
from pathlib import Path
import tempfile
import shutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from photofilter.core.recognition import PhotoOrganizer, YOLOv5Detector


class TestPhotoRecognition:
    """Test cases for photo recognition core functionality."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_input = Path(self.temp_dir) / "input"
        self.test_output = Path(self.temp_dir) / "output"
        self.test_input.mkdir()
        self.test_output.mkdir()

    def teardown_method(self):
        """Clean up test environment after each test."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_photo_organizer_init(self):
        """Test PhotoOrganizer initialization."""
        organizer = PhotoOrganizer(
            input_folder=str(self.test_input), output_folder=str(self.test_output)
        )
        assert organizer.input_folder == str(self.test_input)
        assert organizer.output_folder == str(self.test_output)

    def test_yolov5_detector_init(self):
        """Test YOLOv5Detector initialization."""
        try:
            detector = YOLOv5Detector()
            assert detector is not None
        except Exception as e:
            pytest.skip(f"YOLOv5 dependencies not available: {e}")

    def test_supported_extensions(self):
        """Test that supported image extensions are properly defined."""
        organizer = PhotoOrganizer(
            input_folder=str(self.test_input), output_folder=str(self.test_output)
        )
        # Should have common image extensions
        expected_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
        assert any(ext in organizer.supported_extensions for ext in expected_extensions)


if __name__ == "__main__":
    pytest.main([__file__])
