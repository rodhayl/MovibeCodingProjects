"""Simple test for ResponsiveFrame component without using conftest.py."""

import tkinter as tk

from pdfutils.gui.components import ResponsiveFrame


def test_responsive_frame():
    """Test the basic properties of a ResponsiveFrame."""
    # Create a root window
    root = tk.Tk()
    root.withdraw()  # Hide the window

    # Create a responsive frame
    frame = ResponsiveFrame(root, width=400, height=300)

    # Check properties
    print(f"Width: {frame.winfo_width()}")
    print(f"Height: {frame.winfo_height()}")
    print(f"Min width: {frame.min_width}")
    print(f"Min height: {frame.min_height}")
    print(f"Current width: {frame.current_width}")
    print(f"Current height: {frame.current_height}")

    # Validate
    assert frame.min_width == 300
    assert frame.min_height == 200

    # Clean up
    frame.destroy()
    root.destroy()

    print("ResponsiveFrame test passed!")


if __name__ == "__main__":
    test_responsive_frame()
