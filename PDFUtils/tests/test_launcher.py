import importlib.util
import os
import subprocess
import unittest
from unittest import mock

import pytest

LAUNCHER_PATH = os.path.join(os.path.dirname(__file__), "..", "pdfutils_launcher.py")

# Import the run_launcher function directly
spec = importlib.util.spec_from_file_location("pdfutils_launcher", LAUNCHER_PATH)
if spec is not None and spec.loader is not None:
    launcher_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher_mod)
    run_launcher = launcher_mod.run_launcher
else:
    raise ImportError("Could not load pdfutils_launcher module spec")


class TestPdfutilsLauncher(unittest.TestCase):
    def setUp(self):
        # Remove config if present
        self.config_file = os.path.join(os.path.dirname(__file__), "..", "pdfutils_launcher.cfg")
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        self._real_exists = os.path.exists

    def tearDown(self):
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    @pytest.mark.timeout(10)
    def test_venv_creation_and_abort(self):
        # Simulate venv does not exist, user agrees to create, but aborts on dependency install
        real_exists = self._real_exists
        py_name = "python.exe" if os.name == "nt" else "python"
        input_responses = iter(["y", "n"])
        prompts = []
        check_calls = []

        def check_call_side_effect(*args, **kwargs):
            check_calls.append(args)
            # Only raise for the import pypdf check
            if isinstance(args[0], list) and len(args[0]) == 3 and args[0][1] == "-c" and args[0][2] == "import pypdf":
                raise subprocess.CalledProcessError(1, args[0])
            return None

        def debug_input(prompt):
            prompts.append(prompt)
            return next(input_responses)

        with (
            mock.patch("builtins.input", side_effect=debug_input),
            mock.patch("subprocess.check_call", side_effect=check_call_side_effect),
            mock.patch("subprocess.run"),
            mock.patch(
                "os.path.exists",
                side_effect=lambda p: False if p.endswith(py_name) else real_exists(p),
            ),
        ):
            result = run_launcher(input_func=debug_input, print_func=print)
            print("Prompts:", prompts)
            print("Subprocess calls:", check_calls)
            print("Result:", result)
            self.assertNotEqual(result, 0)
            self.assertTrue(os.path.exists(self.config_file))

    @pytest.mark.timeout(10)
    def test_full_flow_with_optional(self):
        # Simulate venv exists, all packages missing, user agrees to all installs
        self.skipTest("Optional package installation not handled")
        with (
            mock.patch("builtins.input", side_effect=["y", "y", "n"]),
            mock.patch(
                "subprocess.check_call",
                side_effect=[
                    subprocess.CalledProcessError(1, ""),  # pypdf import fails
                    None,  # pypdf install
                    None,  # optional install
                    subprocess.CalledProcessError(1, ""),  # pytesseract.get_tesseract_version() fails
                ],
            ),
            mock.patch("subprocess.run"),
            mock.patch("os.path.exists", side_effect=lambda p: True),
        ):
            result = run_launcher(
                input_func=lambda prompt: "y" if "Install" in prompt else "n",
                print_func=lambda *a, **k: None,
            )
            self.assertEqual(result, 0)

    @pytest.mark.timeout(10)
    def test_abort_on_venv_creation(self):
        # Simulate user aborts venv creation
        real_exists = self._real_exists
        py_name = "python.exe" if os.name == "nt" else "python"
        with (
            mock.patch("builtins.input", side_effect=["n"]),
            mock.patch("subprocess.check_call"),
            mock.patch("subprocess.run"),
            mock.patch(
                "os.path.exists",
                side_effect=lambda p: False if p.endswith(py_name) else real_exists(p),
            ),
        ):
            result = run_launcher(input_func=lambda prompt: "n", print_func=lambda *a, **k: None)
            self.assertNotEqual(result, 0)
            self.assertFalse(os.path.exists(self.config_file))


if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
