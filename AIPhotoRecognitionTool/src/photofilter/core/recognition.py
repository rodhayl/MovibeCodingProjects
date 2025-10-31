#!/usr/bin/env python3
"""
Photo Recognition and Organization Tool

This script analyzes photos in the 'ToProcess' folder using advanced AI models for object detection.
Users can specify what objects to detect, and photos are organized into corresponding folders
under 'Filtered/[ObjectName]' or 'Filtered/Other' if the object is not found.

Supports multiple detection models:
- YOLOv5 (n/s/m/l/x variants)
- YOLOv8 (latest architecture)
- RT-DETR (transformer-based)
- Ensemble (combination of multiple models)

Optimized for NVIDIA GeForce GTX 1050 (2GB RAM) with automatic CPU fallback.
"""

import os
import sys
import shutil
from pathlib import Path
import logging
import argparse
from typing import List
import time
import gc

try:
    import torch
    from PIL import Image, ImageFile
    import numpy as np

    # Import advanced detectors
    try:
        from .detectors import (
            BaseDetector,
            YOLOv8Detector,
            RTDETRDetector,
            EnsembleDetector,
            AVAILABLE_DETECTORS,
            create_detector,
            create_ensemble_detector,
        )
    except ImportError:
        # Fallback for when detectors module has issues
        BaseDetector = None
        YOLOv5Detector = None
        YOLOv8Detector = None
        RTDETRDetector = None
        EnsembleDetector = None
        AVAILABLE_DETECTORS = {}
        create_detector = None
        create_ensemble_detector = None

    DEPENDENCIES_AVAILABLE = True
    # Enable loading of truncated images
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    # Type hint for numpy array when available
    NumpyArray = np.ndarray
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    MISSING_DEPENDENCY = str(e)
    # Fallback type hint
    NumpyArray = object

    # Create dummy classes for when dependencies aren't available
    class BaseDetector:
        pass


# Set up logging
def setup_logging(log_file: str = "photo_recognition.log"):
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


# Define image file extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"}


