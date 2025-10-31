#!/usr/bin/env python3
"""
Advanced Photo Deduplication Tool

This module provides comprehensive duplicate detection using multiple algorithms:
- File name similarity
- File size comparison
- Image metadata analysis
- Perceptual hashing (visual similarity)
- Content-based comparison

Designed to be integrated with the Photo Recognition GUI.
"""

import hashlib
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import json
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

# Core dependencies
try:
    from PIL import Image
    from PIL.ExifTags import TAGS

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    TAGS = {}

# Optional advanced dependencies
try:
    import imagehash

    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False

try:
    from difflib import SequenceMatcher

    DIFFLIB_AVAILABLE = True
except ImportError:
    DIFFLIB_AVAILABLE = False

# Image file extensions
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
    ".gif",
    ".ico",
}


@dataclass
class ImageMetadata:
    """Container for image metadata."""

    path: Path
    size: int  # File size in bytes
    dimensions: Optional[Tuple[int, int]]  # Width, height
    creation_date: Optional[datetime]
    modification_date: datetime
    camera_make: Optional[str]
    camera_model: Optional[str]
    focal_length: Optional[str]
    iso: Optional[str]
    exposure_time: Optional[str]
    f_number: Optional[str]
    flash: Optional[str]
    orientation: Optional[str]
    md5_hash: Optional[str]
    perceptual_hash: Optional[str]


@dataclass
class DuplicateGroup:
    """Container for a group of duplicate images."""

    similarity_score: float
    duplicate_type: str  # 'exact', 'similar', 'metadata', 'name'
    files: List[Path]
    recommended_action: str  # 'keep_first', 'keep_largest', 'manual_review'
    size_savings: int  # Bytes that would be saved by removing duplicates


