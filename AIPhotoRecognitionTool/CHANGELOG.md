# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.5] - 2025-08-03

### Added
- **Progress Callbacks**: Enhanced progress reporting during deduplication
  - Real-time progress updates during file processing
  - Detailed status messages for each operation
  - Support for cancellation during long-running operations

### Fixed
- **Test Suite**: All tests now pass successfully
  - Fixed progress callback implementation in DeduplicationEngine
  - Resolved file handling issues in test cases
  - Improved test coverage and reliability

### Documentation
- Consolidated all documentation into README.md and CHANGELOG.md
- Removed redundant documentation files for better maintainability
- Added comprehensive usage examples and configuration guides

## [0.2.4] - 2025-08-02

### Added
- **Performance Optimizations**: Added selective metadata extraction based on enabled detection methods:
  - Skip EXIF extraction when metadata comparison is disabled
  - Skip perceptual hashing when visual similarity check is disabled
  - Added logging of active optimizations to help track performance improvements
  - Maintains full compatibility with existing deduplication functionality

### Fixed
- Reduced CPU and memory usage during image analysis
- Improved overall processing speed for large image collections

### Technical
- Refactored `extract_metadata` method to accept feature-specific flags
- Added optimization reporting to provide transparency on which optimizations are active

## [0.2.3] - 2025-07-28

### Added
- **Move to Organized Folders**: A new deduplication action that organizes duplicate files into `original/` and `duplicated/` folders.
  - Largest file from each group is moved to `original/`.
  - Other files are moved to `duplicated/`.
  - Handles filename conflicts with automatic numbering.
- **Safety First**: No files are deleted, ensuring zero data loss.

### Fixed
- Improved GUI feedback for deduplication mode.
- Enhanced error handling for missing dependencies.

### Documentation
- Updated `README.md` and `DEDUPLICATION_GUIDE.md` to include details about the new feature.

## [0.2.2] - 2025-07-28

### Fixed
- **AttributeError in Deduplication Mode**:
  - Resolved timing issue in GUI initialization causing AttributeError.
  - Added safety checks to ensure frames exist before accessing them.
  - Enhanced fallback GUI to include all required attributes.

### Updated
- **GUI Enhancements**:
  - Improved mode status display with dynamic feedback.
  - Added deduplication status indicator.
  - Enhanced `on_mode_change()` function for better user feedback.
  - Disabled deduplication radio button when engine is unavailable.
  - Added informative status messages for deduplication mode.

## [0.2.1] - 2025-07-28

### Removed
- Removed unnecessary placeholder folders (`Filtered/`, `ToProcess/`).
- Removed unused `test_images/` folder.
- Cleaned up `__pycache__/` folder.

### Updated
- Updated `.gitignore` to exclude `test_images/` folder.
- Streamlined repository for production readiness.

## [0.2.0] - 2025-07-28

### Added
- **🔍 Advanced Photo Deduplication Feature**
  - Multi-algorithm duplicate detection system
  - Visual similarity analysis using perceptual hashing (pHash, dHash, wHash)
  - EXIF metadata comparison (camera make/model, dimensions, settings)
  - Filename similarity matching with fuzzy string algorithms
  - File size comparison with configurable tolerance
  - MD5 hash comparison for exact duplicate detection
  - Configurable similarity threshold (0.5 - 1.0)
  - Multiple removal strategies (keep largest, keep oldest, preview only)
  - Export deduplication results to JSON format
  - Real-time progress tracking during analysis
  - Safe preview mode with confirmation dialogs

- **🖥️ Dual-Mode GUI Interface**
  - Mode switching between Object Detection and Deduplication
  - Intelligent component hiding/showing based on active mode
  - Dedicated deduplication controls panel
  - Detection method selection checkboxes
  - Action selection radio buttons
  - Results display with scrollable text area
  - Export and apply action buttons

- **🛡️ Enhanced Safety Features**
  - Preview mode as default setting to prevent accidental deletions
  - Confirmation dialogs before any file removal operations
  - Comprehensive logging of all deduplication activities
  - Cancel operation support during analysis
  - Detailed activity tracking with timestamps

- **📦 New Dependencies**
  - Added `imagehash>=4.2.0` for advanced visual similarity detection
  - Enhanced dependency management with graceful fallbacks
  - Automatic installation prompts for missing components

- **📚 Comprehensive Documentation**
  - New `DEDUPLICATION_GUIDE.md` with detailed usage instructions
  - Updated README.md with deduplication feature overview
  - Code documentation and inline comments
  - Multiple test scripts for feature verification

### Changed
- GUI window title updated to reflect new capabilities
- Controls section reorganized with mode selection
- Progress tracking enhanced to support both detection and deduplication
- Main application description updated to mention deduplication

### Technical Improvements
- Modular architecture with separate deduplication engine
- Thread-safe background processing for both modes
- Memory-efficient batch processing for large image collections
- Clean separation between detection and deduplication logic
- Graceful degradation when optional dependencies are missing

## [0.1.2] - 2025-07-28

### Added
- README now lists all supported AI models and recommended GPU VRAM for each model.
- README includes a clear explanation of the confidence threshold and its effect on detection results.

### Changed
- Default input folder is now the Windows 'Pictures' folder; output defaults to 'AIPhotoRecognitionTool' inside 'Pictures'.
- Folder entry fields in the GUI are now readonly and can only be changed using the folder selector.
- No folders are created by default; only subfolders are created inside the selected output folder during processing.

### Fixed
- Prevented manual clearing/editing of folder paths in the GUI.

## [0.1.1] - 2025-07-28

### Changed
- **BREAKING**: Removed pre-bundled model files from repository
- Models are now downloaded automatically by the application on first use
- Removed unnecessary ultralytics_yolov5_master folder - app uses pip-installed ultralytics
- Cleaned up repository structure for better distribution

### Removed
- Large model files (*.pt) - reduces repository size by ~33MB
- models/ultralytics_yolov5_master/ folder - uses system-installed ultralytics instead
- Filtered/ folder from repository - created dynamically by application

### Technical Improvements
- Repository size reduced significantly
- Faster cloning and distribution
- Models cached locally after first download
- Cleaner project structure

## [0.1.0] - 2025-07-28

### Added
- Initial release of AI Photo Recognition Tool
- Modern GUI interface with Tkinter
- Multiple AI model support:
  - YOLOv5 (automatic download)
  - YOLOv8 (automatic download)
  - RT-DETR support
  - Ensemble mode for maximum accuracy
- Advanced object detection with custom detectors
- Batch photo processing with progress tracking
- Automatic folder organization by detected objects
- Confidence threshold adjustment
- Robust dependency management with auto-installation
- Cross-platform support (Windows, Linux, macOS)

### Features
- **Source & Output Folder Selection**: Easy directory browsing
- **Object Detection Categories**: Predefined and custom object detection
- **Model Selection**: Choose from multiple AI models based on needs
- **Real-time Progress**: Live progress tracking during batch processing
- **Error Handling**: Comprehensive error handling and user feedback
- **Settings Persistence**: GUI settings saved between sessions

### Technical Details
- Built with Python 3.8+
- Core dependencies: PyTorch, Ultralytics, OpenCV, Pillow
- Modern GUI using Tkinter with custom styling
- Modular architecture for easy extension
- Automated dependency installation
- Memory-efficient processing for large image batches

### Installation
- Simple installation via `install.bat` or `pip install -r requirements.txt`
- One-click execution via `run.bat` or `python photo_recognition_gui_production.py`
- Alternative launcher via `launcher.py`
