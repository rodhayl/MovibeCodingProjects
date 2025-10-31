#!/usr/bin/env python3
"""
Packaging script for Video Downloader
Creates a standalone executable using PyInstaller
"""

import os
import subprocess
import sys


# create_executable() function has been moved to build_package.py
# Use build_package.py for creating executables as it has enhanced error handling
# and better platform compatibility


def create_zip_package():
    """Create a ZIP package with all necessary files"""

    print("Creating ZIP package...")

    import zipfile

    zip_name = "VideoDownloader_Package.zip"

    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add main files
        for file in ["main.py", "run.py", "run.bat", "requirements.txt", "README.md"]:
            if os.path.exists(file):
                zipf.write(file)

        # Add executable if it exists
        exe_path = "dist/VideoDownloader.exe"
        if os.path.exists(exe_path):
            zipf.write(exe_path, "VideoDownloader.exe")

        # Add bin directory with FFmpeg if it exists
        if os.path.exists("bin"):
            for root, _dirs, files in os.walk("bin"):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path)

    print(f"ZIP package created: {zip_name}")


if __name__ == "__main__":
    print("Video Downloader Packaging Script")
    print("=" * 40)
    print("\n⚠️  NOTICE: Executable creation has been moved to build_package.py")
    print("   For better reliability and enhanced features, please use:")
    print("   python build_package.py")
    print()

    choice = input(
        "Choose packaging option:\n1. Use build_package.py (Recommended)\n2. Create ZIP package only\nEnter choice (1-2): "
    ).strip()

    if choice == "1":
        print("\n🔄 Redirecting to build_package.py...")
        import subprocess

        subprocess.run([sys.executable, "build_package.py"])
    elif choice == "2":
        create_zip_package()
    else:
        print("Invalid choice. Exiting.")
