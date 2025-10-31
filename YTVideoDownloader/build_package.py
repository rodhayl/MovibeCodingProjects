#!/usr/bin/env python3
"""
Video Downloader Package Builder
A reliable Python-based packaging script that creates standalone executables.
This replaces the problematic batch file approach with pure Python.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

from utils import download_ffmpeg


def safe_print(text: str = "") -> None:
    """Print text safely on Windows consoles without Unicode emojis.

    Falls back to ASCII-only output if the console encoding can't handle
    certain characters.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            print(str(text).encode("ascii", errors="ignore").decode("ascii"))
        except Exception:
            print("[output omitted]")


def print_header():
    """Print a nice header for the packaging process."""
    safe_print("Video Downloader Package Builder")
    safe_print("=" * 50)
    safe_print("This tool creates standalone executables from your Python application.")
    safe_print()


def check_python_version():
    """Check if we have a compatible Python version."""
    safe_print("Checking Python version...")
    safe_print(
        f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} found."
    )
    return True


def check_and_install_pyinstaller():
    """Check for PyInstaller and install if missing."""
    safe_print("\nChecking for PyInstaller...")

    try:
        # Try to import PyInstaller
        import PyInstaller

        safe_print(f"PyInstaller {PyInstaller.__version__} is installed.")
        return True
    except ImportError:
        safe_print("PyInstaller not found. Installing...")
        safe_print("   This may take a moment...")

        try:
            # Try installing with pip
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--user",  # Install to user directory to avoid permission issues
                    "pyinstaller",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                safe_print("PyInstaller installed successfully!")
                safe_print("   (Restarting script to detect new installation...)")

                # Restart the script to pick up the new installation
                safe_print("\nRestarting packaging process...")
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                safe_print("Failed to install PyInstaller:")
                safe_print(f"   Exit code: {result.returncode}")
                if result.stderr:
                    safe_print(f"   Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            safe_print("Installation timed out after 5 minutes.")
            return False
        except Exception as e:
            safe_print(f"Installation failed: {e}")
            return False


def create_executable():
    """Create the standalone executable."""
    safe_print("\nCreating executable...")

    # Ensure we're in the right directory
    script_dir = Path(__file__).parent.resolve()  # Use resolve() to get absolute path
    os.chdir(script_dir)

    # Check if main.py exists
    if not Path("main.py").exists():
        safe_print("main.py not found in current directory!")
        safe_print("   Please run this script from the Video Downloader project root.")
        return False

    safe_print(f"Working directory: {script_dir}")
    safe_print("Building executable from: main.py")

    # Create output directories if they don't exist
    (script_dir / "dist").mkdir(exist_ok=True)
    (script_dir / "build").mkdir(exist_ok=True)

    # Check for FFmpeg
    ffmpeg_available = download_ffmpeg()

    # PyInstaller command arguments - simplified approach
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",  # Single executable file
        "--windowed",  # No console window for GUI apps
        "--name=VideoDownloader",
        "--distpath=./dist",
        "--workpath=./build",
        "--specpath=./build",
        "--log-level=INFO",  # Give us more visibility into issues
        # Only add essential hidden imports
        "--hidden-import=customtkinter",
        "--hidden-import=tkinter",
        "--hidden-import=yt_dlp",
        "--hidden-import=yt_dlp.extractor",
        "--hidden-import=yt_dlp.postprocessor",
        "--hidden-import=importlib.util",
    ]

    # Include FFmpeg binaries in the package if available
    if ffmpeg_available:
        ffmpeg_exe = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
        src_path = os.path.join(script_dir, "bin", ffmpeg_exe)
        if platform.system() == "Windows":
            cmd.extend(["--add-data", f"{src_path};bin"])
        else:  # macOS/Linux
            cmd.extend(["--add-data", f"{src_path}:bin"])

    # Include resources folder (HTML help files for cookie management)
    resources_path = os.path.join(script_dir, "resources")
    if os.path.exists(resources_path):
        if platform.system() == "Windows":
            cmd.extend(["--add-data", f"{resources_path};resources"])
        else:  # macOS/Linux
            cmd.extend(["--add-data", f"{resources_path}:resources"])

    # Add main.py
    cmd.append("main.py")

    try:
        safe_print("Running PyInstaller (this may take several minutes)...")
        safe_print("   Please be patient while the executable is created...")

        # Run PyInstaller with real-time output
        process = subprocess.run(cmd, cwd=script_dir)

        if process.returncode == 0:
            # Check if executable was created
            exe_name = (
                "VideoDownloader.exe"
                if platform.system() == "Windows"
                else "VideoDownloader"
            )
            exe_path = script_dir / "dist" / exe_name

            if exe_path.exists():
                size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
                safe_print("\nExecutable created successfully!")
                safe_print(f"   File: {exe_path}")
                safe_print(f"   Size: {size:.1f} MB")
                safe_print(
                    "   Note: This executable includes Python and all dependencies."
                )
                return True
            else:
                safe_print("\nExecutable file not found after build.")
                safe_print("   Check the 'dist' directory for any error files.")
                return False
        else:
            safe_print(f"\nPyInstaller failed with exit code: {process.returncode}")
            safe_print("   Check the output above for error messages.")
            return False

    except subprocess.SubprocessError as e:
        safe_print(f"\nFailed to run PyInstaller: {e}")
        return False
    except Exception as e:
        safe_print(f"\nUnexpected error during build: {e}")
        return False


def show_next_steps():
    """Show what to do with the created executable."""
    safe_print("\nNext Steps:")
    safe_print("1. Find your executable in the 'dist' folder")
    safe_print("2. Test it on a computer without Python installed")
    safe_print("3. Share the executable with others who want to use the app")
    safe_print("4. Use 'python package.py' to create additional package types")


def main():
    """Main packaging function."""
    print_header()

    # Step 1: Check Python version
    if not check_python_version():
        return False

    # Step 2: Check and install PyInstaller
    if not check_and_install_pyinstaller():
        return False

    # Step 3: Create executable
    if not create_executable():
        return False

    # Step 4: Show success message and next steps
    show_next_steps()

    safe_print("\nPackaging completed successfully!")
    safe_print("   Your Video Downloader executable is ready to use!")
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        safe_print("\n\nPackaging interrupted by user.")
        sys.exit(1)
    except Exception as e:
        safe_print(f"\nUnexpected error: {e}")
        safe_print("   If this continues, please check your Python installation.")
        sys.exit(1)
