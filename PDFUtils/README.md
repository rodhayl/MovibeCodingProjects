# PDFUtils: Desktop PDF Processing and OCR Prototype

**Status:** Learning-oriented proof of concept with Python source, automated test code and a Windows executable. Document compatibility and optional OCR backends require environment-specific testing.

PDFUtils brings PDF merging, splitting, compression and extraction into a desktop interface, with optional workflows for OCR, tables, barcodes and handwriting recognition. The project demonstrates modular document-processing integration, dependency-aware UI components and packaging. Keep backups of input documents and review extracted content, especially when using OCR or unfamiliar PDF formats.

## What this project demonstrates

- Core PDF operations separated from GUI components and feature tabs.
- Integration of PDF/OCR libraries and optional system dependencies.
- Tests for document operations, error conditions, launcher behavior and GUI workflows.
- Windows packaging alongside a source-run application.

This is a PoC for evaluation and learning. Feature presence and test code do not establish production readiness, accessibility conformance or correct handling of every PDF.

## Windows executable

[Download PDFUtils.exe](dist/PDFUtils/PDFUtils.exe)

The executable is versioned in this repository under `dist/PDFUtils/PDFUtils.exe`. It can be evaluated without a separate Python installation. Its presence does not certify compatibility with every Windows environment; use sample documents first.

## Install from source

```bash
git clone https://github.com/rodhayl/MovibeCodingProjects.git
cd MovibeCodingProjects/PDFUtils
python -m venv .venv
```

Activate the environment before installing dependencies:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

```bash
# Linux/macOS shell
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The project metadata declares Python 3.8+, but the resolved dependencies and optional OCR packages can require a newer or specific Python version. Check installation errors and dependency compatibility in your environment. Windows has a committed executable; other platforms use the source route and need separate validation.

## Run

```bash
python pdfutils_launcher.py
```

The launcher can create its own `.pdfutils_venv` and install dependencies. Review its prompts if you already manage a virtual environment. The UI and available features depend on installed libraries and system tools.

## Core operations

| Tab | Operation |
| --- | --- |
| Merge | Add, remove and reorder PDFs before merging |
| Split | Split a PDF into two parts |
| Compress | Use available PyMuPDF/Ghostscript backends and quality presets |
| Extract | Export a selected page range |

Output names are suggested from the input files. Check the output path and resulting document before replacing an original.

Core libraries include `pypdf` for PDF manipulation and PyMuPDF for supported compression/processing paths. Ghostscript is an optional system backend and must be discoverable on `PATH` (`gs`, `gswin64c`, etc.).

## OCR and extraction

Additional tabs and processing paths cover:

- Standard, batch and zonal OCR using Tesseract, with language/model selection.
- Image preprocessing such as thresholding, contrast, deskew and denoise.
- Table extraction through Camelot/pdfplumber and structured export.
- Barcode/QR extraction.
- Handwriting OCR through optional Kraken integration.

OCR quality depends on the scan, language, preprocessing and selected model. Review text, tables and coordinates before using extracted results. Kraken is not enabled in the current requirements file because of a documented Python compatibility issue; the presence of its integration is not a claim that it runs in the default environment.

### Optional/system dependencies

- **Tesseract:** install the system OCR executable and required language packs.
- **Ghostscript:** install when using the corresponding compression or PDF processing path.
- **Barcode support:** `pyzbar` can require the platform's ZBar libraries.
- **Handwriting:** install a compatible Kraken version and models in a suitable environment.
- **GUI/headless tests:** a display or virtual display and the relevant GUI libraries are required.

The consolidated [requirements.txt](requirements.txt) includes application and test dependencies. Review optional features before adding more packages.

## Development and testing

From the `PDFUtils` directory:

```bash
python -m pytest -q --cov=pdfutils --cov-config=.coveragerc --cov-report=term-missing
python -m unittest tests/test_launcher.py
```

On a headless Linux host with Xvfb installed, the relevant GUI suite can be run under a virtual display, for example `xvfb-run -a python -m pytest`. Optional tools/models can change which tests execute or skip.

Tests cover specific operations and scenarios; they do not prove that every PDF or UI path works. No current coverage percentage is asserted here. When reporting coverage, include the commit, command, included modules, skipped tests and optional dependencies. Inspect [.coveragerc](.coveragerc) for the actual measurement scope.

## Build a Windows executable

```bash
python -m pip install pyinstaller
python build_package.py --name PDFUtils --onefile --windowed
```

See `python build_package.py --help` for the supported options, including directory bundles and dependency selection. Building a package is separate from testing its installation and runtime behavior.

## Repository layout

```text
pdfutils/pdf_ops.py       document-processing operations
pdfutils/gui/components/ reusable GUI components
pdfutils/tabs/           feature-specific UI tabs
pdfutils/responsive_app.py
pdfutils_launcher.py     source launcher
tests/                  operation, launcher and GUI tests
docs/                   component documentation
```

[Component usage](docs/component_usage.md) documents the UI building blocks.

## License

See [LICENSE](LICENSE) for this project's terms. Dependencies and externally installed tools retain their own licenses; review the obligations for the combination you distribute.