class YOLOv5nOriginalDetector:
    """Legacy YOLOv5n-based detector optimized for low memory usage with enhanced precision.

    Note: Advanced YOLOv5 variants live in photofilter.core.detectors as YOLOv5Detector.
    This class is retained for backward compatibility and specific behaviors (e.g., white dog mode).
    """

    def __init__(self, confidence_threshold: float = 0.25, iou_threshold: float = 0.45):
        self.model = None
        self.device = None
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold  # Non-Maximum Suppression threshold
        self.class_names = []
        self.batch_size = 1  # Start with batch size 1 for 2GB GPU

        # Enhanced detection settings for better precision
        self.use_multi_scale = True  # Enable multi-scale detection
        self.augment_inference = True  # Use test-time augmentation

    def initialize_model(self) -> bool:
        """Initialize YOLOv5n model with memory optimization."""
        try:
            # Check CUDA availability and memory
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (
                    1024**3
                )
                logging.info(f"CUDA available. GPU memory: {gpu_memory:.1f}GB")

                if gpu_memory < 3.0:  # Less than 3GB, use conservative settings
                    self.device = torch.device("cuda")
                    self.batch_size = 1
                    logging.info("Using GPU with conservative memory settings")
                else:
                    self.device = torch.device("cuda")
                    self.batch_size = 4
                    logging.info("Using GPU with standard settings")
            else:
                self.device = torch.device("cpu")
                self.batch_size = 2
                logging.info("CUDA not available, using CPU")

            # Load YOLOv5n model (smallest version)
            logging.info("Loading YOLOv5n model...")

            # Ensure we have a clean download
            try:
                # Set explicit torch.hub cache directory consistent with detectors.py
                hub_dir = Path.cwd() / "model_cache"
                if hub_dir.exists() and not hub_dir.is_dir():
                    logging.warning(
                        f"Path {hub_dir} exists and is not a directory. Using fallback .model_cache"
                    )
                    hub_dir = Path.cwd() / ".model_cache"
                hub_dir.mkdir(parents=True, exist_ok=True)
                torch.hub.set_dir(str(hub_dir))
                logging.info(f"torch.hub cache dir set to: {hub_dir}")

                # Download the model with verbose output and trust the repository
                logging.info("Downloading YOLOv5n (Original) model from Ultralytics...")
                self.model = torch.hub.load(
                    "ultralytics/yolov5",
                    "yolov5n",
                    pretrained=True,
                    verbose=True,
                    trust_repo=True,  # Trust the ultralytics repository
                )

                logging.info("✅ YOLOv5n model downloaded and loaded successfully")

            except Exception as download_error:
                logging.error(f"Model download failed: {download_error}")
                logging.error("This might be due to missing dependencies.")
                logging.error(
                    "Missing packages may include: seaborn, matplotlib, opencv-python"
                )
                logging.error(
                    "Please run the GUI launcher which will install all dependencies automatically."
                )
                return False

            # Configure model for enhanced precision
            self.model.to(self.device)
            self.model.eval()

            # Enhanced detection settings
            self.model.conf = self.confidence_threshold  # Confidence threshold
            self.model.iou = self.iou_threshold  # IoU threshold for NMS
            self.model.agnostic = False  # Class-agnostic NMS
            self.model.multi_label = True  # Multiple labels per box
            self.model.max_det = 1000  # Maximum detections per image

            # Enable test-time augmentation for better detection
            if self.augment_inference:
                self.model.augment = True

            logging.info(f"Enhanced detection settings applied:")
            logging.info(f"  - Confidence threshold: {self.confidence_threshold}")
            logging.info(f"  - IoU threshold: {self.iou_threshold}")
            logging.info(f"  - Multi-label detection: {self.model.multi_label}")
            logging.info(f"  - Test-time augmentation: {self.augment_inference}")

            # Get class names from COCO dataset
            self.class_names = self.model.names

            logging.info(f"Model loaded successfully on {self.device}")
            logging.info(f"Available classes: {len(self.class_names)} classes")

            # Test with a small dummy image to ensure everything works
            dummy_image = Image.new("RGB", (640, 640), color="red")
            test_results = self.model(dummy_image)
            logging.info("Model test successful")

            return True

        except Exception as e:
            logging.error(f"Failed to initialize YOLOv5n (Original) model: {e}")
            return False

    def detect_objects(self, image_path: Path) -> List[str]:
        """Detect objects in an image with enhanced precision and return list of detected class names."""
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")
            original_size = image.size

            # Enhanced preprocessing for better detection
            max_size = 1280 if self.device.type == "cuda" else 640

            detected_objects = []

            # Multi-scale detection for better accuracy
            if self.use_multi_scale:
                scales = (
                    [max_size, int(max_size * 0.8), int(max_size * 1.2)]
                    if max_size == 1280
                    else [max_size]
                )
            else:
                scales = [max_size]

            all_detections = []

            for scale in scales:
                # Resize image for current scale
                test_image = image.copy()
                if max(test_image.size) > scale:
                    test_image.thumbnail((scale, scale), Image.Resampling.LANCZOS)

                # Run inference with enhanced settings
                with torch.no_grad():
                    if self.augment_inference:
                        # Test-time augmentation: original + flipped
                        results1 = self.model(test_image)
                        results2 = self.model(
                            test_image.transpose(Image.FLIP_LEFT_RIGHT)
                        )

                        # Combine results
                        combined_detections = []
                        for r in [results1, results2]:
                            for detection in r.pandas().xyxy[0].itertuples():
                                combined_detections.append(
                                    {
                                        "name": detection.name.lower(),
                                        "confidence": detection.confidence,
                                        "scale": scale,
                                    }
                                )
                        all_detections.extend(combined_detections)
                    else:
                        results = self.model(test_image)
                        for detection in results.pandas().xyxy[0].itertuples():
                            all_detections.append(
                                {
                                    "name": detection.name.lower(),
                                    "confidence": detection.confidence,
                                    "scale": scale,
                                }
                            )

            # Advanced post-processing: consensus-based detection
            object_scores = {}
            for det in all_detections:
                obj_name = det["name"]
                confidence = det["confidence"]

                if obj_name not in object_scores:
                    object_scores[obj_name] = []
                object_scores[obj_name].append(confidence)

            # Apply consensus threshold and enhanced filtering
            for obj_name, scores in object_scores.items():
                max_confidence = max(scores)
                avg_confidence = sum(scores) / len(scores)
                detection_count = len(scores)

                # Enhanced decision criteria
                if max_confidence >= self.confidence_threshold and (
                    avg_confidence >= self.confidence_threshold * 0.8
                    or detection_count >= 2
                ):
                    detected_objects.append(obj_name)

            # Remove duplicates while preserving order
            detected_objects = list(dict.fromkeys(detected_objects))

            # Clear GPU cache if using CUDA
            if self.device.type == "cuda":
                torch.cuda.empty_cache()

            return detected_objects

        except Exception as e:
            logging.error(f"Error detecting objects in {image_path} (Original YOLOv5n): {e}")
            return []

    def detect_white_dogs(self, image_path: Path) -> bool:
        """Enhanced detection specifically for white dogs using color analysis and shape detection."""
        try:
            # First, check if any dogs are detected at all
            detected_objects = self.detect_objects(image_path)
            if "dog" not in detected_objects:
                return False

            # Load image for color analysis
            image = Image.open(image_path).convert("RGB")
            image_array = np.array(image)

            # Run YOLO detection to get bounding boxes
            with torch.no_grad():
                results = self.model(image)

            # Analyze each detected dog for white color characteristics
            for detection in results.pandas().xyxy[0].itertuples():
                if (
                    detection.name.lower() == "dog"
                    and detection.confidence >= self.confidence_threshold
                ):
                    # Extract bounding box coordinates
                    x1, y1, x2, y2 = (
                        int(detection.xmin),
                        int(detection.ymin),
                        int(detection.xmax),
                        int(detection.ymax),
                    )

                    # Ensure coordinates are within image bounds
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(image.width, x2), min(image.height, y2)

                    # Extract the dog region
                    dog_region = image_array[y1:y2, x1:x2]

                    if dog_region.size > 0:
                        # Color analysis for white detection
                        white_score = self._analyze_white_content(dog_region)

                        # Enhanced criteria for white dog detection
                        if white_score > 0.6:  # 60% white content threshold
                            logging.info(
                                f"White dog detected in {image_path.name} (white score: {white_score:.2f})"
                            )
                            return True

            return False

        except Exception as e:
            logging.error(f"Error in white dog detection for {image_path} (Original YOLOv5n): {e}")
            return False

    def _analyze_white_content(self, image_region) -> float:
        """Analyze the white content in an image region."""
        if not DEPENDENCIES_AVAILABLE:
            return 0.0

        if image_region.size == 0:
            return 0.0

        # Convert to HSV for better color analysis
        from PIL import Image as PILImage

        region_image = PILImage.fromarray(image_region)
        hsv_image = region_image.convert("HSV")
        hsv_array = np.array(hsv_image)

        # Define white color ranges in HSV
        # White has low saturation and high value
        h, s, v = hsv_array[:, :, 0], hsv_array[:, :, 1], hsv_array[:, :, 2]

        # White detection criteria:
        # - Low saturation (< 30 out of 255)
        # - High value/brightness (> 180 out of 255)
        # - Any hue is acceptable for white
        white_mask = (s < 30) & (v > 180)

        # Also check for light gray/off-white
        light_gray_mask = (s < 50) & (v > 160)

        # Combine masks
        white_or_light_mask = white_mask | light_gray_mask

        # Calculate percentage of white/light pixels
        white_percentage = np.sum(white_or_light_mask) / white_or_light_mask.size

        return white_percentage