class DeduplicationEngine:
    """Advanced photo deduplication engine with multiple detection algorithms."""

    def set_progress_callback(self, callback):
        """Set callback function for progress updates."""
        self.progress_callback = callback

    def cancel_operation(self):
        """Cancel the current deduplication operation."""
        self.cancel_flag = True

    def extract_metadata(
        self, image_path: Path, extract_md5=True, extract_exif=True, extract_visual=True
    ) -> Optional[ImageMetadata]:
        """Extract metadata from an image file with robust error handling and timeouts.

        Args:
            image_path: Path to the image file
            extract_md5: Whether to calculate MD5 hash (needed for exact content matching)
            extract_exif: Whether to extract EXIF metadata (needed for metadata comparison)
            extract_visual: Whether to calculate perceptual hash (needed for visual similarity)

        Returns:
            ImageMetadata object or None if extraction failed
        """

        def _safe_extract():
            try:
                # Get basic file stats first
                try:
                    stat = image_path.stat()
                except Exception as e:
                    logging.warning(f"Could not stat file {image_path}: {e}")
                    return None

                metadata = ImageMetadata(
                    path=image_path,
                    size=stat.st_size,
                    dimensions=None,
                    creation_date=None,
                    modification_date=datetime.fromtimestamp(stat.st_mtime),
                    camera_make=None,
                    camera_model=None,
                    focal_length=None,
                    iso=None,
                    exposure_time=None,
                    f_number=None,
                    flash=None,
                    orientation=None,
                    md5_hash=None,
                    perceptual_hash=None,
                )

                if not CORE_AVAILABLE:
                    return metadata

                # Calculate MD5 hash with timeout
                if extract_md5:
                    try:
                        with open(image_path, "rb") as f:
                            # Read file in chunks to handle large files
                            md5_hash = hashlib.md5()
                            for chunk in iter(lambda: f.read(8192), b""):
                                md5_hash.update(chunk)
                            metadata.md5_hash = md5_hash.hexdigest()
                    except Exception as e:
                        logging.warning(
                            f"Could not calculate MD5 for {image_path}: {e}"
                        )

                # Process image only if needed
                if extract_exif or extract_visual:
                    try:
                        # Use a timeout for the entire image processing

                        def process_image():
                            with Image.open(image_path) as img:
                                # Get dimensions
                                metadata.dimensions = img.size

                                # Extract EXIF data
                                if extract_exif and hasattr(img, "_getexif"):
                                    try:
                                        exif = img._getexif()
                                        if exif:
                                            for tag, value in exif.items():
                                                tag_name = TAGS.get(tag, tag)
                                                if tag_name == "Make":
                                                    metadata.camera_make = str(
                                                        value
                                                    ).strip()
                                                elif tag_name == "Model":
                                                    metadata.camera_model = str(
                                                        value
                                                    ).strip()
                                                elif tag_name == "FocalLength":
                                                    metadata.focal_length = str(value)
                                                elif tag_name == "ISOSpeedRatings":
                                                    metadata.iso = str(value)
                                                elif tag_name == "ExposureTime":
                                                    metadata.exposure_time = str(value)
                                                elif tag_name == "FNumber":
                                                    metadata.f_number = str(value)
                                                elif tag_name == "Flash":
                                                    metadata.flash = str(value)
                                                elif tag_name == "Orientation":
                                                    metadata.orientation = str(value)
                                                elif tag_name == "DateTime":
                                                    try:
                                                        metadata.creation_date = (
                                                            datetime.strptime(
                                                                str(value),
                                                                "%Y:%m:%d %H:%M:%S",
                                                            )
                                                        )
                                                    except (ValueError, TypeError):
                                                        pass
                                    except Exception as e:
                                        logging.debug(
                                            f"EXIF extraction failed for {image_path}: {e}"
                                        )

                                # Calculate perceptual hashes if needed
                                if extract_visual and IMAGEHASH_AVAILABLE:
                                    try:
                                        # Convert to RGB if necessary (faster than RGBA)
                                        if img.mode != "RGB":
                                            img = img.convert("RGB")

                                        # Use a single hash algorithm first to check if we can process the image
                                        phash = imagehash.phash(img)

                                        # Only calculate additional hashes if the first one succeeded
                                        dhash = imagehash.dhash(img)
                                        whash = imagehash.whash(img)
                                        metadata.perceptual_hash = (
                                            f"{phash}:{dhash}:{whash}"
                                        )

                                    except Exception as e:
                                        logging.debug(
                                            f"Could not calculate perceptual hash for {image_path}: {e}"
                                        )
                            return True

                        # Run with timeout
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(process_image)
                            try:
                                future.result(timeout=10)  # 10 second timeout per image
                            except FutureTimeout:
                                logging.warning(
                                    f"Image processing timeout for {image_path}"
                                )
                                future.cancel()
                                return metadata  # Return what we have so far

                    except Exception as e:
                        logging.warning(f"Error processing image {image_path}: {e}")

                return metadata

            except Exception as e:
                logging.warning(
                    f"Unexpected error in metadata extraction for {image_path}: {e}"
                )
                return None

        try:
            # Add a global timeout for the entire extraction

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_safe_extract)
                try:
                    return future.result(timeout=15)  # 15 second global timeout
                except FutureTimeout:
                    logging.error(f"Global timeout reached for {image_path}")
                    future.cancel()
                    return None

        except Exception as e:
            logging.error(f"Fatal error processing {image_path}: {e}")
            return None

    def calculate_filename_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two filenames."""
        if not DIFFLIB_AVAILABLE:
            return 1.0 if name1.lower() == name2.lower() else 0.0

        # Remove extensions and normalize
        name1_clean = Path(name1).stem.lower()
        name2_clean = Path(name2).stem.lower()

        # Use sequence matcher for base similarity
        ratio = SequenceMatcher(None, name1_clean, name2_clean).ratio()

        # Bonus for exact match
        if name1_clean == name2_clean:
            return 1.0

        # Check for numbered variations (common duplicate pattern)
        # This catches cases like "IMG_001.jpg" vs "IMG_001_copy.jpg" or "photo (1).jpg" vs "photo (2).jpg"
        if (
            "_" in name1_clean
            or "_" in name2_clean
            or "(" in name1_clean
            or "(" in name2_clean
            or "-" in name1_clean
            or "-" in name2_clean
        ):

            # Remove common suffixes that indicate copies

            # Remove patterns like _1, _copy, _backup, (1), (2), etc.
            pattern = r"[_\-\s]*(?:copy|backup|\d+|\(\d+\))[_\-\s]*$"
            base1 = re.sub(pattern, "", name1_clean, flags=re.IGNORECASE)
            base2 = re.sub(pattern, "", name2_clean, flags=re.IGNORECASE)

            if base1 == base2 and len(base1) > 2:
                ratio = max(ratio, 0.95)  # Very high similarity for copy patterns

        return ratio

    def calculate_visual_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate visual similarity between two perceptual hashes."""
        if not hash1 or not hash2 or not IMAGEHASH_AVAILABLE:
            return 0.0

        try:
            # Split combined hashes
            hashes1 = hash1.split(":")
            hashes2 = hash2.split(":")

            if len(hashes1) != 3 or len(hashes2) != 3:
                return 0.0

            # Calculate average distance across all hash types
            total_distance = 0
            for h1, h2 in zip(hashes1, hashes2):
                # Convert to imagehash objects and calculate hamming distance
                hash_obj1 = imagehash.hex_to_hash(h1)
                hash_obj2 = imagehash.hex_to_hash(h2)
                distance = hash_obj1 - hash_obj2
                total_distance += distance

            avg_distance = total_distance / 3

            # Convert distance to similarity (lower distance = higher similarity)
            # Max possible distance is typically 64 for most hash algorithms
            similarity = max(0.0, 1.0 - (avg_distance / 64.0))
            return similarity

        except Exception as e:
            logging.warning(f"Error calculating visual similarity: {e}")
            return 0.0

    def find_duplicates(self, source_paths: List[Path]) -> List[DuplicateGroup]:
        """Find duplicate images using multiple detection methods.

        Accepts a single path (str/Path) or an iterable of paths and normalizes to List[Path].
        """
        if not source_paths:
            return []

        # Normalize inputs: allow str/Path or iterables of them
        try:
            from collections.abc import Iterable as _Iterable
        except Exception:
            _Iterable = tuple  # Fallback; shouldn't happen

        if isinstance(source_paths, (str, Path)):
            normalized_paths = [Path(source_paths)]
        elif isinstance(source_paths, _Iterable):
            normalized_paths = []
            for p in source_paths:
                normalized_paths.append(Path(p))
        else:
            normalized_paths = [Path(source_paths)]

        source_paths = normalized_paths

        self.cancel_flag = False
        self.duplicate_groups = []

        # Collect all image files
        all_images = []
        for source_path in source_paths:
            if source_path.is_file() and source_path.suffix.lower() in IMAGE_EXTENSIONS:
                all_images.append(source_path)
            elif source_path.is_dir():
                for image_path in source_path.rglob("*"):
                    if (
                        image_path.is_file()
                        and image_path.suffix.lower() in IMAGE_EXTENSIONS
                    ):
                        all_images.append(image_path)

        if not all_images:
            logging.info("No image files found for deduplication")
            return []

        self.total_files_analyzed = len(all_images)
        logging.info(f"Analyzing {self.total_files_analyzed} images for duplicates...")

        # Process all files - no artificial limits

        # Log optimization settings
        optimizations = []
        if not self.check_metadata:
            optimizations.append("EXIF extraction disabled")
        if not self.check_visual_similarity:
            optimizations.append("perceptual hashing disabled")
        if not self.check_filenames:
            optimizations.append("filename comparison disabled")
        if not self.check_filesizes:
            optimizations.append("file size comparison disabled")

        if optimizations:
            logging.info(f"Performance optimizations: {', '.join(optimizations)}")
        else:
            logging.info("All detection methods enabled - full analysis mode")

        # Extract metadata for all images - only compute what's needed based on settings
        metadata_list = []
        for i, image_path in enumerate(all_images):
            if self.cancel_flag:
                break

            if self.progress_callback:
                self.progress_callback(
                    i, len(all_images), f"Analyzing {image_path.name}"
                )

            try:
                # Only extract what's needed based on enabled detection methods
                extract_md5 = True  # We'll keep MD5 for exact matching
                extract_exif = self.check_metadata
                extract_visual = self.check_visual_similarity

                metadata = self.extract_metadata(
                    image_path,
                    extract_md5=extract_md5,
                    extract_exif=extract_exif,
                    extract_visual=extract_visual,
                )
                if metadata:
                    metadata_list.append(metadata)
            except Exception as e:
                logging.warning(f"Failed to extract metadata for {image_path}: {e}")
                continue

        if self.cancel_flag:
            return []

        logging.info(f"Successfully extracted metadata for {len(metadata_list)} images")

        # Optimize: Group files by size first to reduce comparisons
        size_groups = {}
        for meta in metadata_list:
            size = meta.size
            if size not in size_groups:
                size_groups[size] = []
            size_groups[size].append(meta)

        # Only process size groups with multiple files (potential duplicates)
        candidate_groups = {
            size: files for size, files in size_groups.items() if len(files) > 1
        }

        logging.info(
            f"Optimization: {len(candidate_groups)} size groups with potential duplicates"
        )
        logging.info(
            f"Files to compare reduced from {len(metadata_list)} to {sum(len(files) for files in candidate_groups.values())}"
        )

        # Find duplicates using various methods
        processed_files = set()
        comparison_count = 0

        # Add safety limits to prevent infinite processing
        MAX_COMPARISONS = 100000  # Reduced from 1M to prevent excessive processing
        MAX_PROCESSING_TIME = 60  # 1 minute max per operation
        MAX_GROUP_SIZE = 30  # Maximum files to process in a single size group

        start_time = time.time()
        last_progress_update = start_time

        # Track progress for the UI
        total_groups = len(candidate_groups)
        processed_groups = 0

        # Process each size group separately (much more efficient)
        for size, size_group in candidate_groups.items():
            if self.cancel_flag:
                logging.info("Operation cancelled by user")
                break

            # Update progress for UI
            current_time = time.time()
            if (
                current_time - last_progress_update > 1.0
            ):  # Update at most once per second
                progress = (processed_groups / max(1, total_groups)) * 100
                if self.progress_callback:
                    self.progress_callback(
                        processed_groups,
                        total_groups,
                        f"Processing group {processed_groups + 1}/{total_groups} - {progress:.1f}%",
                    )
                last_progress_update = current_time

            # Safety check: don't process if too much time has passed
            if current_time - start_time > MAX_PROCESSING_TIME:
                logging.warning(
                    f"Processing timeout reached ({MAX_PROCESSING_TIME}s). Stopping to prevent hang."
                )
                if self.progress_callback:
                    self.progress_callback(
                        0,
                        0,
                        "Processing timed out - some files may not have been processed",
                    )
                break

            # Skip very large size groups that would take too long
            if len(size_group) > MAX_GROUP_SIZE:
                logging.warning(
                    f"Skipping large size group: {size:,} bytes ({len(size_group)} files) - exceeds maximum group size of {MAX_GROUP_SIZE}"
                )
                processed_groups += 1
                continue

            logging.info(
                f"Processing size group {processed_groups + 1}/{total_groups}: {size:,} bytes ({len(size_group)} files)"
            )
            group_start_time = time.time()

            # Process files in chunks with progress updates
            chunk_size = max(1, len(size_group) // 10)  # Update progress every 10%
            for i, meta1 in enumerate(size_group):
                if self.cancel_flag:
                    logging.info("Comparison cancelled by user")
                    break

                # Check if we've exceeded the maximum comparisons
                if comparison_count >= MAX_COMPARISONS:
                    logging.warning(
                        f"Maximum comparisons reached ({MAX_COMPARISONS}). Stopping to prevent hang."
                    )
                    break

                # Skip already processed files
                if meta1.path in processed_files:
                    continue

                # More frequent progress updates
                current_time = time.time()
                if (
                    current_time - last_progress_update > 0.5
                ):  # Update at most twice per second
                    progress = (i / max(1, len(size_group))) * 100
                    status = f"Processing {i+1}/{len(size_group)} in group {processed_groups + 1}/{total_groups} - {progress:.1f}%"
                    if self.progress_callback:
                        self.progress_callback(
                            comparison_count,
                            min(
                                MAX_COMPARISONS, len(metadata_list) * 10
                            ),  # Estimate max comparisons
                            status,
                        )
                    last_progress_update = current_time

                # Check for timeout
                if current_time - start_time > MAX_PROCESSING_TIME:
                    logging.warning(
                        f"Processing timeout reached ({MAX_PROCESSING_TIME}s)."
                    )
                    break

                duplicate_group = [meta1.path]
                duplicate_reasons = []
                max_similarity = 0.0

                # Process remaining files in the group for comparison
                for j, meta2 in enumerate(size_group[i + 1 :], i + 1):
                    # Check for cancellation or timeouts frequently
                    if self.cancel_flag:
                        logging.info("Comparison cancelled by user during inner loop")
                        break

                    if meta2.path in processed_files:
                        continue

                    comparison_count += 1

                    # Update progress more frequently during intensive operations
                    if comparison_count % 10 == 0:
                        current_time = time.time()
                        if (
                            current_time - last_progress_update > 0.5
                        ):  # Throttle updates
                            status = f"Comparing {comparison_count} files in group {processed_groups + 1}/{total_groups}"
                            if self.progress_callback:
                                self.progress_callback(
                                    comparison_count
                                    % 100,  # Rotate through 0-99 for smooth progress
                                    100,
                                    status,
                                )
                            last_progress_update = current_time

                    # Check comparison limits
                    if comparison_count >= MAX_COMPARISONS:
                        logging.warning(
                            f"Maximum comparisons reached ({MAX_COMPARISONS})."
                        )
                        break

                    # Check for timeouts at multiple levels
                    current_time = time.time()
                    if current_time - group_start_time > 30:  # 30s per group max
                        logging.warning(
                            f"Size group processing timeout after 30 seconds - moving to next group"
                        )
                        break

                    if current_time - start_time > MAX_PROCESSING_TIME:
                        logging.warning(
                            f"Total processing time exceeded {MAX_PROCESSING_TIME} seconds."
                        )
                        break

                    similarity_score = 0.0
                    reasons = []

                    # Since we're already grouped by size, start with high similarity
                    similarity_score = 0.95
                    reasons.append("same_size")

                    # Check if dimensions are also the same
                    if (
                        meta1.dimensions
                        and meta2.dimensions
                        and meta1.dimensions == meta2.dimensions
                    ):
                        similarity_score = max(similarity_score, 0.98)
                        reasons.append("same_size_dimensions")

                    # Check for exact content match (MD5)
                    if (
                        meta1.md5_hash
                        and meta2.md5_hash
                        and meta1.md5_hash == meta2.md5_hash
                    ):
                        similarity_score = 1.0
                        reasons = ["identical_content"]  # Override other reasons

                    # Check filename similarity (only if not already a perfect match)
                    if similarity_score < 0.99 and self.check_filenames:
                        name_sim = self.calculate_filename_similarity(
                            meta1.path.name, meta2.path.name
                        )
                        if name_sim >= self.filename_similarity_threshold:
                            base_score = name_sim * 0.85
                            similarity_score = max(similarity_score, base_score)
                            reasons.append("filename_similarity")

                            # Bonus for same size + similar name
                            if meta1.size == meta2.size and meta1.size > 0:
                                similarity_score = max(
                                    similarity_score, name_sim * 0.95
                                )
                                reasons.append("filename_size_match")

                    # Check visual similarity (only if no strong match yet - most expensive)
                    if (
                        similarity_score < 0.8
                        and self.check_visual_similarity
                        and meta1.perceptual_hash
                        and meta2.perceptual_hash
                    ):
                        visual_sim = self.calculate_visual_similarity(
                            meta1.perceptual_hash, meta2.perceptual_hash
                        )
                        if visual_sim >= 0.6:
                            similarity_score = max(similarity_score, visual_sim)
                            reasons.append("visual_similarity")

                    # Add to duplicate group if similarity is high enough
                    if similarity_score >= self.similarity_threshold:
                        duplicate_group.append(meta2.path)
                        duplicate_reasons.extend(reasons)
                        max_similarity = max(max_similarity, similarity_score)

                # Create duplicate group if we found duplicates
                if len(duplicate_group) > 1:
                    logging.info(
                        f"Found duplicate group: {len(duplicate_group)} files, max similarity: {max_similarity:.3f}"
                    )
                    logging.info(f"  Files: {[p.name for p in duplicate_group]}")
                    logging.info(f"  Reasons: {set(duplicate_reasons)}")

                    # Mark all files in this group as processed
                    for path in duplicate_group:
                        processed_files.add(path)

                    # Determine duplicate type and recommended action
                    duplicate_type = "similar"
                    recommended_action = "manual_review"

                    if "identical_content" in duplicate_reasons:
                        duplicate_type = "exact"
                        recommended_action = "keep_largest"
                    elif "same_size_dimensions" in duplicate_reasons:
                        duplicate_type = "likely_exact"
                        recommended_action = "keep_first"
                    elif "visual_similarity" in duplicate_reasons:
                        duplicate_type = "visually_similar"
                        recommended_action = "manual_review"

                    # Calculate potential size savings
                    file_sizes = [
                        meta.size
                        for meta in metadata_list
                        if meta.path in duplicate_group
                    ]
                    size_savings = (
                        sum(file_sizes) - max(file_sizes) if file_sizes else 0
                    )

                    group = DuplicateGroup(
                        similarity_score=max_similarity,
                        duplicate_type=duplicate_type,
                        files=duplicate_group,
                        recommended_action=recommended_action,
                        size_savings=size_savings,
                    )

                    self.duplicate_groups.append(group)
                    self.total_duplicates_found += len(duplicate_group) - 1
                    self.potential_savings += size_savings

            logging.info(
                f"Completed size group {size:,} in {time.time() - group_start_time:.1f} seconds"
            )  # Sort groups by similarity score (highest first)
        self.duplicate_groups.sort(key=lambda g: g.similarity_score, reverse=True)

        processing_time = time.time() - start_time

        # Prepare summary message
        summary = (
            f"Deduplication complete: {len(self.duplicate_groups)} duplicate groups found\n"
            f"Total duplicates: {self.total_duplicates_found}\n"
            f"Potential space savings: {self.potential_savings / (1024*1024):.1f} MB\n"
            f"Processing time: {processing_time:.1f} seconds\n"
            f"Files analyzed: {self.total_files_analyzed}\n"
            f"Comparisons made: {comparison_count:,}"
        )

        # Log the summary
        logging.info("\n" + "=" * 50)
        logging.info(summary.replace("\n", "\n  "))
        logging.info("=" * 50)

        # Update progress callback with final status
        if self.progress_callback:
            if self.cancel_flag:
                status = "Operation cancelled by user"
            elif comparison_count >= MAX_COMPARISONS:
                status = "⚠️  Comparison limit reached. Some files may not have been processed."
            elif processing_time >= MAX_PROCESSING_TIME:
                status = (
                    "⚠️  Time limit reached. Some files may not have been processed."
                )
            else:
                status = "✅  Deduplication completed successfully"

            self.progress_callback(100, 100, f"{status}\n\n{summary}")  # 100% complete

        # Log warnings if we hit any limits
        if comparison_count >= MAX_COMPARISONS:
            logging.warning(
                "⚠️  Processing stopped due to comparison limit. Some duplicates may not have been found."
            )
        if processing_time >= MAX_PROCESSING_TIME:
            logging.warning(
                "⚠️  Processing stopped due to time limit. Some duplicates may not have been found."
            )
        if self.cancel_flag:
            logging.warning("⚠️  Processing was cancelled by the user.")

        return self.duplicate_groups

    def __init__(
        self,
        threshold: float = 0.85,
        check_filenames: bool = True,
        check_visual_similarity: bool = True,
        filename_similarity_threshold: float = 0.7,
        similarity_threshold: Optional[float] = None,
        **kwargs,
    ):
        """Initialize the deduplication engine.

        Backward/forward compatible args:
        - threshold: main similarity threshold (0.0-1.0)
        - similarity_threshold: alias for threshold (used by some callers like GUI)
        - check_filenames: enable filename similarity
        - check_visual_similarity: enable perceptual hashing
        - filename_similarity_threshold: 0.0-1.0
        """
        # Allow GUI to pass similarity_threshold; it overrides threshold if provided
        if similarity_threshold is not None:
            threshold = similarity_threshold

        if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
            raise ValueError("threshold must be a float between 0.0 and 1.0")
        if not isinstance(check_filenames, bool):
            raise ValueError("check_filenames must be a boolean")
        if not isinstance(check_visual_similarity, bool):
            raise ValueError("check_visual_similarity must be a boolean")
        if not isinstance(filename_similarity_threshold, (int, float)) or not (
            0.0 <= filename_similarity_threshold <= 1.0
        ):
            raise ValueError(
                "filename_similarity_threshold must be a float between 0.0 and 1.0"
            )

        # Core thresholds/settings
        self.similarity_threshold = float(threshold)
        self.check_filenames = check_filenames
        self.check_visual_similarity = check_visual_similarity
        self.filename_similarity_threshold = float(filename_similarity_threshold)

        # Additional settings
        self.check_filesizes = True
        self.check_metadata = True
        self.size_difference_threshold = 0.02  # 2% difference allowed
        self.visual_similarity_threshold = 5  # Hamming distance for perceptual hashes

        # Results tracking
        self.duplicate_groups: List[DuplicateGroup] = []
        self.total_files_analyzed = 0
        self.total_duplicates_found = 0
        self.potential_savings = 0
        self.cancel_flag = False
        self.progress_callback = None

    # Backward-compatibility: expose 'threshold' property to mirror similarity_threshold
    @property
    def threshold(self) -> float:
        return self.similarity_threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
            raise ValueError("threshold must be a float between 0.0 and 1.0")
        self.similarity_threshold = float(value)

    def remove_duplicates(
        self,
        groups_to_process: List[DuplicateGroup],
        action: str = "auto",
        output_folder: Optional[Path] = None,
    ) -> Dict[str, int]:
        """Remove duplicates based on the specified action.

        Args:
            groups_to_process: List of duplicate groups to process
            action: Action to take on duplicates ('auto', 'keep_first', 'keep_largest', 'move_organize', 'move_to_folder')
            output_folder: Folder for move operations (required for 'move_organize' and 'move_to_folder' actions)

        Returns:
            Dictionary with operation statistics
        """
        if not groups_to_process:
            raise ValueError("No duplicate groups provided")
        if not isinstance(action, str) or action not in [
            "auto",
            "keep_first",
            "keep_largest",
            "move_organize",
            "move_to_folder",
        ]:
            raise ValueError(
                "Invalid action. Must be one of 'auto', 'keep_first', 'keep_largest', 'move_organize', or 'move_to_folder'"
            )
        if action in ["move_organize", "move_to_folder"] and not output_folder:
            raise ValueError(f"Output folder must be specified for {action} action")

        stats = {"files_removed": 0, "files_moved": 0, "space_saved": 0, "errors": 0}

        # Calculate total number of files to process for progress tracking
        total_files = sum(len(group.files) for group in groups_to_process)
        processed_files = 0

        # Notify start of operation
        if self.progress_callback:
            self.progress_callback(0, total_files, "Starting duplicate removal...")

        for group_idx, group in enumerate(groups_to_process, 1):
            if self.cancel_flag:
                break

            # Update progress at the start of each group
            if self.progress_callback:
                self.progress_callback(
                    processed_files,
                    total_files,
                    f"Processing group {group_idx}/{len(groups_to_process)} with {len(group.files)} files",
                )

            try:
                files_to_remove = []
                files_to_move = []

                if action == "auto":
                    # Use recommended action for each group
                    if group.recommended_action == "keep_largest":
                        # Keep the largest file, remove others
                        file_sizes = [(f, f.stat().st_size) for f in group.files]
                        file_sizes.sort(key=lambda x: x[1], reverse=True)
                        files_to_remove = [f[0] for f in file_sizes[1:]]

                    elif group.recommended_action == "keep_first":
                        # Keep the first file (oldest), remove others
                        files_to_remove = group.files[1:]

                elif action == "keep_first":
                    files_to_remove = group.files[1:]

                elif action == "keep_largest":
                    file_sizes = [(f, f.stat().st_size) for f in group.files]
                    file_sizes.sort(key=lambda x: x[1], reverse=True)
                    files_to_remove = [f[0] for f in file_sizes[1:]]

                elif action == "move_organize":
                    # Move duplicates to organized folders
                    if output_folder is None:
                        raise ValueError(
                            "Output folder must be specified for move_organize action"
                        )

                    # Create organized folder structure
                    original_folder = output_folder / "original"
                    duplicates_folder = output_folder / "duplicated"
                    try:
                        output_folder.mkdir(parents=True, exist_ok=True)
                        original_folder.mkdir(exist_ok=True)
                        duplicates_folder.mkdir(exist_ok=True)
                        logging.info(
                            f"Created organized folder structure: {original_folder} and {duplicates_folder}"
                        )
                    except Exception as e:
                        error_msg = f"Failed to create organized folders: {e}"
                        logging.error(error_msg)
                        raise RuntimeError(error_msg) from e

                    # Find the largest file (original) and duplicates
                    file_sizes = [(f, f.stat().st_size) for f in group.files]
                    file_sizes.sort(key=lambda x: x[1], reverse=True)
                    original_file = file_sizes[0][0]
                    duplicate_files = [f[0] for f in file_sizes[1:]]

                    # Move original to original folder
                    try:
                        original_dest = original_folder / original_file.name
                        # Handle name conflicts
                        if original_dest.exists():
                            stem = original_dest.stem
                            suffix = original_dest.suffix
                            counter = 1
                            while original_dest.exists():
                                original_dest = (
                                    original_folder / f"{stem}_{counter}{suffix}"
                                )
                                counter += 1

                        shutil.move(str(original_file), str(original_dest))
                        stats["files_moved"] += 1
                        processed_files += 1
                        if self.progress_callback:
                            self.progress_callback(
                                processed_files,
                                total_files,
                                f"Moved original: {original_file.name}",
                            )
                        logging.info(f"Moved original to: {original_dest}")
                    except Exception as e:
                        logging.error(f"Failed to move original {original_file}: {e}")
                        stats["errors"] += 1

                    # Move duplicates to duplicates folder
                    for dup_file in duplicate_files:
                        try:
                            dup_dest = duplicates_folder / dup_file.name
                            # Handle name conflicts
                            if dup_dest.exists():
                                stem = dup_dest.stem
                                suffix = dup_dest.suffix
                                counter = 1
                                while dup_dest.exists():
                                    dup_dest = (
                                        duplicates_folder / f"{stem}_{counter}{suffix}"
                                    )
                                    counter += 1

                            shutil.move(str(dup_file), str(dup_dest))
                            stats["files_moved"] += 1
                            processed_files += 1
                            if self.progress_callback:
                                self.progress_callback(
                                    processed_files,
                                    total_files,
                                    f"Moved duplicate: {dup_file.name}",
                                )
                            logging.info(f"Moved duplicate to: {dup_dest}")
                        except Exception as e:
                            logging.error(f"Failed to move duplicate {dup_file}: {e}")
                            stats["errors"] += 1

                    # Skip the removal logic for move_organize
                    continue

                # Handle move_to_folder action
                if action == "move_to_folder" and output_folder:
                    # Ensure output folder exists
                    try:
                        output_folder.mkdir(parents=True, exist_ok=True)
                        logging.info(f"Ensured output folder exists: {output_folder}")
                    except Exception as e:
                        error_msg = (
                            f"Failed to create output folder {output_folder}: {e}"
                        )
                        logging.error(error_msg)
                        raise RuntimeError(error_msg) from e

                    # Move all files in the group to the output folder
                    for file_path in group.files:
                        try:
                            if not file_path.exists():
                                logging.warning(
                                    f"Source file does not exist: {file_path}"
                                )
                                continue

                            # Create the destination path
                            dest_path = output_folder / file_path.name

                            # Handle name conflicts
                            if dest_path.exists():
                                stem = dest_path.stem
                                suffix = dest_path.suffix
                                counter = 1
                                while dest_path.exists():
                                    dest_path = (
                                        output_folder / f"{stem}_{counter}{suffix}"
                                    )
                                    counter += 1

                            # Move the file
                            shutil.move(str(file_path), str(dest_path))
                            stats["files_moved"] += 1
                            stats["space_saved"] += file_path.stat().st_size
                            processed_files += 1
                            if self.progress_callback:
                                self.progress_callback(
                                    processed_files,
                                    total_files,
                                    f"Moved: {file_path.name}",
                                )
                            logging.info(f"Moved to {dest_path}")

                        except Exception as e:
                            logging.error(f"Failed to move {file_path}: {e}")
                            stats["errors"] += 1
                    continue

                # Default: Remove the files (for non-move actions)
                for file_path in files_to_remove:
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        stats["files_removed"] += 1
                        stats["space_saved"] += file_size
                        processed_files += 1
                        if self.progress_callback:
                            self.progress_callback(
                                processed_files,
                                total_files,
                                f"Removed: {file_path.name}",
                            )
                        logging.info(f"Removed duplicate: {file_path}")
                    except Exception as e:
                        logging.error(f"Failed to remove {file_path}: {e}")
                        processed_files += 1
                        stats["errors"] += 1
                        if self.progress_callback:
                            self.progress_callback(
                                processed_files,
                                total_files,
                                f"Error removing {file_path.name}",
                            )

            except Exception as e:
                logging.error(f"Error processing duplicate group: {e}")
                stats["errors"] += 1

        # Notify completion
        if self.progress_callback and not self.cancel_flag:
            self.progress_callback(
                total_files, total_files, "Duplicate removal completed"
            )

        return stats

    def export_results(self, output_path: Path) -> bool:
        """Export deduplication results to a JSON file."""
        try:
            results = {
                "analysis_timestamp": datetime.now().isoformat(),
                "total_files_analyzed": self.total_files_analyzed,
                "duplicate_groups_found": len(self.duplicate_groups),
                "total_duplicates": self.total_duplicates_found,
                "potential_savings_bytes": self.potential_savings,
                "potential_savings_mb": round(
                    self.potential_savings / (1024 * 1024), 2
                ),
                "groups": [],
            }

            for group in self.duplicate_groups:
                group_data = {
                    "similarity_score": group.similarity_score,
                    "duplicate_type": group.duplicate_type,
                    "recommended_action": group.recommended_action,
                    "size_savings_bytes": group.size_savings,
                    "files": [str(f) for f in group.files],
                }
                results["groups"].append(group_data)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logging.info(f"Deduplication results exported to: {output_path}")
            return True

        except Exception as e:
            logging.error(f"Failed to export results: {e}")
            return False

    def get_stats(self) -> Dict[str, int]:
        """Return basic statistics about the last deduplication run."""
        try:
            return {
                "total_files": int(self.total_files_analyzed),
                "duplicate_groups": int(len(self.duplicate_groups)),
                "duplicate_count": int(self.total_duplicates_found),
                "potential_savings": int(self.potential_savings),
                "potential_savings_mb": round(
                    self.potential_savings / (1024 * 1024), 2
                ),
            }
        except Exception:
            # Be resilient; return minimal stats
            return {
                "total_files": 0,
                "duplicate_groups": 0,
                "duplicate_count": 0,
                "potential_savings": 0,
                "potential_savings_mb": 0.0,
            }


def install_deduplication_dependencies():
    """Install optional dependencies for enhanced deduplication."""
    try:
        import subprocess
        import sys

        # Try to install imagehash for perceptual hashing
        if not IMAGEHASH_AVAILABLE:
            print("Installing imagehash for advanced visual similarity detection...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "imagehash"])

        return True

    except Exception as e:
        logging.warning(f"Could not install optional deduplication dependencies: {e}")
        return False


# Test function
def main():
    """Test the deduplication functionality."""
    import argparse

    parser = argparse.ArgumentParser(description="Photo Deduplication Tool")
    parser.add_argument("source", help="Source directory to scan for duplicates")
    parser.add_argument(
        "--threshold", type=float, default=0.85, help="Similarity threshold (0.0-1.0)"
    )
    parser.add_argument("--export", help="Export results to JSON file")
    parser.add_argument(
        "--remove",
        choices=["auto", "keep_first", "keep_largest"],
        help="Automatically remove duplicates",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Initialize deduplication engine
    engine = DeduplicationEngine(similarity_threshold=args.threshold)

    # Find duplicates
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: Source path '{source_path}' does not exist")
        return

    print(f"Scanning for duplicates in: {source_path}")
    groups = engine.find_duplicates([source_path])

    if not groups:
        print("No duplicates found!")
        return

    # Display results
    print(f"\nFound {len(groups)} duplicate groups:")
    for i, group in enumerate(groups, 1):
        print(
            f"\nGroup {i} ({group.duplicate_type}, {group.similarity_score:.2f} similarity):"
        )
        for file_path in group.files:
            file_size = file_path.stat().st_size / (1024 * 1024)
            print(f"  - {file_path} ({file_size:.1f} MB)")
        print(f"  Potential savings: {group.size_savings / (1024*1024):.1f} MB")
        print(f"  Recommended action: {group.recommended_action}")

    print(f"\nTotal potential savings: {engine.potential_savings / (1024*1024):.1f} MB")

    # Export results if requested
    if args.export:
        engine.export_results(Path(args.export))

    # Remove duplicates if requested
    if args.remove:
        print(f"\nRemoving duplicates using strategy: {args.remove}")
        stats = engine.remove_duplicates(groups, args.remove)
        print(f"Files removed: {stats['files_removed']}")
        print(f"Space saved: {stats['space_saved'] / (1024*1024):.1f} MB")
        if stats["errors"]:
            print(f"Errors: {stats['errors']}")


if __name__ == "__main__":
    main()
