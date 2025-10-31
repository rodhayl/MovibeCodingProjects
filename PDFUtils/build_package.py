"""Build a standalone executable for PDFUtils using PyInstaller.

Non-breaking helper that can be used locally:

  python build_package.py --name PDFUtils --onefile --windowed
  python build_package.py --onedir --extras core  # faster dev build
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


def _is_module_available(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except Exception:
        return False


def build(
    *,
    name: str,
    onefile: bool,
    onedir: bool,
    windowed: bool,
    icon: str | None,
    extras: str,
) -> int:
    try:
        import PyInstaller  # noqa: F401
    except Exception:
        print("PyInstaller not found. Installing into current environment...")
        code = subprocess.call([sys.executable, "-m", "pip", "install", "pyinstaller"])  # best effort
        if code != 0:
            print("Failed to install pyinstaller. Please install it manually.")
            return code

    cmd: List[str] = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--name",
        name,
    ]
    if onefile and onedir:
        onedir = False
    if onefile:
        cmd.append("--onefile")
    if onedir:
        cmd.append("--onedir")
    if windowed:
        cmd.append("--windowed")
    if icon:
        cmd.extend(["--icon", icon])

    groups = {
        "minimal": ["fitz", "PIL"],
        "core": ["fitz", "PIL", "pytesseract", "ttkbootstrap"],
        "all": [
            "fitz",
            "PIL",
            "pytesseract",
            "ttkbootstrap",
            "camelot",
            "pdfplumber",
            "pyzbar",
            "segno",
            "kraken",
            "sentry_sdk",
        ],
    }
    for mod in groups.get(extras, groups["core"]):
        if _is_module_available(mod):
            cmd.extend(["--hidden-import", mod])

    entry = str(Path("pdfutils") / "__main__.py")
    cmd.append(entry)

    print("Running:")
    print(" ".join(cmd))
    return subprocess.call(cmd)


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build a standalone executable for PDFUtils")
    ap.add_argument("--name", default="PDFUtils", help="Executable name")
    ap.add_argument("--onefile", action="store_true", help="Create a single-file bundle")
    ap.add_argument("--onedir", action="store_true", help="Create a directory bundle")
    ap.add_argument("--windowed", action="store_true", help="Build a GUI app without console")
    ap.add_argument("--icon", help="Path to application icon (.ico/.icns)")
    ap.add_argument("--extras", choices=["minimal", "core", "all"], default="core")
    args = ap.parse_args(argv)
    return build(
        name=args.name,
        onefile=args.onefile,
        onedir=args.onedir,
        windowed=args.windowed,
        icon=args.icon,
        extras=args.extras,
    )


if __name__ == "__main__":
    raise SystemExit(main())
