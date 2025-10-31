#!/usr/bin/env python3
"""
Simple file scanner to see what files exist and their properties
"""

from pathlib import Path


def scan_test_directory():
    print("🔍 Scanning for files...")

    # Check both possible locations
    test_paths = [
        Path("C:/Users/david/Pictures/ToProcess"),
        Path("c:/Users/david/GitHUB/AIPhotoRecognitionToolWorking/ToProcess"),
        Path("ToProcess"),  # relative
        Path("."),  # current directory
    ]

    for test_path in test_paths:
        print(f"\n📁 Checking: {test_path}")
        if test_path.exists():
            print(f"  ✅ Directory exists")
            try:
                files = list(test_path.iterdir())
                print(f"  📊 Found {len(files)} items")

                if files:
                    print("  📋 First 10 items:")
                    for i, file_path in enumerate(files[:10]):
                        if file_path.is_file():
                            size = file_path.stat().st_size
                            print(f"    {i+1}. {file_path.name} ({size:,} bytes)")
                        else:
                            print(f"    {i+1}. {file_path.name} (directory)")

                    # Look for image files specifically
                    image_extensions = {
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".gif",
                        ".bmp",
                        ".tiff",
                        ".webp",
                    }
                    image_files = [
                        f
                        for f in files
                        if f.is_file() and f.suffix.lower() in image_extensions
                    ]
                    print(f"  🖼️  Image files: {len(image_files)}")

                    if image_files:
                        print("  🎯 First 5 image files:")
                        for i, img in enumerate(image_files[:5]):
                            size = img.stat().st_size
                            print(f"    {i+1}. {img.name} ({size:,} bytes)")

                        # Look for potential duplicates by name
                        print(
                            "  🔍 Looking for potential duplicates by name pattern..."
                        )
                        names = [f.stem.lower() for f in image_files]
                        for i, name1 in enumerate(names):
                            for j, name2 in enumerate(names[i + 1 :], i + 1):
                                # Check for numbered variations
                                if name1 in name2 or name2 in name1:
                                    if name1 != name2:  # not identical
                                        print(
                                            f"    🎯 Potential: {image_files[i].name} <-> {image_files[j].name}"
                                        )

                        # Look for exact size matches
                        print("  📏 Looking for files with same size...")
                        size_groups = {}
                        for img in image_files:
                            size = img.stat().st_size
                            if size not in size_groups:
                                size_groups[size] = []
                            size_groups[size].append(img)

                        for size, files_with_size in size_groups.items():
                            if len(files_with_size) > 1:
                                print(
                                    f"    📊 {len(files_with_size)} files with size {size:,} bytes:"
                                )
                                for f in files_with_size:
                                    print(f"      - {f.name}")
                else:
                    print("  ❌ Directory is empty")

            except Exception as e:
                print(f"  ❌ Error reading directory: {e}")
        else:
            print(f"  ❌ Directory does not exist")


def scan_current_workspace():
    print("\n🏠 Scanning current workspace...")
    current = Path(".")

    try:
        files = list(current.glob("*.py"))
        print(f"Python files: {len(files)}")
        for f in files:
            print(f"  - {f.name}")

        # Check for any image files in current directory
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
        images = [
            f
            for f in current.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        print(f"Image files in workspace: {len(images)}")
        for img in images:
            size = img.stat().st_size
            print(f"  - {img.name} ({size:,} bytes)")

    except Exception as e:
        print(f"Error scanning workspace: {e}")


if __name__ == "__main__":
    scan_test_directory()
    scan_current_workspace()
    print("\n🏁 Scan complete!")