# Backward-compatibility alias so existing code/tests importing YOLOv5Detector from
# photofilter.core.recognition keep working. Advanced YOLOv5Detector lives in
# photofilter.core.detectors and is distinct.
YOLOv5Detector = YOLOv5nOriginalDetector


class PhotoOrganizer:
    """Organizes photos based on detected objects using multiple AI model options."""

    def __init__(
        self,
        base_path: Path = None,
        target_objects: List[str] = None,
        source_path: Path = None,
        output_path: Path = None,
        detector_type: str = "yolov5n_original",
        confidence_threshold: float = 0.25,
        # Backward-compatibility with older API/tests
        input_folder: str = None,
        output_folder: str = None,
    ):
        # Resolve paths allowing legacy args
        resolved_source = Path(input_folder) if input_folder else source_path
        resolved_output = Path(output_folder) if output_folder else output_path

        # Choose a sensible base_path default if not provided
        if base_path is None:
            if resolved_source is not None:
                base_path = Path(resolved_source).parent
            else:
                base_path = Path.cwd()

        self.base_path = base_path
        self.source_path = resolved_source  # May be provided by user/GUI or tests
        self.filtered_path = resolved_output  # May be provided by user/GUI or tests

        # Legacy attribute names expected by tests
        self.input_folder = str(self.source_path) if self.source_path is not None else None
        self.output_folder = str(self.filtered_path) if self.filtered_path is not None else None

        # Supported extensions attribute for tests
        self.supported_extensions = IMAGE_EXTENSIONS

        # Normalize target objects
        target_objects = target_objects or []
        self.target_objects = [obj.lower().strip() for obj in target_objects]
        self.detector_type = detector_type
        self.confidence_threshold = confidence_threshold

        # Check for white dog detection mode
        self.white_dog_mode = (
            "dog" in self.target_objects and len(self.target_objects) == 1
        )

        # Adjust confidence threshold for specific detection modes
        if self.white_dog_mode:
            self.confidence_threshold = max(
                0.15, confidence_threshold - 0.1
            )  # Lower threshold for white dogs

        # Initialize detector
        self.detector = None
        self.detector_info = None

        # Statistics
        self.stats = {
            "total_processed": 0,
            "target_found": 0,
            "moved_to_other": 0,
            "errors": 0,
            "detection_time": 0.0,
        }

    def initialize_detector(self) -> bool:
        """Initialize the selected detection model."""
        logging.info(f"Initializing detector: {self.detector_type}")

        try:
            # Use original YOLOv5nOriginalDetector for backward compatibility
            if self.detector_type == "yolov5n_original":
                self.detector = YOLOv5nOriginalDetector(self.confidence_threshold)
                self.detector_info = {
                    "name": "YOLOv5n (Original)",
                    "description": "Original implementation - reliable and tested",
                    "accuracy": "⭐⭐⭐",
                    "speed": "⭐⭐⭐⭐⭐",
                    "memory": "⭐⭐⭐⭐⭐",
                }
                success = self.detector.initialize_model()

            # Handle ensemble detection
            elif self.detector_type.startswith("ensemble:"):
                detector_names = self.detector_type.replace("ensemble:", "").split(",")
                detector_names = [name.strip() for name in detector_names]
                self.detector = create_ensemble_detector(
                    detector_names, self.confidence_threshold
                )
                if self.detector:
                    self.detector_info = self.detector.get_info()
                    success = self.detector.initialize_model()
                else:
                    return False

            # Use advanced detectors
            else:
                self.detector = create_detector(
                    self.detector_type, self.confidence_threshold
                )
                if self.detector:
                    self.detector_info = self.detector.get_info()
                    success = self.detector.initialize_model()
                else:
                    return False

            if not success:
                logging.error(
                    f"Failed to initialize detector model: {self.detector_type}"
                )
                return False

            logging.info(
                f"✅ {self.detector_info['name']} detector initialized successfully"
            )
            return True

        except Exception as e:
            logging.error(f"Failed to initialize detector {self.detector_type}: {e}")
            return False

    def get_available_detectors(self) -> dict:
        """Get information about all available detectors including original."""
        detectors = {
            "yolov5n_original": {
                "class": "YOLOv5nOriginalDetector",
                "args": {},
                "name": "YOLOv5n (Original)",
                "description": "Original tested implementation",
                "accuracy": "⭐⭐⭐",
                "speed": "⭐⭐⭐⭐⭐",
                "memory": "⭐⭐⭐⭐⭐",
            }
        }

        # Add advanced detectors if available
        if DEPENDENCIES_AVAILABLE:
            try:
                detectors.update(AVAILABLE_DETECTORS)
            except:
                pass  # Advanced detectors not available

        return detectors

    def set_detector(
        self, detector_type: str, confidence_threshold: float = None
    ) -> bool:
        """Change the detection model."""
        self.detector_type = detector_type
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold

        # Re-initialize with new detector
        return self.initialize_detector()

    def create_destination_folders(self) -> bool:
        """Create subfolders for target objects and 'Other' inside the selected output folder."""
        try:
            if not self.filtered_path:
                logging.error("No output folder specified.")
                return False

            # Only create subfolders inside the provided output folder
            for obj in self.target_objects:
                if obj == "dog" and self.white_dog_mode:
                    folder_name = "White_Dog"
                else:
                    folder_name = obj.capitalize()
                folder_path = self.filtered_path / folder_name
                folder_path.mkdir(exist_ok=True)
                logging.info(f"Destination folder ready: {folder_path}")

            # Create 'Other' folder
            other_path = self.filtered_path / "Other"
            other_path.mkdir(exist_ok=True)
            logging.info(f"Destination folder ready: {other_path}")

            return True

        except Exception as e:
            logging.error(f"Failed to create destination folders: {e}")
            return False

    def find_image_files(self) -> List[Path]:
        """Recursively find all image files in the source directory."""
        image_files = []

        try:
            for root, dirs, files in os.walk(self.source_path):
                # Skip hidden directories (starting with '.')
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                for file in files:
                    # Skip hidden files (starting with '.')
                    if file.startswith("."):
                        continue

                    file_path = Path(root) / file
                    if file_path.suffix.lower() in IMAGE_EXTENSIONS:
                        image_files.append(file_path)

            logging.info(
                f"Found {len(image_files)} image files to process (excluding hidden files)"
            )
            return image_files

        except Exception as e:
            logging.error(f"Error scanning directory {self.source_path}: {e}")
            return []

    def move_image_file(self, source_file: Path, destination_folder: Path) -> bool:
        """Move a single image file to the destination folder."""
        try:
            destination_file = destination_folder / source_file.name

            # Handle filename conflicts
            counter = 1
            original_destination = destination_file
            while destination_file.exists():
                stem = original_destination.stem
                suffix = original_destination.suffix
                destination_file = destination_folder / f"{stem}_{counter}{suffix}"
                counter += 1

            # Move the file
            shutil.move(str(source_file), str(destination_file))
            logging.info(f"Moved: {source_file.name} -> {destination_folder.name}/")
            return True

        except Exception as e:
            logging.error(f"Failed to move {source_file}: {e}")
            return False

    def process_images(self) -> bool:
        """Process all images and organize them based on detected objects."""
        if not self.detector.initialize_model():
            logging.error("Failed to initialize detection model")
            return False

        # Find all image files
        image_files = self.find_image_files()
        if not image_files:
            logging.info("No image files found to process")
            return True

        logging.info(f"Processing {len(image_files)} images...")
        logging.info(f"Looking for objects: {', '.join(self.target_objects)}")

        # Process each image
        for i, image_file in enumerate(image_files, 1):
            try:
                logging.info(f"Processing {i}/{len(image_files)}: {image_file.name}")

                # Detect objects in the image
                start_time = time.time()
                detected_objects = self.detector.detect_objects(image_file)
                detection_time = time.time() - start_time
                self.stats["detection_time"] += detection_time

                # Check if any target object was found
                target_found = False
                destination_folder = None

                for target_obj in self.target_objects:
                    if target_obj in detected_objects:
                        target_found = True
                        folder_name = target_obj.capitalize()
                        destination_folder = self.filtered_path / folder_name

                        # Special handling for white dog detection (only for original detector)
                        if (
                            target_obj == "dog"
                            and hasattr(self, "white_dog_mode")
                            and self.white_dog_mode
                            and self.detector_type == "yolov5n_original"
                            and hasattr(self.detector, "detect_white_dogs")
                        ):
                            # Check if it's specifically a white dog
                            if self.detector.detect_white_dogs(image_file):
                                folder_name = "White_Dog"
                                destination_folder = self.filtered_path / folder_name
                                logging.info(
                                    f"White dog specifically detected in {image_file.name}"
                                )
                            else:
                                # It's a dog but not white, skip if in white dog mode
                                target_found = False
                                continue
                        break

                # Move to appropriate folder
                if target_found:
                    if self.move_image_file(image_file, destination_folder):
                        self.stats["target_found"] += 1
                        logging.info(
                            f"✓ Found {target_obj}! Moved to {folder_name}/ (detection: {detection_time:.2f}s)"
                        )
                else:
                    # Move to 'Other' folder
                    other_folder = self.filtered_path / "Other"
                    if self.move_image_file(image_file, other_folder):
                        self.stats["moved_to_other"] += 1
                        logging.info(
                            f"○ No target objects found. Moved to Other/ (detection: {detection_time:.2f}s)"
                        )

                self.stats["total_processed"] += 1

                # Memory cleanup every 10 images
                if i % 10 == 0:
                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

            except Exception as e:
                logging.error(f"Error processing {image_file}: {e}")
                self.stats["errors"] += 1

        return True

    def print_summary(self):
        """Print processing summary."""
        logging.info("=" * 60)
        logging.info("PHOTO RECOGNITION COMPLETE")
        logging.info(
            f"Detection model: {self.detector_info['name'] if self.detector_info else self.detector_type}"
        )
        if self.detector_info:
            logging.info(f"Model description: {self.detector_info['description']}")
        logging.info(
            f"Target objects: {', '.join([obj.capitalize() for obj in self.target_objects])}"
        )
        logging.info(f"Total images processed: {self.stats['total_processed']}")
        logging.info(f"Images with target objects: {self.stats['target_found']}")
        logging.info(f"Images moved to 'Other': {self.stats['moved_to_other']}")
        logging.info(f"Processing errors: {self.stats['errors']}")

        if self.stats["detection_time"] > 0:
            avg_detection_time = self.stats["detection_time"] / max(
                1, self.stats["total_processed"]
            )
            logging.info(f"Average detection time: {avg_detection_time:.2f}s per image")

        if self.stats["total_processed"] > 0:
            success_rate = (
                (self.stats["target_found"] + self.stats["moved_to_other"])
                / self.stats["total_processed"]
            ) * 100
            logging.info(f"Success rate: {success_rate:.1f}%")

        logging.info("=" * 60)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Organize photos based on object detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python photo_recognition.py --detect dog
  python photo_recognition.py --detect "dog,cat,bird"
  python photo_recognition.py --detect person --confidence 0.6

