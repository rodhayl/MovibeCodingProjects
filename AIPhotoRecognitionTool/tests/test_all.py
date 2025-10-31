#!/usr/bin/env python3
"""
Comprehensive test suite for AIPhotoRecognitionTool.

This module imports and runs all test cases from individual test files.
"""

import unittest
import sys
import os
import importlib.util
from pathlib import Path

# Add the project root to the path
PROJECT_ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, PROJECT_ROOT)


def import_test_module(module_name):
    """Dynamically import a test module."""
    module_path = str(Path(__file__).parent / f"{module_name}.py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Import test modules
# Note: Avoid including test_gui_dedup_workflow here to prevent duplicate
# execution when running unittest discovery. It will be discovered separately.
test_modules = ["test_deduplication_comprehensive"]


# Load all test cases
def load_tests(loader, standard_tests, pattern):
    """Load all test cases."""
    suite = unittest.TestSuite()

    for module_name in test_modules:
        try:
            module = import_test_module(module_name)
            # Find all test cases in the module
            for name, obj in vars(module).items():
                if (
                    isinstance(obj, type)
                    and issubclass(obj, unittest.TestCase)
                    and obj != unittest.TestCase
                ):
                    suite.addTest(loader.loadTestsFromTestCase(obj))
        except Exception as e:
            print(f"Error loading {module_name}: {e}")

    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
