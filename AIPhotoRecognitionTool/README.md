# AI Photo Recognition Tool

AI-powered photo organization and deduplication system with object detection capabilities.

## Features

- **Object Detection**: Detect and classify objects in photos using YOLOv5, YOLOv8, and RT-DETR models
- **Photo Deduplication**: Find and remove duplicate photos using multiple detection algorithms
- **Smart Organization**: Automatically organize photos into folders based on detected objects
- **GPU Acceleration**: Supports CUDA (NVIDIA), AMD DirectML, and CPU processing
- **Modern GUI**: User-friendly interface with real-time progress tracking
- **Batch Processing**: Process entire folders of images efficiently

## Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/AIPhotoRecognitionTool.git
cd AIPhotoRecognitionTool

# Run with automatic dependency installation
start.bat
```

### Manual Installation

```bash
pip install -r requirements.txt
python photo_recognition_gui_production.py
```

## Usage

### Object Detection Mode

1. Launch the application
2. Select "🎯 Object Detection" mode
3. Choose source folder with images
4. Select objects to detect (person, car, animal, etc.)
5. Click "▶️ Start Detection"
6. Photos will be organized into folders by detected objects

### Deduplication Mode

1. Launch the application
2. Select "🔍 Deduplication" mode
3. Choose detection methods:
   - File name similarity
   - File size comparison
   - Visual similarity (perceptual hashing)
   - Metadata analysis (EXIF data)
4. Select folder to scan
5. Click "▶️ Find Duplicates"
6. Review and remove duplicates

## Requirements

- Python 3.8 or higher
- Windows 10/11 (AMD DirectML support)
- Linux (ROCm support for AMD GPUs)
- CUDA-capable GPU (optional, for NVIDIA acceleration)

## GPU Acceleration

The application automatically detects and configures GPU acceleration:
- **NVIDIA GPUs**: CUDA support (auto-detected)
- **AMD GPUs**: DirectML on Windows, ROCm on Linux
- **CPU Mode**: Fallback when no GPU is available

To force a specific accelerator:
```bash
# Windows PowerShell
$env:PHOTOFILTER_TORCH_ACCELERATOR = 'cuda'  # or 'amd' or 'cpu'
python photo_recognition_gui_production.py

# Or pass to start.bat
start.bat cuda
```

## Supported Models

- YOLOv5 (fast, reliable)
- YOLOv8 (newest, most accurate)
- RT-DETR (transformer-based)
- Ensemble Mode (combines multiple models)

Models are automatically downloaded on first use.

## Project Structure

```
AIPhotoRecognitionTool/
├── photo_recognition_gui_production.py  # Main GUI application
├── src/                                 # Source code modules
│   ├── deduplication/                  # Duplicate detection engine
│   ├── detection/                      # Object detection models
│   └── gui/                           # GUI components
├── scripts/                            # Utility scripts
├── tests/                              # Unit tests
└── requirements.txt                    # Python dependencies
```

## Author

Created by Rulfe - 2025
