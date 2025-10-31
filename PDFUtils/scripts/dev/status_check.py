import subprocess


def check_current_status():
    """Check current status of all 27 problematic test files"""
    files_with_errors = [
        "tests/test_barcode_tab.py",
        "tests/test_compress_tab_simplified.py",
        "tests/test_extract_tab.py",
        "tests/test_file_selector_parameterized.py",
        "tests/test_file_selector_parameterized_new.py",
        "tests/test_gui_helpers.py",
        "tests/test_launcher.py",
        "tests/test_merge_tab.py",
        "tests/test_notification_panel.py",
        "tests/test_ocr_tab_simplified.py",
        "tests/test_output_file_selector.py",
        "tests/test_output_file_selector_parameterized.py",
        "tests/test_pdf_ops.py",
        "tests/test_progress_tracker.py",
        "tests/test_progress_tracker_fixed.py",
        "tests/test_progress_tracker_simplified.py",
        "tests/test_property_based.py",
        "tests/test_property_based_fixed.py",
        "tests/test_property_based_simplified.py",
        "tests/test_responsive_tabs.py",
        "tests/test_split_tab.py",
        "tests/test_table_extraction_tab.py",
        "tests/test_table_extraction_tab_fixed.py",
        "tests/test_table_extraction_tab_simplified.py",
        "tests/test_ui_workflows.py",
        "tests/test_ui_workflows_part1.py",
        "tests/test_ui_workflows_simple.py",
    ]

    compiling = []
    broken = []

    for file_path in files_with_errors:
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", file_path],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                compiling.append(file_path)
            else:
                error = result.stderr.strip()
                # Extract simplified error
                if "line" in error:
                    line_info = error.split("line")[1].split()[0].rstrip(",")
                    error_type = error.split("SyntaxError:")[-1].strip() if "SyntaxError:" in error else "Error"
                    broken.append((file_path, f"Line {line_info}: {error_type}"))
                else:
                    broken.append((file_path, "Other error"))
        except Exception as e:
            broken.append((file_path, f"Exception: {str(e)}"))

    print(f"✅ COMPILING: {len(compiling)}/27 files")
    for f in compiling:
        print(f"  ✅ {f}")

    print(f"\n❌ BROKEN: {len(broken)}/27 files")

    # Sort broken files by error type for prioritization
    simple_errors = []
    bracket_errors = []
    complex_errors = []

    for file_path, error in broken:
        if "invalid syntax" in error and "comma" not in error:
            simple_errors.append((file_path, error))
        elif "does not match" in error or "was never closed" in error:
            bracket_errors.append((file_path, error))
        else:
            complex_errors.append((file_path, error))

    print("\n🎯 PRIORITY TARGETS (Simple syntax errors):")
    for file_path, error in simple_errors[:5]:  # Top 5
        print(f"  🎯 {file_path} - {error}")

    print("\n🔧 MEDIUM TARGETS (Bracket mismatches):")
    for file_path, error in bracket_errors[:5]:  # Top 5
        print(f"  🔧 {file_path} - {error}")

    return compiling, simple_errors, bracket_errors, complex_errors


if __name__ == "__main__":
    check_current_status()
