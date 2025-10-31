"""Utility helpers for PDFUtils.

Currently provides:
- Ghostscript discovery across platforms.
- Simple logging configuration helper.
- DPI awareness and theme/scaling helpers (non-breaking additions).
"""

from __future__ import annotations

import ctypes
import logging
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path
from tkinter import Tk, messagebox
from typing import Optional

# ---------------------------------------------------------------------------
# Logging + error handling helpers
# ---------------------------------------------------------------------------


def configure_logging(level: int = logging.INFO, *, logfile: str | os.PathLike | None = "pdfutils.log") -> None:
    """Configure root logger.

    * If *logfile* is provided, a rotating file handler (1 MB × 3 backups)
      is attached.  Format is ISO-8601 timestamp + level + logger name.
    * Respects the ``LOG_LEVEL`` env override.
    * If ``SENTRY_DSN`` env var is set and *sentry_sdk* is importable, crash
      reports are sent to Sentry (production deployments).
    """

    level_name = os.environ.get("LOG_LEVEL")
    if level_name:
        level = getattr(logging, level_name.upper(), level)

    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    fmt = "%Y-%m-%d %H:%M:%S"
    handler_stream = logging.StreamHandler()
    handler_stream.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", fmt))
    root.setLevel(level)
    root.addHandler(handler_stream)

    if logfile:
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(logfile, maxBytes=1_000_000, backupCount=3)
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", fmt))
        root.addHandler(file_handler)

    # Optional Sentry integration
    dsn = os.environ.get("SENTRY_DSN")
    if dsn:
        try:
            import sentry_sdk  # type: ignore

            sentry_sdk.init(dsn=dsn, traces_sample_rate=0.0)
        except ModuleNotFoundError:  # pragma: no cover
            root.warning("SENTRY_DSN set but sentry-sdk not installed")


# ---------------------------------------------------------------------------
# DPI awareness / scaling / theme helpers (safe no-ops when unsupported)
# ---------------------------------------------------------------------------


def set_dpi_awareness_windows() -> None:
    """Enable per‑monitor DPI awareness on Windows (best effort).

    No‑ops on non‑Windows platforms or if the call is unavailable.
    """
    if not sys.platform.startswith("win"):
        return
    try:
        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
        user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
        return
    except Exception:
        pass
    try:
        shcore = ctypes.windll.shcore  # type: ignore[attr-defined]
        shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        return
    except Exception:
        pass
    try:
        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        user32.SetProcessDPIAware()
    except Exception:
        pass


def configure_scaling(root) -> None:
    """Configure Tk scaling based on actual DPI for crisp rendering."""
    try:
        px_per_inch = root.winfo_fpixels("1i")
        scaling = max(0.5, float(px_per_inch) / 72.0)
        root.tk.call("tk", "scaling", scaling)
    except Exception:
        pass


def configure_theme(root) -> None:
    """Apply a consistent ttk theme when ttkbootstrap is unavailable."""
    try:
        from tkinter import ttk

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", padding=(8, 6))
        style.configure("TEntry", padding=(4, 4))
        style.configure("TCombobox", padding=(4, 4))
        style.configure("TNotebook.Tab", padding=(12, 6))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Tesseract discovery
# ---------------------------------------------------------------------------


