# PDFUtils Clean Test Setup

## Overview

All legacy, buggy test running scripts have been removed and replaced with a single, clean, reliable test runner: `run_test.py`.

## Usage

### Basic Commands

```bash
# Run all tests
python run_test.py

# Run tests with verbose output
python run_test.py --verbose

# Run tests quietly (minimal output)
python run_test.py --quiet

# Run specific test file
python run_test.py --pattern test_ui_components.py

# Run tests with coverage report
python run_test.py --coverage
```

### Advanced Usage

```bash
# Run tests matching a pattern
python run_test.py --pattern test_progress_tracker.py --verbose

# Generate coverage report with HTML output
python run_test.py --coverage
# Coverage report will be in htmlcov/index.html
```

## Features

- **Memory Safe**: Uses the fixed tkinter mocks to prevent infinite loops and memory exhaustion
- **Simple Interface**: Single script with clear command-line options
- **Fast Execution**: No unnecessary overhead or complex orchestration
- **Coverage Support**: Optional coverage reporting with HTML output
- **Pattern Matching**: Run specific test files or patterns
- **Clear Output**: Clean, readable test results with timing information

## Removed Legacy Scripts

The following buggy test runners have been removed to prevent confusion and errors:

- `run_fixed_tests.py`
- `run_comprehensive_tests.py`
- `run_isolated_tests.py`
- `run_auto_hide_test.py`
- `run_isolated_tests_advanced.py`
- `run_simple_tests.py`
- `run_memory_safe_tests.py`
- `run_simplified_tests.py`
- `run_tests.py`
- `run_single_test.py`
- `run_visual_test_report.py`
- `run_test_suite_manager.py`
- `run_test_reporter.py`
- `run_tests_with_timeout.py`
- `run_tests_and_report.py`
- `test_memory_fix.py`

## Memory Leak Fix

The memory leak issue has been resolved through modifications to `tests/conftest.py`:

- **Disabled callback scheduling**: The mock `after()` method no longer schedules actual callbacks
- **Simplified update methods**: Both `update()` and `update_idletasks()` are now no-ops
- **Prevented infinite loops**: Animation callbacks no longer cause memory exhaustion

## Best Practices

1. **Always use `run_test.py`** - This is the only test runner you need
2. **Start with `--quiet`** for quick checks
3. **Use `--verbose`** for debugging specific issues
4. **Use `--pattern`** to focus on specific test files during development
5. **Run `--coverage`** periodically to check test coverage

## Examples

```bash
# Quick test run during development
python run_test.py --quiet

# Debug a failing test
python run_test.py --pattern test_ui_components.py --verbose

# Full test suite with coverage for CI/CD
python run_test.py --coverage

# Test a specific component
python run_test.py --pattern test_progress_tracker.py
```

## Troubleshooting

If tests fail:

1. Use `--verbose` to see detailed output
2. Use `--pattern` to isolate the failing test file
3. Check that the virtual environment is activated
4. Ensure all dependencies are installed with `pip install -r requirements-dev.txt`

The clean test setup eliminates the memory issues and provides a reliable, fast testing experience.
