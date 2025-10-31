#!/usr/bin/env python3
"""
End-to-end dry run for PhotoOrganizer folder creation.
- Creates temp input/output folders
- Generates a few tiny images
- Instantiates PhotoOrganizer with target ["dog"]
- Calls create_destination_folders() only (no model downloads)
- Prints created subfolders so we can verify behavior
"""
import sys
import os
import tempfile
from pathlib import Path

# Ensure src is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from PIL import Image
except Exception as e:
    print(f"ERROR: Pillow is required for this dry run: {e}")
    sys.exit(1)

from photofilter.core.recognition import PhotoOrganizer

def make_sample_images(input_dir: Path):
    input_dir.mkdir(parents=True, exist_ok=True)
    # Create simple color images
    samples = [
        ("red.jpg", (255, 0, 0)),
        ("green.png", (0, 255, 0)),
        ("blue.bmp", (0, 0, 255)),
    ]
    for name, rgb in samples:
        p = input_dir / name
        Image.new("RGB", (64, 64), color=rgb).save(p)


def main():
    temp_root = Path(tempfile.mkdtemp(prefix="aiphoto_e2e_"))
    input_dir = temp_root / "input"
    output_dir = temp_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    make_sample_images(input_dir)

    print(f"Temp root: {temp_root}")
    print(f"Input:     {input_dir}")
    print(f"Output:    {output_dir}")

    org = PhotoOrganizer(input_folder=str(input_dir), output_folder=str(output_dir), target_objects=["dog"]) 
    print(f"white_dog_mode: {getattr(org, 'white_dog_mode', None)}")

    ok = org.create_destination_folders()
    print(f"create_destination_folders() -> {ok}")

    if not ok:
        print("Folder creation failed.")
        sys.exit(2)

    subdirs = sorted([p.name for p in output_dir.iterdir() if p.is_dir()])
    print(f"Subfolders under output/: {subdirs}")

    # Expected with target ['dog'] (white_dog_mode True): White_Dog and Other
    expected = {"White_Dog", "Other"}
    if expected.issubset(set(subdirs)):
        print("PASS: Expected subfolders present: White_Dog, Other")
        sys.exit(0)
    else:
        print("FAIL: Expected subfolders not present.")
        sys.exit(3)


if __name__ == "__main__":
    main()