Available objects (COCO dataset):
  person, bicycle, car, motorcycle, airplane, bus, train, truck, boat,
  traffic light, fire hydrant, stop sign, parking meter, bench, bird,
  cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe, backpack,
  umbrella, handbag, tie, suitcase, frisbee, skis, snowboard, sports ball,
  kite, baseball bat, baseball glove, skateboard, surfboard, tennis racket,
  bottle, wine glass, cup, fork, knife, spoon, bowl, banana, apple,
  sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake, chair,
  couch, potted plant, bed, dining table, toilet, tv, laptop, mouse,
  remote, keyboard, cell phone, microwave, oven, toaster, sink,
  refrigerator, book, clock, vase, scissors, teddy bear, hair drier,
  toothbrush
        """,
    )

    parser.add_argument(
        "--detect",
        type=str,
        required=True,
        help="Objects to detect (comma-separated for multiple objects)",
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.4,
        help="Detection confidence threshold (0.0-1.0, default: 0.4)",
    )

    parser.add_argument(
        "--base-path",
        type=str,
        help="Base path for the photo filter project (default: parent directory)",
    )

    args = parser.parse_args()

    # Check dependencies
    if not DEPENDENCIES_AVAILABLE:
        print(f"ERROR: Missing required dependencies: {MISSING_DEPENDENCY}")
        print("\nTo install required packages, run:")
        print("pip install torch torchvision pillow pandas")
        print("pip install ultralytics  # For YOLOv5")
        sys.exit(1)

    # Set up logging
    setup_logging()

    # Parse target objects
    target_objects = [obj.strip() for obj in args.detect.split(",")]

    # Determine base path
    if args.base_path:
        base_path = Path(args.base_path)
    else:
        # Use parent directory of RecognitionApp
        base_path = Path(__file__).parent.parent

    logging.info("=" * 60)
    logging.info("PHOTO RECOGNITION AND ORGANIZATION TOOL")
    logging.info("=" * 60)
    logging.info(f"Base path: {base_path}")
    logging.info(f"Target objects: {', '.join(target_objects)}")
    logging.info(f"Confidence threshold: {args.confidence}")

    # Check if source folder exists
    source_path = base_path / "ToProcess"
    if not source_path.exists():
        logging.error(f"Source folder does not exist: {source_path}")
        sys.exit(1)

    # Initialize and run photo organizer
    try:
        organizer = PhotoOrganizer(base_path, target_objects)
        organizer.detector.confidence_threshold = args.confidence

        # Create destination folders
        if not organizer.create_destination_folders():
            logging.error("Failed to create destination folders")
            sys.exit(1)

        # Process images
        success = organizer.process_images()

        # Print summary
        organizer.print_summary()

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        logging.info("\nProcessing interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
