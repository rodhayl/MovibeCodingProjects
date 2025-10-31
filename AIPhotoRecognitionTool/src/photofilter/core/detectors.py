#!/usr/bin/env python3
"""
Advanced Object Detection Models

This module provides multiple state-of-the-art object detection models
with different accuracy/speed trade-offs for enhanced photo recognition.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

try:
    import torch
    from PIL import Image, ImageFile
    import numpy as np

    DEPENDENCIES_AVAILABLE = True
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    NumpyArray = np.ndarray
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    MISSING_DEPENDENCY = str(e)
    NumpyArray = object


class BaseDetector(ABC):
    """Abstract base class for all detectors."""

    def __init__(self, confidence_threshold: float = 0.25):
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.device = None
        self.class_names = []
        self.model_name = "Base"
        self.description = "Base detector class"

    @abstractmethod
    def initialize_model(self) -> bool:
        """Initialize the detection model."""
        pass

    @abstractmethod
    def detect_objects(self, image_path: Path) -> List[str]:
        """Detect objects in an image."""
        pass

    def get_info(self) -> Dict[str, str]:
        """Get detector information."""
        return {
            "name": self.model_name,
            "description": self.description,
            "accuracy": "Unknown",
            "speed": "Unknown",
            "memory": "Unknown",
        }


class YOLOv5Detector(BaseDetector):
    """Enhanced YOLOv5 detector with multiple model sizes."""

    def __init__(
        self,
        model_size: str = "n",
        confidence_threshold: float = 0.25,
        iou_threshold: float = 0.45,
    ):
        super().__init__(confidence_threshold)
        self.model_size = model_size  # n, s, m, l, x
        self.iou_threshold = iou_threshold
        self.model_name = f"YOLOv5{model_size.upper()}"
        self.augment_inference = True
        self.use_multi_scale = True

        # Model-specific settings
        self.model_configs = {
            "n": {
                "description": "Nano - Fastest, lowest accuracy",
                "accuracy": "⭐⭐⭐",
                "speed": "⭐⭐⭐⭐⭐",
                "memory": "⭐⭐⭐⭐⭐",
            },
            "s": {
                "description": "Small - Balanced speed/accuracy",
                "accuracy": "⭐⭐⭐⭐",
                "speed": "⭐⭐⭐⭐",
                "memory": "⭐⭐⭐⭐",
            },
            "m": {
                "description": "Medium - Higher accuracy",
                "accuracy": "⭐⭐⭐⭐⭐",
                "speed": "⭐⭐⭐",
                "memory": "⭐⭐⭐",
            },
            "l": {
                "description": "Large - High accuracy",
                "accuracy": "⭐⭐⭐⭐⭐",
                "speed": "⭐⭐",
                "memory": "⭐⭐",
            },
            "x": {
                "description": "Extra Large - Highest accuracy",
                "accuracy": "⭐⭐⭐⭐⭐",
                "speed": "⭐",
                "memory": "⭐",
            },
        }

        config = self.model_configs.get(model_size, self.model_configs["n"])
        self.description = config["description"]

    def get_info(self) -> Dict[str, str]:
        """Get YOLOv5 detector information."""
        config = self.model_configs.get(self.model_size, self.model_configs["n"])
        return {
            "name": self.model_name,
            "description": config["description"],
            "accuracy": config["accuracy"],
            "speed": config["speed"],
            "memory": config["memory"],
        }

    def initialize_model(self) -> bool:
        """Initialize YOLOv5 model with specified size."""
        try:
            # Device selection: CUDA -> DirectML (Windows) -> CPU
            pref = os.getenv("PHOTOFILTER_TORCH_ACCELERATOR", "auto").lower()
            is_windows = sys.platform.startswith("win")

            self.device = torch.device("cpu")
            used = "cpu"

            # Prefer CUDA when requested or available in auto
            if pref == "cuda" or (pref == "auto" and torch.cuda.is_available()):
                if torch.cuda.is_available():
                    try:
                        gpu_memory = torch.cuda.get_device_properties(
                            0
                        ).total_memory / (1024**3)
                        logging.info(f"CUDA available. GPU memory: {gpu_memory:.1f}GB")
                    except Exception:
                        logging.info("CUDA available.")
                    self.device = torch.device("cuda")
                    used = "cuda"
                else:
                    logging.warning("CUDA requested but not available. Falling back.")

            # AMD path: DirectML on Windows when requested or in auto without CUDA
            if used == "cpu" and (
                pref == "amd" or (pref == "auto" and not torch.cuda.is_available())
            ):
                if is_windows:
                    try:
                        import torch_directml  # type: ignore

                        self.device = torch_directml.device()
                        used = "directml"
                        logging.info("Using DirectML device for AMD on Windows")
                    except Exception as dml_e:
                        logging.warning(f"DirectML not available ({dml_e}). Using CPU")
                else:
                    # On Linux, ROCm builds expose CUDA-like APIs; torch.cuda.is_available() may be True.
                    # If not, we stay on CPU.
                    pass

            logging.info(f"Selected device: {used if used != 'cuda' else 'cuda'}")

            # Safety fallback for very large models on limited VRAM
            if used == "cuda":
                try:
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory / (
                        1024**3
                    )
                    if self.model_size in ["x", "l"] and gpu_memory < 4.0:
                        logging.warning(
                            f"Large model {self.model_size} may not fit in {gpu_memory:.1f}GB GPU memory"
                        )
                        if gpu_memory < 2.5:
                            logging.info("Switching to CPU for large model")
                            self.device = torch.device("cpu")
                            used = "cpu"
                except Exception:
                    pass

            # Load model
            logging.info(f"Loading YOLOv5{self.model_size} model...")
            # Ensure a valid torch.hub cache directory (avoid conflicts with files named 'models')
            try:
                hub_dir = Path.cwd() / "model_cache"
                if hub_dir.exists() and not hub_dir.is_dir():
                    # If a conflicting file exists, use a hidden fallback directory
                    logging.warning(
                        f"Path {hub_dir} exists and is not a directory. Using fallback .model_cache"
                    )
                    hub_dir = Path.cwd() / ".model_cache"
                hub_dir.mkdir(parents=True, exist_ok=True)
                torch.hub.set_dir(str(hub_dir))
                logging.info(f"torch.hub cache dir set to: {hub_dir}")
            except Exception as cache_e:
                logging.warning(f"Could not set torch.hub cache dir: {cache_e}")

            self.model = torch.hub.load(
                "ultralytics/yolov5",
                f"yolov5{self.model_size}",
                pretrained=True,
                verbose=True,
                trust_repo=True,
            )

            # Configure model
            self.model.to(self.device)
            self.model.eval()

            # Enhanced settings
            self.model.conf = self.confidence_threshold
            self.model.iou = self.iou_threshold
            self.model.agnostic = False
            self.model.multi_label = True
            self.model.max_det = 1000

            if self.augment_inference:
                self.model.augment = True

            self.class_names = self.model.names

            logging.info(
                f"✅ {self.model_name} model loaded successfully on {self.device}"
            )
            logging.info(f"Available classes: {len(self.class_names)} classes")

            return True

        except Exception as e:
            logging.error(f"Failed to initialize {self.model_name}: {e}")
            return False

    def detect_objects(self, image_path: Path) -> List[str]:
        """Enhanced object detection with multi-scale inference."""
        try:
            image = Image.open(image_path).convert("RGB")

            # Determine optimal input size based on model
            size_map = {"n": 640, "s": 640, "m": 832, "l": 1024, "x": 1280}
            max_size = size_map.get(self.model_size, 640)

            if self.device.type == "cpu":
                max_size = min(max_size, 640)  # Limit CPU processing

            detected_objects = []

            # Multi-scale detection for better accuracy
            if self.use_multi_scale and self.model_size in ["m", "l", "x"]:
                scales = [max_size, int(max_size * 0.8), int(max_size * 1.2)]
            else:
                scales = [max_size]

            all_detections = []

            for scale in scales:
                test_image = image.copy()
                if max(test_image.size) > scale:
                    test_image.thumbnail((scale, scale), Image.Resampling.LANCZOS)

                with torch.no_grad():
                    if self.augment_inference:
                        # Test-time augmentation
                        results1 = self.model(test_image)
                        results2 = self.model(
                            test_image.transpose(Image.FLIP_LEFT_RIGHT)
                        )

                        for r in [results1, results2]:
                            for detection in r.pandas().xyxy[0].itertuples():
                                all_detections.append(
                                    {
                                        "name": detection.name.lower(),
                                        "confidence": detection.confidence,
                                        "scale": scale,
                                    }
                                )
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

            # Aggregate detections across scales
            detection_counts = {}
            for det in all_detections:
                name = det["name"]
                if name not in detection_counts:
                    detection_counts[name] = {"count": 0, "max_conf": 0}
                detection_counts[name]["count"] += 1
                detection_counts[name]["max_conf"] = max(
                    detection_counts[name]["max_conf"], det["confidence"]
                )

            # Filter by confidence and count
            for name, stats in detection_counts.items():
                if stats["max_conf"] >= self.confidence_threshold:
                    detected_objects.append(name)

            return list(set(detected_objects))

        except Exception as e:
            logging.error(f"Detection failed for {image_path}: {e}")
            return []


class YOLOv8Detector(BaseDetector):
    """YOLOv8 detector with ultralytics implementation."""

    def __init__(self, model_size: str = "n", confidence_threshold: float = 0.25):
        super().__init__(confidence_threshold)
        self.model_size = model_size
        self.model_name = f"YOLOv8{model_size.upper()}"
        self.description = f"YOLOv8{model_size.upper()} - Latest YOLO architecture"

    def initialize_model(self) -> bool:
        """Initialize YOLOv8 model."""
        try:
            from ultralytics import YOLO

            # Device selection
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

            # Load model
            logging.info(f"Loading YOLOv8{self.model_size} model...")
            self.model = YOLO(f"yolov8{self.model_size}.pt")

            # Get class names
            self.class_names = self.model.names

            logging.info(f"✅ {self.model_name} model loaded successfully")
            return True

        except ImportError:
            logging.error("YOLOv8 requires: pip install ultralytics")
            return False
        except Exception as e:
            logging.error(f"Failed to initialize {self.model_name}: {e}")
            return False

    def detect_objects(self, image_path: Path) -> List[str]:
        """YOLOv8 object detection."""
        try:
            results = self.model(
                str(image_path), conf=self.confidence_threshold, device=self.device
            )

            detected_objects = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.class_names[class_id].lower()
                    detected_objects.append(class_name)

            return list(set(detected_objects))

        except Exception as e:
            logging.error(f"YOLOv8 detection failed for {image_path}: {e}")
            return []


class RTDETRDetector(BaseDetector):
    """RT-DETR (Real-Time Detection Transformer) detector."""

    def __init__(self, model_size: str = "l", confidence_threshold: float = 0.25):
        super().__init__(confidence_threshold)
        self.model_size = model_size
        self.model_name = f"RT-DETR-{model_size.upper()}"
        self.description = f"RT-DETR - Transformer-based real-time detection"

    def get_info(self) -> Dict[str, str]:
        """Get RT-DETR detector information."""
        return {
            "name": self.model_name,
            "description": "Real-Time Detection Transformer - State-of-the-art accuracy",
            "accuracy": "⭐⭐⭐⭐⭐",
            "speed": "⭐⭐⭐",
            "memory": "⭐⭐",
        }

    def initialize_model(self) -> bool:
        """Initialize RT-DETR model."""
        try:
            from ultralytics import RTDETR

            self.device = "cuda" if torch.cuda.is_available() else "cpu"

            logging.info(f"Loading RT-DETR-{self.model_size} model...")
            self.model = RTDETR(f"rtdetr-{self.model_size}.pt")

            self.class_names = self.model.names

            logging.info(f"✅ {self.model_name} model loaded successfully")
            return True

        except ImportError:
            logging.error("RT-DETR requires: pip install ultralytics")
            return False
        except Exception as e:
            logging.error(f"Failed to initialize {self.model_name}: {e}")
            return False

    def detect_objects(self, image_path: Path) -> List[str]:
        """RT-DETR object detection."""
        try:
            results = self.model(
                str(image_path), conf=self.confidence_threshold, device=self.device
            )

            detected_objects = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.class_names[class_id].lower()
                    detected_objects.append(class_name)

            return list(set(detected_objects))

        except Exception as e:
            logging.error(f"RT-DETR detection failed for {image_path}: {e}")
            return []


class EnsembleDetector(BaseDetector):
    """Ensemble detector combining multiple models for maximum accuracy."""

    def __init__(self, detectors: List[BaseDetector], vote_threshold: int = 2):
        super().__init__()
        self.detectors = detectors
        self.vote_threshold = vote_threshold
        self.model_name = "Ensemble"
        self.description = f"Ensemble of {len(detectors)} models - Maximum accuracy"

    def get_info(self) -> Dict[str, str]:
        """Get ensemble detector information."""
        return {
            "name": self.model_name,
            "description": f"Ensemble of {len(self.detectors)} models",
            "accuracy": "⭐⭐⭐⭐⭐",
            "speed": "⭐",
            "memory": "⭐",
        }

    def initialize_model(self) -> bool:
        """Initialize all ensemble models."""
        success_count = 0
        for detector in self.detectors:
            if detector.initialize_model():
                success_count += 1

        if success_count == 0:
            logging.error("No ensemble models initialized successfully")
            return False

        logging.info(
            f"✅ Ensemble initialized with {success_count}/{len(self.detectors)} models"
        )
        return True

    def detect_objects(self, image_path: Path) -> List[str]:
        """Ensemble detection with voting."""
        try:
            all_detections = {}

            # Get detections from all models
            for detector in self.detectors:
                if detector.model is not None:
                    detections = detector.detect_objects(image_path)
                    for obj in detections:
                        if obj not in all_detections:
                            all_detections[obj] = 0
                        all_detections[obj] += 1

            # Apply voting threshold
            final_detections = []
            for obj, votes in all_detections.items():
                if votes >= self.vote_threshold:
                    final_detections.append(obj)

            return final_detections

        except Exception as e:
            logging.error(f"Ensemble detection failed for {image_path}: {e}")
            return []


# Available detector configurations
AVAILABLE_DETECTORS = {
    "yolov5n": {
        "class": YOLOv5Detector,
        "args": {"model_size": "n"},
        "name": "YOLOv5n",
        "description": "Fastest, lowest memory usage",
        "accuracy": "⭐⭐⭐",
        "speed": "⭐⭐⭐⭐⭐",
        "memory": "⭐⭐⭐⭐⭐",
    },
    "yolov5s": {
        "class": YOLOv5Detector,
        "args": {"model_size": "s"},
        "name": "YOLOv5s",
        "description": "Balanced speed and accuracy",
        "accuracy": "⭐⭐⭐⭐",
        "speed": "⭐⭐⭐⭐",
        "memory": "⭐⭐⭐⭐",
    },
    "yolov5m": {
        "class": YOLOv5Detector,
        "args": {"model_size": "m"},
        "name": "YOLOv5m",
        "description": "Medium model - good accuracy",
        "accuracy": "⭐⭐⭐⭐⭐",
        "speed": "⭐⭐⭐",
        "memory": "⭐⭐⭐",
    },
    "yolov5l": {
        "class": YOLOv5Detector,
        "args": {"model_size": "l"},
        "name": "YOLOv5l",
        "description": "Large model - high accuracy",
        "accuracy": "⭐⭐⭐⭐⭐",
        "speed": "⭐⭐",
        "memory": "⭐⭐",
    },
    "yolov5x": {
        "class": YOLOv5Detector,
        "args": {"model_size": "x"},
        "name": "YOLOv5x",
        "description": "Extra large - highest accuracy",
        "accuracy": "⭐⭐⭐⭐⭐",
        "speed": "⭐",
        "memory": "⭐",
    },
    "yolov8n": {
        "class": YOLOv8Detector,
        "args": {"model_size": "n"},
        "name": "YOLOv8n",
        "description": "Latest YOLO - nano size",
        "accuracy": "⭐⭐⭐⭐",
        "speed": "⭐⭐⭐⭐⭐",
        "memory": "⭐⭐⭐⭐⭐",
    },
    "yolov8s": {
        "class": YOLOv8Detector,
        "args": {"model_size": "s"},
        "name": "YOLOv8s",
        "description": "Latest YOLO - small size",
        "accuracy": "⭐⭐⭐⭐⭐",
        "speed": "⭐⭐⭐⭐",
        "memory": "⭐⭐⭐⭐",
    },
    "rtdetr": {
        "class": RTDETRDetector,
        "args": {"model_size": "l"},
        "name": "RT-DETR",
        "description": "Transformer-based detection",
        "accuracy": "⭐⭐⭐⭐⭐",
        "speed": "⭐⭐⭐",
        "memory": "⭐⭐",
    },
}


def create_detector(
    detector_type: str, confidence_threshold: float = 0.25
) -> Optional[BaseDetector]:
    """Factory function to create detector instances."""
    if detector_type not in AVAILABLE_DETECTORS:
        logging.error(f"Unknown detector type: {detector_type}")
        return None

    config = AVAILABLE_DETECTORS[detector_type]
    detector_class = config["class"]
    args = config["args"].copy()
    args["confidence_threshold"] = confidence_threshold

    try:
        return detector_class(**args)
    except Exception as e:
        logging.error(f"Failed to create {detector_type} detector: {e}")
        return None


def create_ensemble_detector(
    detector_types: List[str],
    confidence_threshold: float = 0.25,
    vote_threshold: int = 2,
) -> Optional[EnsembleDetector]:
    """Create an ensemble detector from multiple detector types."""
    detectors = []
    for detector_type in detector_types:
        detector = create_detector(detector_type, confidence_threshold)
        if detector:
            detectors.append(detector)

    if not detectors:
        logging.error("No valid detectors for ensemble")
        return None

    return EnsembleDetector(detectors, vote_threshold)
