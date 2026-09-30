# AI Photo Recognition Tool: Desktop Photo Organization and Deduplication

**Status:** Experimental desktop application, marked Beta in its package metadata, with source, tests and a [Windows executable artifact](dist/PhotoFilter.exe).

AI Photo Recognition Tool combines object-detection model adapters with photo organization and duplicate-review workflows. It explores how pretrained computer-vision models, perceptual hashing and a desktop interface can work together for batch photo management. Detection results and similarity scores need review; model downloads, hardware support and performance depend on the selected backend and environment.

## What this project demonstrates

- A common detector interface with YOLOv5, YOLOv8 and RT-DETR integrations.
- Batch organization by detected objects and duplicate-candidate review.
- Perceptual hashing, file/metadata comparisons and desktop progress feedback.
- CPU/GPU configuration, tests and packaging for an applied computer-vision workflow.

A similarity threshold is not a measured accuracy rate. Keep backups and review duplicate candidates before deleting files. No project-specific accuracy, speed or universal hardware-compatibility benchmark is claimed here.

## Installation

### Windows quick start

```powershell
git clone https://github.com/rodhayl/MovibeCodingProjects.git
cd MovibeCodingProjects/AIPhotoRecognitionTool
.\start.bat
```

The launcher can install dependencies. Review installation choices and use a dedicated environment. A prebuilt [PhotoFilter.exe](dist/PhotoFilter.exe) is also stored in the repository; evaluate it on sample images before working on a photo library.

### Manual installation

```bash
python -m venv .venv
# Activate .venv for your shell, then:
python -m pip install -r requirements.txt
python photo_recognition_gui_production.py
```

The package metadata declares Python 3.8+, but current PyTorch and other dependencies may impose stricter version/platform requirements. The word `production` in the historical launcher filename is not a readiness guarantee.

## Usage

### Object detection

1. Launch the application and select Object Detection mode.
2. Choose a source folder, model and objects of interest.
3. Start detection and inspect the output organization and progress.
4. Review results against the originals; detections can be missed or incorrect.

### Deduplication

1. Select Deduplication mode and a folder to scan.
2. Choose comparison methods: names, sizes, visual/perceptual similarity and available metadata.
3. Scan for duplicate candidates and review each proposed group.
4. Keep a backup before removing files, including candidates that look similar but are not interchangeable.

## Models and data boundaries

The detector adapters use pretrained YOLOv5, YOLOv8 and RT-DETR models, with an ensemble option described in the application. Model files can be downloaded on first use. Dependency installation and model retrieval require network access; check the libraries' settings and licenses before using personal photos.

Local inference does not by itself establish an audited privacy guarantee. Model/backend choice affects resource use and output quality. “Newest” or “most accurate” labels are not used here without a dated project evaluation.

## CPU and GPU configuration

The project includes CPU fallback and configuration for NVIDIA CUDA and AMD-related accelerators. Availability depends on operating system, drivers, PyTorch builds and the chosen model. Do not infer tested support for a device from the presence of a configuration option.

```powershell
# Windows PowerShell; supported launcher choices include cuda, amd and cpu
$env:PHOTOFILTER_TORCH_ACCELERATOR = 'cpu'
python photo_recognition_gui_production.py

# Or select an accelerator through the Windows launcher
.\start.bat cuda
```

See [installer helpers](scripts/install_gpu_deps.py) and [detector adapters](src/photofilter/core/detectors.py) for implementation details. Validate with a small sample before a large batch.

## Development and tests

```bash
python -m pytest tests
```

The repository includes detector, recognition, deduplication, GUI and installer tests. Some checks need models, optional dependencies or a display. Record the commit, hardware/backend, executed tests and skips when sharing results. The nested `.github/workflows/ci.yml` is retained project material; it is not a root-level GitHub Actions workflow for the collection repository.

## Project structure

```text
photo_recognition_gui_production.py  application entry point
src/photofilter/core/               detection and deduplication logic
src/photofilter/gui/                desktop interface
src/photofilter/utils/              scanning helpers
scripts/                           installers, launchers and scenarios
tests/                             automated test code
dist/PhotoFilter.exe               Windows artifact
```

## Credits and license

Originally documented as “Created by Rulfe - 2025”. Pretrained models and third-party libraries retain their own authorship and terms. See [LICENSE](LICENSE) and the relevant dependency/model licenses.