def find_tesseract_command() -> Optional[str]:
    """Return a path to a Tesseract command if available, else ``None``.

    Searches for typical executable names using :pymod:`shutil.which` and also
    checks the ``TESSERACT_PATH`` environment variable if set.

    On Windows, also checks common installation paths if standard discovery fails.
    """
    # Environment variable override.
    env_override = os.environ.get("TESSERACT_PATH")
    if env_override:
        tesseract_path = shutil.which(env_override)
        if tesseract_path:
            return tesseract_path
        # Also try with .exe extension on Windows
        if sys.platform.startswith("win") and not env_override.endswith(".exe"):
            tesseract_path = shutil.which(env_override + ".exe")
            if tesseract_path:
                return tesseract_path

    # Typical executable names.
    tesseract_names = ["tesseract"]
    if sys.platform.startswith("win"):
        tesseract_names.append("tesseract.exe")

    for name in tesseract_names:
        tesseract_path = shutil.which(name)
        if tesseract_path:
            return tesseract_path

    # On Windows, check common installation paths if standard discovery fails
    if sys.platform.startswith("win"):
        # Common Tesseract installation paths on Windows
        common_paths = [
            os.path.join(os.environ.get("ProgramFiles", ""), "Tesseract-OCR"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Tesseract-OCR"),
            os.path.join(os.environ.get("ProgramW6432", ""), "Tesseract-OCR"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Tesseract-OCR"),
            os.path.join(os.environ.get("APPDATA", ""), "Tesseract-OCR"),
        ]

        # Look for Tesseract in common directories
        for base_path in common_paths:
            if os.path.exists(base_path):
                # Check for tesseract executable
                for exe_name in ["tesseract.exe", "tesseract"]:
                    exe_path = os.path.join(base_path, exe_name)
                    if os.path.exists(exe_path):
                        return exe_path

                    # Also check bin subdirectory
                    bin_path = os.path.join(base_path, "bin", exe_name)
                    if os.path.exists(bin_path):
                        return bin_path

    return None


def check_tesseract_version(tesseract_cmd: Optional[str] = None) -> Optional[str]:
    """Check if Tesseract is installed and return its version.

    Returns the version string if Tesseract is available, None otherwise.
    """

    try:
        # Use provided command or find it
        cmd = tesseract_cmd or find_tesseract_command()
        if not cmd:
            return None

        # Get version
        result = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            # Version info is in stderr for Tesseract
            version_output = result.stderr or result.stdout
            # Extract version from output (first line usually contains version)
            lines = version_output.strip().split("\n")
            if lines:
                # Extract version number (e.g., "tesseract 4.1.1" -> "4.1.1")
                parts = lines[0].split()
                for part in parts:
                    if "." in part and part[0].isdigit():
                        return part
            return version_output.strip()
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return None


# ---------------------------------------------------------------------------
# Ghostscript discovery
# ---------------------------------------------------------------------------

_GS_EXECUTABLE_CANDIDATES = (
    "gs",  # Unix-like systems
    "gswin64c",  # Windows 64-bit
    "gswin32c",  # Windows 32-bit
    "gswin64",  # Windows 64-bit alternative
    "gswin32",  # Windows 32-bit alternative
)


def find_ghostscript_command() -> Optional[str]:
    """Return a path to a Ghostscript command if available, else ``None``.

    Searches for typical executable names using :pymod:`shutil.which` and also
    checks the ``GS_PROG`` environment variable if set.

    On Windows, also checks common installation paths if standard discovery fails.
    """
    # Environment variable override.
    env_override = os.environ.get("GS_PROG")
    if env_override:
        if shutil.which(env_override):
            return env_override

    # Typical executable names.
    for cmd in _GS_EXECUTABLE_CANDIDATES:
        if shutil.which(cmd):
            return cmd

    # On Windows, check common installation paths if standard discovery fails
    if sys.platform.startswith("win"):
        # Common Ghostscript installation paths on Windows
        common_paths = [
            os.path.join(os.environ.get("ProgramFiles", ""), "gs"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "gs"),
            os.path.join(os.environ.get("ProgramW6432", ""), "gs"),
        ]

        # Look for Ghostscript in program files directories
        for base_path in common_paths:
            if os.path.exists(base_path):
                # Look for version subdirectories
                try:
                    for item in os.listdir(base_path):
                        if item.startswith("gs"):
                            # Check for bin directory with executables
                            bin_path = os.path.join(base_path, item, "bin")
                            if os.path.exists(bin_path):
                                for exe_name in [
                                    "gswin64c.exe",
                                    "gswin32c.exe",
                                    "gs.exe",
                                ]:
                                    exe_path = os.path.join(bin_path, exe_name)
                                    if os.path.exists(exe_path):
                                        return exe_path
                except (OSError, PermissionError):
                    # Skip directories we can't read
                    continue

    return None


# ---------------------------------------------------------------------------
# Error handling helpers
# ---------------------------------------------------------------------------


def _log_unhandled_exception(exc_type, exc_value, exc_tb):  # type: ignore[yy]
    """sys.excepthook that logs and shows a fatal error dialog (CLI fall-back)."""
    logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))
    # Pretty print last traceback frame path:line
    tb_last = traceback.extract_tb(exc_tb)[-1] if exc_tb else None
    location = f"{tb_last.filename}:{tb_last.lineno}" if tb_last else "<unknown>"
    message = f"{exc_type.__name__}: {exc_value}\n({location})"
    try:
        # Use a bare Tk root to show dialog if none exists
        root = Tk()
        root.withdraw()
        messagebox.showerror("Fatal error", message)
        root.destroy()
    except Exception:  # pragma: no cover – headless env
        pass


sys.excepthook = _log_unhandled_exception


def install_tk_error_handler(root: Tk) -> None:
    """Install *root.report_callback_exception* to show an error dialog and log."""

    def _handler(exc_type, exc_value, exc_tb):  # type: ignore[yy]
        logging.error("Tkinter callback exception", exc_info=(exc_type, exc_value, exc_tb))
        messagebox.showerror("Error", f"{exc_type.__name__}: {exc_value}")

    root.report_callback_exception = _handler  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Accessibility / Color helpers
# ---------------------------------------------------------------------------


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a #rrggbb hex string to an (R, G, B) tuple (0-255 each)."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return r, g, b  # type: ignore[return-value]


def _relative_luminance(r: int, g: int, b: int) -> float:
    """Return WCAG relative luminance for RGB tuple (0–1)."""

    def _chan(c: int) -> float:
        c_float = c / 255.0
        return c_float / 12.92 if c_float <= 0.03928 else ((c_float + 0.055) / 1.055) ** 2.4

    r_l, g_l, b_l = map(_chan, (r, g, b))
    return 0.2126 * r_l + 0.7152 * g_l + 0.0722 * b_l


def contrast_ratio(c1: str, c2: str) -> float:
    """Compute WCAG contrast ratio (>=1.0). Both colors hex (#rrggbb)."""
    lum1 = _relative_luminance(*_hex_to_rgb(c1))
    lum2 = _relative_luminance(*_hex_to_rgb(c2))
    lighter, darker = max(lum1, lum2), min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def is_contrast_ok(c1: str, c2: str, *, ratio: float = 4.5) -> bool:
    """Return True if *c1* and *c2* meet the minimum WCAG ratio (default 4.5)."""
    return contrast_ratio(c1, c2) >= ratio


def audit_palette_contrast(palette: dict[str, tuple[str, str]], *, ratio: float = 4.5) -> dict[str, float]:
    """Return mapping of *name* ➔ actual ratio for entries below threshold.

    *palette* is ``{name: (fg_hex, bg_hex)}``.
    The result includes only the failing names; empty dict means all good.
    """
    failures: dict[str, float] = {}
    for name, (fg, bg) in palette.items():
        cr = contrast_ratio(fg, bg)
        if cr < ratio:
            failures[name] = cr
    return failures


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------


def ensure_dir(path: os.PathLike | str) -> Path:
    """Create directory *path* if it doesn't exist and return :class:`Path`."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
