#!/usr/bin/env python3
"""
Video Downloader Launcher
Run this script to start the video downloader application.
"""

import os
import sys


def main():
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)

    # Import and run the main application
    from main import main as app_main

    app_main()


if __name__ == "__main__":
    main()
