#!/usr/bin/env python3
"""
Test script for the DeduplicationEngine class using imagehash for deduplication.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the 'src' directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from photofilter.core.deduplication import DeduplicationEngine, DuplicateGroup


def print_duplicate_groups(groups: List[DuplicateGroup]) -> None:
    """Print duplicate groups in a readable format."""
    if not groups:
        print("No duplicates found.")
        return

    print(f"\nFound {len(groups)} duplicate groups:")
    print("=" * 80)

    for i, group in enumerate(groups, 1):
        print(
            f"\nGroup {i} (similarity: {group.similarity_score:.2f}, "
            f"type: {group.duplicate_type}, "
            f"size savings: {group.size_savings/1024/1024:.2f} MB):"
        )

        for j, file_path in enumerate(group.files, 1):
            prefix = (
                "  [KEEP] "
                if j == 1 and group.recommended_action == "keep_best_quality"
                else "  [DUP]  "
            )
            print(f"{prefix}{file_path} ({file_path.stat().st_size/1024:.1f} KB)")


class TestDeduplication:
    """Test class for deduplication functionality."""
    def setup_method(self):
        """Initialize engine and default state for pytest compatibility."""
        self.directory = None
        self.engine = DeduplicationEngine(threshold=0.85)
        self.engine.check_filenames = True
        self.engine.check_filesizes = True
        self.engine.check_metadata = False
        self.engine.check_visual_similarity = True
        self.duplicates = []
        self.stats = {}

    def run(self):
        """Run the deduplication test."""
        print(f"Searching for duplicate images in: {self.directory}")
        print(f"Using similarity threshold: {self.engine.similarity_threshold}")

        # Set up progress callback
        def progress_callback(current: int, total: int, filename: str) -> None:
            percent = int((current / total) * 100) if total > 0 else 0
            print(f"\rProgress: {percent}% - {filename}", end="", flush=True)

        self.engine.progress_callback = progress_callback

        # Find duplicates
        print("\nStarting duplicate detection...")
        start_time = time.time()
        self.duplicates = self.engine.find_duplicates([self.directory])
        elapsed = time.time() - start_time

        # Get statistics
        self.stats = self.engine.get_stats()
        self.stats["elapsed_time"] = elapsed

        return self.duplicates

    def print_results(self):
        """Print the results of the deduplication."""
        print("\n" + "=" * 80)
        print("DUPLICATE DETECTION COMPLETE")
        print("=" * 80)

        if not self.duplicates:
            print("\nNo duplicates found!")
            return

        # Print statistics
        print(f"\nStatistics:")
        print(f"- Total files analyzed: {self.stats.get('total_files', 0)}")
        print(f"- Duplicate groups found: {self.stats.get('duplicate_groups', 0)}")
        print(f"- Total duplicate files: {self.stats.get('duplicate_count', 0)}")
        print(
            f"- Potential space savings: {self.stats.get('potential_savings_mb', 0):.2f} MB"
        )
        print(f"- Processing time: {self.stats.get('elapsed_time', 0):.2f} seconds")

        # Print duplicate groups
        print_duplicate_groups(self.duplicates)


def main():
    try:
        # Check if directory path is provided
        if len(sys.argv) < 2:
            print("Usage: python test_dedup.py <directory_path>")
            return

        directory = Path(sys.argv[1])

        if not directory.exists() or not directory.is_dir():
            print(
                f"Error: Directory '{directory}' does not exist or is not a directory"
            )
            return

        # Run the test
        test = TestDeduplication()
        test.setup_method()
        test.directory = directory
        test.run()
        test.print_results()

        # Ask user if they want to remove duplicates
        if test.duplicates:
            print("\n" + "-" * 80)
            choice = (
                input("\nDo you want to remove the duplicate files? (y/N): ")
                .strip()
                .lower()
            )
            if choice == "y":
                print("\nRemoving duplicates...")
                removed_count = 0
                for group in test.duplicates:
                    # Keep the first file in each group, remove the rest
                    for dup_file in group.files[1:]:
                        try:
                            dup_file.unlink()
                            print(f"Removed: {dup_file}")
                            removed_count += 1
                        except Exception as e:
                            print(f"Error removing {dup_file}: {e}")
                print(f"\nRemoved {removed_count} duplicate files.")

        print("\nTest complete!")

    except ImportError as e:
        print(f"\nError: {e}")
        print("Please install the required dependencies with:")
        print("pip install Pillow imagehash")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
