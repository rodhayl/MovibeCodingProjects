"""Package entry-point.

Supports both "python -m pdfutils" and execution as a frozen app (PyInstaller).
Always prefers the responsive GUI.
"""

from __future__ import annotations


def _resolve_runner():
    """Return the GUI runner function, preferring absolute import (frozen-safe)."""
    try:
        from pdfutils.responsive_main import run_responsive as _run  # type: ignore

        return _run
    except Exception:
        pass
    try:
        from .responsive_main import run_responsive as _run  # type: ignore

        return _run
    except Exception as exc:  # noqa: F841

        def _run():  # pragma: no cover
            print("Cannot start application: Import error.")
            print(str(exc))  # noqa: F821

        return _run


_run = _resolve_runner()

if __name__ == "__main__":  # pragma: no cover
    _run()
