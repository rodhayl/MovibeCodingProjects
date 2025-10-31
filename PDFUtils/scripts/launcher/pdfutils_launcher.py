import argparse
import configparser
import os
import subprocess
import sys

REQUIRED_PACKAGES = ["pypdf", "pytest"]
OPTIONAL_PACKAGES = [
    "pymupdf",
    "pytesseract",
    "Pillow",
    "opencv-python",
    "scikit-image",
    "pyzbar",
    "camelot-py[cv]",
    "pdfplumber",
    "pikepdf",
    "langdetect",
    "reportlab",
]
DEFAULT_VENV = ".pdfutils_venv"
CONFIG_FILE = "pdfutils_launcher.cfg"


def get_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config


def save_config(venv_path):
    config = configparser.ConfigParser()
    config["launcher"] = {"venv_path": venv_path}
    with open(CONFIG_FILE, "w") as f:
        config.write(f)


def ensure_venv(input_func=input, print_func=print):
    config = get_config()
    venv_path = config.get("launcher", "venv_path", fallback=None)
    venv_python_name = "python.exe" if os.name == "nt" else "python"
    venv_python = None

    # 1. Check config file
    if venv_path:
        venv_python = os.path.join(venv_path, "Scripts" if os.name == "nt" else "bin", venv_python_name)
        if os.path.exists(venv_python):
            return 0, venv_python
        # If config is stale, fall back to default

    # 2. Check default location
    venv_path = DEFAULT_VENV
    venv_python = os.path.join(venv_path, "Scripts" if os.name == "nt" else "bin", venv_python_name)
    if os.path.exists(venv_python):
        save_config(venv_path)  # Always save config if found
        return 0, venv_python

    # 3. Prompt to create new venv
    print_func(f"Python virtual environment not found at {venv_path}.")
    resp = input_func(f"Create a new virtual environment at '{venv_path}'? [Y/n]: ").strip().lower()
    if resp and resp != "y":
        print_func("Aborting. Please create a virtual environment manually.")
        return 1, None
    subprocess.check_call([sys.executable, "-m", "venv", venv_path])
    print_func(f"Created virtual environment at {venv_path}.")
    save_config(venv_path)
    venv_python = os.path.join(venv_path, "Scripts" if os.name == "nt" else "bin", venv_python_name)
    return 0, venv_python


