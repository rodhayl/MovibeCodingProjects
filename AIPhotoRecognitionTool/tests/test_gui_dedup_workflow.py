#!/usr/bin/env python3
"""
End-to-end test for the deduplication workflow with GUI settings.
"""

import sys
import os
import unittest
import shutil
import tempfile
from pathlib import Path
import logging

# Add the 'src' directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from photofilter.core.deduplication import DeduplicationEngine
except ImportError as e:
    print(f"Error importing DeduplicationEngine: {e}")
    raise

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestGUIDeduplicationWorkflow(unittest.TestCase):
    """Test the deduplication workflow with GUI settings."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Create test directories
        cls.base_dir = Path(tempfile.mkdtemp(prefix="dedup_test_"))
        cls.source_dir = cls.base_dir / "source"
        cls.output_dir = cls.base_dir / "output"

        # Create test files
        cls.setup_test_files()

        # GUI settings
        cls.settings = {
            "dedup_threshold": 0.85,
            "source_folder": str(cls.source_dir),
            "output_folder": str(cls.output_dir),
            "dedup_check_filenames": True,
            "dedup_check_filesizes": True,
            "dedup_check_metadata": False,
            "dedup_check_visual": False,
            "dedup_action": "move_organize",
        }

        # Initialize engine with threshold parameter
        cls.engine = DeduplicationEngine(threshold=cls.settings["dedup_threshold"])
        cls.engine.check_filenames = cls.settings["dedup_check_filenames"]
        cls.engine.check_filesizes = cls.settings["dedup_check_filesizes"]
        cls.engine.check_metadata = cls.settings["dedup_check_metadata"]
        cls.engine.check_visual_similarity = cls.settings["dedup_check_visual"]

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after all tests."""
        if hasattr(cls, "base_dir") and cls.base_dir.exists():
            shutil.rmtree(cls.base_dir)

    @classmethod
    def setup_test_files(cls):
        """Create test files for deduplication."""
        cls.source_dir.mkdir(exist_ok=True, parents=True)
        test_files = [
            ("test1.jpg", b"test content 1"),
            ("test1_copy.jpg", b"test content 1"),  # Exact duplicate
            ("test2.jpg", b"test content 2"),
            ("unique.jpg", b"unique content"),  # Unique file
        ]
        for filename, content in test_files:
            with open(cls.source_dir / filename, "wb") as f:
                f.write(content)

    def test_deduplication_workflow(self):
        """Test the complete deduplication workflow."""
        # Find duplicates
        groups = self.engine.find_duplicates([self.source_dir])
        self.assertGreater(len(groups), 0, "Should find duplicate groups")

        # Perform deduplication
        stats = self.engine.remove_duplicates(
            groups,
            action=self.settings["dedup_action"],
            output_folder=Path(self.settings["output_folder"]),
        )

        # Verify results
        self._verify_deduplication_results()

    def _verify_deduplication_results(self):
        """Verify that files were moved as expected."""
        original_folder = Path(self.settings["output_folder"]) / "original"
        duplicates_folder = Path(self.settings["output_folder"]) / "duplicated"

        self.assertTrue(original_folder.exists(), "Original folder should exist")
        self.assertTrue(duplicates_folder.exists(), "Duplicates folder should exist")

        # Check that duplicates were moved
        self.assertTrue(
            (duplicates_folder / "test1_copy.jpg").exists(),
            "Duplicate file should be in duplicates folder",
        )

        # Check that original is in source or original folder
        original_in_source = (self.source_dir / "test1.jpg").exists()
        original_in_original = (original_folder / "test1.jpg").exists()
        self.assertTrue(
            original_in_source or original_in_original,
            "Original file should be in source or original folder",
        )


if __name__ == "__main__":
    unittest.main()
