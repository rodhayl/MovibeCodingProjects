#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def _safe_run(cmd: List[str]) -> bool:
    try:
        r = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
        )
        return r.returncode == 0
    except Exception:
        return False


def detect_recommended_accelerator() -> str:
    """Detect a recommended accelerator: 'cuda', 'amd', or 'cpu'."""
    # Prefer CUDA if NVIDIA is present
    if _safe_run(["nvidia-smi", "-L"]):
        return "cuda"

    # On Linux, try to spot ROCm quickly
    if sys.platform.startswith("linux"):
        if any(
            _safe_run([cmd, "--help"]) for cmd in ["rocminfo", "rocm-smi", "hipinfo"]
        ):
            return "amd"

    # On Windows, DirectML is generally the AMD path
    if sys.platform.startswith("win"):
        try:
            __import__("torch_directml")  # presence hints at AMD capability
            return "amd"
        except Exception:
            # Even if not installed yet, AMD may be desired on Windows
            return "amd"

    return "cpu"


def prompt_for_choice(recommended: str) -> Tuple[str, bool]:
    valid = {"auto", "cuda", "amd", "cpu"}
    # Respect pre-set env var
    env_choice = os.getenv("PHOTOFILTER_TORCH_ACCELERATOR")
    if env_choice and env_choice.lower() in valid:
        logging.info(f"Using accelerator from environment: {env_choice}")
        return env_choice.lower(), False

    # Try lightweight GUI dialog first if possible
    try:
        choice, persist = _prompt_with_tkinter(recommended)
        if choice:
            return choice, persist
    except Exception:
        # Fall back to console
        pass

    # Fallbacks: console prompt if interactive, otherwise recommended
    if not sys.stdin.isatty():
        logging.info(
            f"Non-interactive shell detected. Using recommended accelerator: {recommended}"
        )
        return recommended, False

    print("")
    print("=== Accelerator Selection ===")
    print(f"Recommended: {recommended.upper()}")
    print(
        "Choose accelerator: [cuda] NVIDIA CUDA, [amd] AMD (DirectML/ROCm), [cpu] CPU, [auto] let app decide"
    )
    print("Press Enter to accept recommended.")
    choice = input("> ").strip().lower()
    if choice == "":
        return recommended, False
    if choice not in {"cuda", "amd", "cpu", "auto"}:
        print(f"Invalid choice '{choice}'. Using recommended: {recommended}")
        return recommended, False
    return choice, False


def _prompt_with_tkinter(recommended: str) -> Tuple[str, bool]:
    """Show a tiny Tkinter dialog to choose accelerator.
    Returns (choice, persist). If GUI not possible, returns ("", False) to indicate fallback.
    """
    # Avoid GUI if obviously headless on Linux
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return "", False
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        return "", False

    root = tk.Tk()
    root.title("Select Accelerator")
    root.resizable(False, False)

    # Center the window
    try:
        root.update_idletasks()
        w, h = 360, 220
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        root.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass

    wrapper = ttk.Frame(root, padding=12)
    wrapper.pack(fill="both", expand=True)

    lbl = ttk.Label(wrapper, text="Choose your accelerator:")
    lbl.pack(anchor="w", pady=(0, 6))

    var = tk.StringVar(value=recommended)
    persist_var = tk.BooleanVar(value=False)

    options = [
        ("NVIDIA CUDA", "cuda"),
        ("AMD (DirectML/ROCm)", "amd"),
        ("CPU", "cpu"),
        ("Auto (let app decide)", "auto"),
    ]
    for text, val in options:
        ttk.Radiobutton(wrapper, text=text, variable=var, value=val).pack(anchor="w")

    info = ttk.Label(
        wrapper, text=f"Recommended: {recommended.upper()}", foreground="#666"
    )
    info.pack(anchor="w", pady=(8, 8))

    chosen = {"value": "", "persist": False}

    def on_ok():
        chosen["value"] = var.get()
        chosen["persist"] = bool(persist_var.get())
        root.quit()

    def on_cancel():
        chosen["value"] = recommended
        chosen["persist"] = False
        root.quit()

    # Checkbox row
    chk = ttk.Checkbutton(
        wrapper, text="Don't ask again (remember my choice)", variable=persist_var
    )
    chk.pack(anchor="w", pady=(0, 8))

    # Buttons row
    btns = ttk.Frame(wrapper)
    btns.pack(anchor="e", fill="x")

    def open_docs():
        readme = Path(__file__).resolve().parents[1] / "README.md"
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(readme))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(readme)])
            else:
                subprocess.Popen(["xdg-open", str(readme)])
        except Exception:
            logging.info(f"README located at: {readme}")

    ttk.Button(btns, text="Open Docs", command=open_docs).pack(side="left")
    ttk.Button(btns, text="OK", command=on_ok).pack(side="right")
    ttk.Button(btns, text="Cancel", command=on_cancel).pack(side="right", padx=(0, 6))

    root.protocol("WM_DELETE_WINDOW", on_cancel)
    try:
        root.mainloop()
    finally:
        try:
            root.destroy()
        except Exception:
            pass

    return (chosen["value"] or "", chosen["persist"])


def persist_choice(choice: str, root: Path):
    try:
        path = root / ".accelerator_choice"
        path.write_text(choice, encoding="utf-8")
        logging.info(f"Accelerator choice saved to {path}")
    except Exception as e:
        logging.warning(f"Could not persist accelerator choice: {e}")


def main():
    repo_root = Path(__file__).resolve().parents[1]
    # Ensure repo root is on sys.path so we can import top-level modules when running from scripts/
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    try:
        import photo_recognition_gui_production as app
    except Exception as e:
        logging.error(f"Failed to import installer module: {e}")
        sys.exit(1)

    rec = detect_recommended_accelerator()
    choice, persist = prompt_for_choice(rec)
    os.environ["PHOTOFILTER_TORCH_ACCELERATOR"] = choice
    if persist:
        persist_choice(choice, repo_root)

    try:
        ok = app.install_dependencies()
        if not ok:
            logging.error("GPU/accelerator dependency installation reported failure.")
            sys.exit(2)
    except SystemExit:
        raise
    except Exception as e:
        logging.error(f"Installer raised an exception: {e}")
        sys.exit(3)

    logging.info("GPU/accelerator dependencies check completed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
