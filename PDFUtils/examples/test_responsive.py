#!/usr/bin/env python3
"""Test script for the responsive PDFUtils application."""

import logging
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from pdfutils import responsive_main

        print("✓ responsive_main imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import responsive_main: {e}")
        return False

    try:
        from pdfutils import responsive_app

        print("✓ responsive_app imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import responsive_app: {e}")
        return False

    try:
        from pdfutils.tabs import (
            AboutTab,
            BarcodeTab,
            CompressTab,
            ExtractTab,
            HandwritingOcrTab,
            MergeTab,
            OcrTab,
            SplitTab,
            TableExtractionTab,
        )

        print("✓ All tabs imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import tabs: {e}")
        return False

    return True


def test_ui_components():
    """Test UI components creation."""
    print("\nTesting UI components...")

    try:
        import tkinter as tk

        from pdfutils.gui.components import ResponsiveFrame, TabContentFrame

        root = tk.Tk()
        root.withdraw()  # Hide the window

        # Test ResponsiveFrame
        frame = ResponsiveFrame(root)
        print("✓ ResponsiveFrame created successfully")

        # Test TabContentFrame
        tab_frame = TabContentFrame(root)
        print("✓ TabContentFrame created successfully")

        root.destroy()
        return True

    except Exception as e:
        print(f"✗ Failed to create UI components: {e}")
        return False


def test_responsive_app():
    """Test responsive app creation."""
    print("\nTesting responsive app...")

    try:
        import tkinter as tk

        from pdfutils.responsive_app import ResponsiveApp

        root = tk.Tk()
        root.withdraw()  # Hide the window

        app = ResponsiveApp(root)
        print("✓ ResponsiveApp created successfully")

        root.destroy()
        return True

    except Exception as e:
        print(f"✗ Failed to create responsive app: {e}")
        return False


def main():
    """Run all tests."""
    print("PDFUtils Responsive Application Test")
    print("=" * 40)

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run tests
    tests = [test_imports, test_ui_components, test_responsive_app]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed! The responsive application is ready to use.")
        print("\nTo run the application:")
        print("  python -m pdfutils")
        print("  or")
        print("  python test_responsive.py --run")
        return True
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        # Actually run the application
        print("Starting PDFUtils responsive application...")
        from pdfutils.responsive_main import run_responsive

        run_responsive()
    else:
        # Run tests
        success = main()
        sys.exit(0 if success else 1)
