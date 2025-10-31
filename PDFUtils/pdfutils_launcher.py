"""
Launcher shim with a self-contained fallback.

It first attempts to import the historical implementation from
`scripts/launcher/pdfutils_launcher.py` to preserve compatibility with
existing setups and test scaffolding. If that import fails, it falls back to
an internal implementation that:

- Creates/uses a virtual environment (path taken from `pdfutils_launcher.cfg`
  if available, else `.pdfutils_venv`).
- Installs runtime dependencies via pip and attempts to install feature
  extras individually with best-effort fallbacks.
- Skips known-incompatible packages (e.g., kraken on Windows / Python >= 3.13)
  while ensuring the app remains usable (handwriting OCR falls back to
  pytesseract).
- Launches the app via `python -m pdfutils`.
"""

from __future__ import annotations

import configparser
import importlib
import importlib.util
import os
import platform
import subprocess
import sys
from pathlib import Path
from types import ModuleType


def _load_impl() -> ModuleType:
    """Load the real launcher module from scripts/launcher/pdfutils_launcher.py.

    Tries regular import first (namespace package), then falls back to
    loading by file path to be robust regardless of package layout.
    """
    # 1) Try namespace package import (PEP 420)
    try:
        return importlib.import_module("scripts.launcher.pdfutils_launcher")
    except Exception:
        pass

    # 2) Fallback: import by file path
    repo_root = os.path.dirname(os.path.abspath(__file__))
    impl_path = os.path.join(repo_root, "scripts", "launcher", "pdfutils_launcher.py")
    spec = importlib.util.spec_from_file_location("scripts.launcher.pdfutils_launcher", impl_path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        return mod
    raise ImportError("Could not load scripts.launcher.pdfutils_launcher")


try:
    _impl = _load_impl()
    # Re-export commonly used entry points for tests and CLI
    ensure_venv = _impl.ensure_venv
    check_tesseract_path = _impl.check_tesseract_path
    install_python_dependencies = getattr(_impl, "install_python_dependencies", None)
    install_all_dependencies = _impl.install_all_dependencies
    check_and_install_packages = _impl.check_and_install_packages
    run_launcher = _impl.run_launcher
    main = _impl.main
except ImportError:
    # ------------------------------
    # Self-contained fallback
    # ------------------------------
    def _read_cfg(repo_root: Path) -> dict:
        cfg = {}
        cfg_path = repo_root / "pdfutils_launcher.cfg"
        if cfg_path.exists():
            parser = configparser.ConfigParser()
            try:
                parser.read(str(cfg_path))
                if parser.has_section("launcher"):
                    venv_path = parser.get("launcher", "venv_path", fallback=None)
                    if venv_path:
                        cfg["venv_path"] = venv_path
            except Exception:
                pass
        return cfg

    def _is_venv() -> bool:
        return getattr(sys, "base_prefix", sys.prefix) != sys.prefix or hasattr(sys, "real_prefix")

    def _venv_paths(venv_dir: Path) -> tuple[Path, Path]:
        if os.name == "nt":
            py = venv_dir / "Scripts" / "python.exe"
            pip = venv_dir / "Scripts" / "pip.exe"
        else:
            py = venv_dir / "bin" / "python"
            pip = venv_dir / "bin" / "pip"
        return py, pip

    def ensure_venv(venv_dir: str | os.PathLike = ".pdfutils_venv") -> Path:
        venv_path = Path(venv_dir)
        if venv_path.exists():
            return venv_path
        print(f"[INFO] Creating virtual environment at {venv_path}...")
        code = subprocess.call([sys.executable, "-m", "venv", str(venv_path)])
        if code != 0:
            print("[WARN] Failed to create venv. Continuing without it.")
        return venv_path

    def _pip_install(pip_path: Path, *args: str) -> int:
        return subprocess.call([str(pip_path), "install", *args])

    def install_requirements(pip_path: Path, requirements_file: Path) -> None:
        if not requirements_file.exists():
            return
        print(f"[INFO] Installing dependencies from {requirements_file.name} ...")
        code = _pip_install(pip_path, "-r", str(requirements_file))
        if code != 0:
            print("[WARN] Some dependencies failed to install. Continuing.")

    def _should_install_kraken() -> bool:
        py = sys.version_info
        system = platform.system().lower()
        if (py.major, py.minor) >= (3, 13):
            return False
        if system == "windows":
            return False
        return True

    def _install_full_feature_set(pip_path: Path) -> None:
        pkgs = [
            "numpy",
            "opencv-python",
            "pdfplumber",
            "camelot-py[cv]",
            "pyzbar",
            "segno",
            "pandas",
            "openpyxl",
        ]
        if _should_install_kraken():
            pkgs.append("kraken")
        else:
            print("[INFO] Skipping kraken on this platform/Python; handwriting OCR uses pytesseract.")

        fallbacks = {
            "opencv-python": ["opencv-python-headless"],
            "camelot-py[cv]": ["camelot-py[base]"],
            "kraken": ["kraken==3.0.13"],
        }

        for pkg in pkgs:
            print(f"[INFO] Installing {pkg} ...")
            code = _pip_install(pip_path, pkg)
            if code != 0:
                tried = [pkg]
                for alt in fallbacks.get(pkg, []):
                    print(f"[INFO] Retrying with fallback: {alt}")
                    code = _pip_install(pip_path, alt)
                    tried.append(alt)
                    if code == 0:
                        break
                if code != 0:
                    print(f"[WARN] Failed to install {pkg} (tried: {', '.join(tried)}).")

    def run_app(python_path: Path | None = None) -> int:
        py = str(python_path) if python_path else sys.executable
        return subprocess.call([py, "-m", "pdfutils"])  # delegates to pdfutils/__main__.py

    def main() -> int:
        if sys.stdout.encoding != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8")
        repo_root = Path(__file__).resolve().parent
        cfg = _read_cfg(repo_root)
        req = repo_root / "requirements.txt"
        if not _is_venv():
            venv_target = Path(cfg.get("venv_path", ".pdfutils_venv"))
            if not venv_target.is_absolute():
                venv_target = repo_root / venv_target
            venv = ensure_venv(venv_target)
            py, pip = _venv_paths(venv)
            if py.exists():
                install_requirements(pip, req)
                _install_full_feature_set(pip)
                return run_app(py)
        return run_app(None)

    # exports (for tests/tools calling into this launcher module)
    ensure_venv = ensure_venv
    run_launcher = main

if __name__ == "__main__":
    sys.exit(main())
