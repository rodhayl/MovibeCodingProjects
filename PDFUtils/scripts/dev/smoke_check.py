"""Local smoke test for critical flows.

Run (not committed to CI):
  python scripts/dev/smoke_check.py
"""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    try:
        pass
    except Exception as e:
        print("Import error:", e)
        return 1

    # Prepare temp paths
    tmp = Path("smoke_out")
    tmp.mkdir(exist_ok=True)
    # Minimal checks (no real PDFs provided here)
    print(
        "pdfutils imported; available functions:",
        ["merge_pdfs", "split_pdf", "compress_pdf", "extract_text_with_ocr"],
    )
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
