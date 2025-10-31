#!/usr/bin/env python3
"""
Simple launcher to test the GUI application
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("🚀 Starting Photo Recognition GUI...")
    import sys
    from pathlib import Path

    # Add src directory to path
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))

    from photofilter.gui.main_window import main

    print("✅ Application loaded successfully!")

    # Start the GUI
    main()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
