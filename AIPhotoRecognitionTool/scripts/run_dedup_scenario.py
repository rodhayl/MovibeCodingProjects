#!/usr/bin/env python3
"""
Run deduplication on the specified folders with GUI settings.
"""

import sys
import os
import time
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("deduplication_run.log")],
)
logger = logging.getLogger(__name__)

# Add the 'src' directory to the Python path (src-layout)
sys.path.insert(0, str((Path(__file__).parent.parent) / "src"))

try:
    from photofilter.core.deduplication import DeduplicationEngine
except ImportError as e:
    logger.error(f"Failed to import DeduplicationEngine: {e}")
    sys.exit(1)


def run_dedup_scenario():
    """Run deduplication with the specified GUI settings."""
    # Configuration matching the GUI settings
    config = {
        "source_folder": r"C:\\Users\\david\\Pictures\\ToProcess",
        "output_folder": r"C:\\Users\\david\\Pictures\\ToProcessDedup",
        "dedup_threshold": 0.85,
        "check_filenames": True,
        "check_filesizes": True,
        "check_metadata": False,
        "check_visual_similarity": False,
        "action": "move_organize",  # Options: 'preview_only', 'move_organize', 'move_to_folder'
        "move_folder": r"C:\\Users\\david\\Pictures\\Duplicates",  # Only used if action is 'move_to_folder'
    }

    logger.info("Starting deduplication with the following settings:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")

    # Initialize the deduplication engine
    try:
        engine = DeduplicationEngine(threshold=config["dedup_threshold"])

        # Configure the engine
        engine.check_filenames = config["check_filenames"]
        engine.check_filesizes = config["check_filesizes"]
        engine.check_metadata = config["check_metadata"]
        engine.check_visual_similarity = config["check_visual_similarity"]

        # Set up progress callback
        def progress_callback(current, total, filename):
            logger.info(f"Progress: {current}/{total} - Processing {filename}")

        engine.progress_callback = progress_callback

        # Find duplicates
        logger.info(f"Searching for duplicates in: {config['source_folder']}")
        source_path = Path(config["source_folder"])

        if not source_path.exists() or not source_path.is_dir():
            logger.error(
                f"Source folder does not exist or is not a directory: {source_path}"
            )
            return False

        # Create output directory if it doesn't exist
        output_path = Path(config["output_folder"])
        output_path.mkdir(parents=True, exist_ok=True)

        # Find duplicates
        start_time = time.time()
        groups = engine.find_duplicates([source_path])
        find_time = time.time() - start_time

        logger.info(f"Found {len(groups)} duplicate groups in {find_time:.2f} seconds")

        if not groups:
            logger.info("No duplicates found.")
            return True

        # Process duplicates
        logger.info(f"Processing duplicates with action: {config['action']}")
        start_time = time.time()

        # Ensure output folder exists and is writable
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            test_file = output_path / ".write_test"
            test_file.touch()
            test_file.unlink()
            logger.info(f"Output folder is writable: {output_path}")
        except Exception as e:
            logger.error(f"Cannot write to output folder {output_path}: {e}")
            return False

        # For move_organize, ensure we have the correct folder structure
        if config["action"] == "move_organize":
            original_folder = output_path / "original"
            duplicates_folder = output_path / "duplicated"
            try:
                original_folder.mkdir(exist_ok=True)
                duplicates_folder.mkdir(exist_ok=True)
                logger.info(
                    f"Created organized folder structure: {original_folder} and {duplicates_folder}"
                )
            except Exception as e:
                logger.error(f"Failed to create organized folders: {e}")
                return False

        # Process the groups with detailed logging
        try:
            logger.info(
                f"Starting to process {len(groups)} duplicate groups with action: {config['action']}"
            )
            logger.info(f"Output folder: {output_path}")

            # Log the first few groups for debugging
            for i, group in enumerate(groups[:3]):  # Log first 3 groups for debugging
                logger.info(f"Group {i+1}: {[str(f) for f in group.files]}")
            if len(groups) > 3:
                logger.info(f"... and {len(groups) - 3} more groups")

            stats = engine.remove_duplicates(
                groups, action=config["action"], output_folder=output_path
            )

            # Log the results of the operation
            logger.info(f"Duplicate processing completed. Stats: {stats}")

            # Verify files were moved
            if config["action"] == "move_organize":
                original_folder = output_path / "original"
                duplicates_folder = output_path / "duplicated"

                original_files = (
                    list(original_folder.glob("*")) if original_folder.exists() else []
                )
                duplicate_files = (
                    list(duplicates_folder.glob("*"))
                    if duplicates_folder.exists()
                    else []
                )

                logger.info(f"Files in 'original' folder: {len(original_files)}")
                logger.info(f"Files in 'duplicated' folder: {len(duplicate_files)}")

                if not original_files and not duplicate_files:
                    logger.warning("No files were moved to the output folders!")
                    # Try to diagnose why
                    logger.info("Checking source files...")
                    for group in groups[:5]:  # Check first 5 groups
                        for file_path in group.files:
                            exists = file_path.exists()
                            logger.info(f"Source file {file_path} exists: {exists}")
                            if not exists:
                                logger.warning(
                                    f"Source file does not exist: {file_path}"
                                )
        except Exception as e:
            logger.error(f"Error during duplicate processing: {e}", exc_info=True)
            return False

        process_time = time.time() - start_time

        # Log results with more details
        logger.info("\n" + "=" * 80)
        logger.info("DEDUPLICATION COMPLETED - SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Source folder: {config['source_folder']}")
        logger.info(f"Output folder: {config['output_folder']}")
        logger.info("-" * 40)

        # File statistics
        total_files = sum(len(group.files) for group in groups)
        total_duplicates = sum(len(group.files) - 1 for group in groups)
        unique_files = len(groups)

        logger.info(f"Total files analyzed: {engine.total_files_analyzed}")
        logger.info(f"Duplicate groups found: {len(groups)}")
        logger.info(f"Total files in groups: {total_files}")
        logger.info(f"Unique files: {unique_files}")
        logger.info(f"Total duplicates: {total_duplicates}")

        # Space savings
        space_saved = stats.get("space_saved", 0)
        space_mb = space_saved / (1024 * 1024)
        space_gb = space_mb / 1024

        logger.info("\nSPACE SAVINGS")
        logger.info("-" * 40)
        logger.info(f"Potential space saved: {space_mb:.2f} MB ({space_gb:.2f} GB)")

        # Performance metrics
        total_time = find_time + process_time
        files_per_second = (
            engine.total_files_analyzed / total_time if total_time > 0 else 0
        )

        logger.info("\nPERFORMANCE METRICS")
        logger.info("-" * 40)
        logger.info(f"Total processing time: {total_time:.2f} seconds")
        logger.info(f"Finding duplicates: {find_time:.2f} seconds")
        logger.info(f"Processing duplicates: {process_time:.2f} seconds")
        logger.info(f"Processing speed: {files_per_second:.2f} files/second")

        # Action taken
        logger.info("\nACTION TAKEN")
        logger.info("-" * 40)
        if config["action"] == "preview_only":
            logger.info("Preview mode: No files were modified")
        elif config["action"] == "move_organize":
            logger.info(f"Files were organized into: {config['output_folder']}")
        elif config["action"] == "move_to_folder":
            logger.info(f"Duplicates were moved to: {config['move_folder']}")

        # Detailed group information
        logger.info("\nDUPLICATE GROUPS")
        logger.info("-" * 40)
        for i, group in enumerate(groups, 1):
            group_size = len(group.files)
            file_size = group.files[0].stat().st_size if group.files else 0
            group_savings = (group_size - 1) * file_size

            logger.info(
                f"\nGroup {i}: {group_size} files, "
                f"{(group_size - 1) * file_size / (1024*1024):.2f} MB potential savings"
            )

            for j, file in enumerate(group.files, 1):
                status = "ORIGINAL" if j == 1 else "DUPLICATE"
                logger.info(f"  {status}: {file}")

        logger.info("\n" + "=" * 80)
        logger.info("Deduplication completed successfully!")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"Error during deduplication: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("Starting deduplication process...")
    success = run_dedup_scenario()
    if success:
        logger.info("Deduplication completed successfully!")
    else:
        logger.error("Deduplication failed!")
    logger.info("Check 'deduplication_run.log' for detailed logs.")