def check_tesseract_path(print_func=print):
    """Check if Tesseract is properly installed and accessible.

    Returns:
        tuple: (is_installed: bool, message: str)
    """
    try:
        import pytesseract

        try:
            version = pytesseract.get_tesseract_version()
            tesseract_cmd = getattr(pytesseract, "pytesseract", None) or getattr(pytesseract, "tesseract_cmd", None)
            if tesseract_cmd:
                tesseract_path = os.path.dirname(tesseract_cmd)
                # Add to PATH if not already there
                current_path = os.environ.get("PATH", "")
                if tesseract_path and tesseract_path not in current_path.split(os.pathsep):
                    os.environ["PATH"] = current_path + os.pathsep + tesseract_path
                    print_func(f"✓ Added Tesseract to PATH: {tesseract_path}")

            # Check for tessdata directory
            tessdata_dir = os.environ.get("TESSDATA_PREFIX")
            if not tessdata_dir:
                # Try common locations
                possible_paths = [
                    os.path.join(os.environ.get("ProgramFiles", ""), "Tesseract-OCR", "tessdata"),
                    os.path.join(
                        os.environ.get("ProgramFiles(x86)", ""),
                        "Tesseract-OCR",
                        "tessdata",
                    ),
                    os.path.join(os.path.expanduser("~"), ".pdfutils", "tessdata"),
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        os.environ["TESSDATA_PREFIX"] = os.path.dirname(path)
                        print_func(f"✓ Using Tesseract data from: {path}")
                        break

            return True, f"Tesseract {version} is installed and working"

        except (pytesseract.TesseractNotFoundError, Exception) as e:
            if "is not installed or it's not in your PATH" in str(e):
                return False, "Tesseract is not installed or not in PATH"
            return False, f"Tesseract error: {str(e)}"

    except ImportError:
        return False, "pytesseract package is not installed"


def install_tesseract_windows(print_func=print):
    """Install Tesseract OCR on Windows."""
    import tempfile
    import urllib.request

    print_func("\nInstalling Tesseract OCR for Windows...")

    # Download Tesseract installer
    tesseract_version = "5.3.3"  # Latest stable version
    download_url = f"https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-{tesseract_version}.exe"
    installer_path = os.path.join(tempfile.gettempdir(), "tesseract_installer.exe")

    try:
        print_func(f"Downloading Tesseract installer from {download_url}...")
        urllib.request.urlretrieve(download_url, installer_path)

        # Run the installer silently
        print_func("Installing Tesseract (this may take a few minutes)...")
        install_dir = os.path.join(os.environ["ProgramFiles"], "Tesseract-OCR")
        subprocess.run([installer_path, "/S", f"/D={install_dir}"], check=True)

        # Add to system PATH
        os.environ["PATH"] = f"{install_dir};{os.environ.get('PATH', '')}"
        os.environ["TESSDATA_PREFIX"] = os.path.join(install_dir, "tessdata")

        # Verify installation
        result = subprocess.run(
            [os.path.join(install_dir, "tesseract.exe"), "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            version = result.stdout.split("\n")[0]
            print_func(f"✓ Successfully installed {version}")
            return True
        return False

    except Exception as e:
        print_func(f"Error installing Tesseract: {e}")
        return False
    finally:
        # Clean up installer
        if os.path.exists(installer_path):
            try:
                os.remove(installer_path)
            except Exception:
                pass


def install_python_dependencies(python_exe, print_func=print):
    """Install all required and optional Python dependencies."""
    try:
        print_func("\nInstalling required Python packages...")
        subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([python_exe, "-m", "pip", "install", *REQUIRED_PACKAGES])
        print_func("✓ Installed required packages")

        print_func("\nInstalling optional Python packages...")
        subprocess.check_call([python_exe, "-m", "pip", "install", *OPTIONAL_PACKAGES])
        print_func("✓ Installed optional packages")
        return True
    except subprocess.CalledProcessError as e:
        print_func(f"⚠ Error installing Python packages: {e}")
        return False


def install_all_dependencies(python_exe, print_func=print):
    """Install all required dependencies and set up Tesseract."""
    # Install Python dependencies first
    if not install_python_dependencies(python_exe, print_func):
        print_func("⚠ Failed to install some Python packages. Some features may not work.")

    # Check Tesseract
    print_func("\nChecking Tesseract OCR installation...")
    tesseract_installed, message = check_tesseract_path(print_func)

    if not tesseract_installed:
        print_func(f"⚠ {message}")
        if os.name == "nt":  # Windows
            print_func("\nTesseract OCR is required for PDF text extraction and OCR features.")
            resp = input("Would you like to install Tesseract OCR now? [Y/n]: ").strip().lower()
            if not resp or resp == "y":
                if install_tesseract_windows(print_func):
                    print_func("✓ Tesseract OCR installed successfully!")
                    tesseract_installed = True
                else:
                    print_func("⚠ Failed to install Tesseract OCR automatically.")
            else:
                print_func("Skipping Tesseract installation.")
        else:
            print_func("\nTesseract OCR is required for PDF text extraction and OCR features.")
            print_func("Please install it using your system's package manager:")
            print_func("  Ubuntu/Debian: sudo apt-get install tesseract-ocr")
            print_func("  Fedora:       sudo dnf install tesseract")
            print_func("  macOS:        brew install tesseract")
            print()

    if tesseract_installed:
        print_func("\n✓ Tesseract OCR is ready to use!")
    else:
        print_func("\n⚠ Tesseract OCR is not installed. Some features will be limited.")
        print_func("You can install it later and restart the application.")

    return 0


def check_and_install_packages(python_exe, input_func=input, print_func=print):
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            subprocess.check_call([python_exe, "-c", f"import {pkg.split('[')[0]}"])
        except subprocess.CalledProcessError:
            missing.append(pkg)
    if missing:
        print_func(f"Required packages missing: {', '.join(missing)}")
        resp = input_func("Install missing packages now in the virtual environment? [Y/n]: ").strip().lower()
        if resp and resp != "y":
            print_func("Aborting. Please install dependencies manually.")
            return 1
        subprocess.check_call([python_exe, "-m", "pip", "install", *missing])

    # Remove prompt for optional dependencies and always install them
    print(
        "Installing all optional dependencies for full feature support ("
        "OCR, PDF/A, deskew, barcode/QR, table extraction, "
        "language auto-detection, etc.)..."
    )
    subprocess.check_call([sys.executable, "-m", "pip", "install", *OPTIONAL_PACKAGES])

    # Check for Tesseract executable (required for OCR)
    try:
        # First try to fix PATH if needed
        if not check_tesseract_path():
            subprocess.check_call(
                [
                    python_exe,
                    "-c",
                    "import pytesseract; pytesseract.get_tesseract_version()",
                ]
            )
        print_func("[OK] Tesseract OCR engine found and working.")
    except (subprocess.CalledProcessError, ImportError):
        print_func("⚠ Tesseract OCR engine not found. OCR features will not work.")
        if os.name == "nt":  # Windows
            print_func("\nTo install Tesseract on Windows:")
            print_func("1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
            print_func("2. Install to default location (C:\\Program Files\\Tesseract-OCR)")
            print_func("3. Add to PATH or restart this launcher")
        else:  # Linux/Mac
            print_func("\nTo install Tesseract:")
            print_func("  Ubuntu/Debian: sudo apt-get install tesseract-ocr")
            print_func("  macOS: brew install tesseract")
            print_func("  CentOS/RHEL: sudo yum install tesseract")

    return 0


def run_launcher(input_func=input, print_func=print):
    code, venv_python = ensure_venv(input_func, print_func)
    if code != 0 or venv_python is None:
        return code if code != 0 else 1
    code = check_and_install_packages(venv_python, input_func, print_func)
    if code != 0:
        return code
    subprocess.run([venv_python, "-m", "pdfutils"])
    return 0


def main():
    # Handle both --install-dependencies and --install-deps for convenience
    if "--install-deps" in sys.argv:
        sys.argv[sys.argv.index("--install-deps")] = "--install-dependencies"

    parser = argparse.ArgumentParser(description="PDFUtils Launcher")
    parser.add_argument(
        "--install-dependencies",
        "--install-deps",
        "-i",
        action="store_true",
        help="Install all required and optional dependencies, then exit.",
    )
    args = parser.parse_args()
    if args.install_dependencies:
        code, venv_python = ensure_venv()
        if code != 0 or venv_python is None:
            sys.exit(code if code != 0 else 1)
        install_all_dependencies(venv_python)
        print("All dependencies installed.")
        sys.exit(0)
    code = run_launcher()
    sys.exit(code)


if __name__ == "__main__":
    main()
