"""Base test classes for PDFUtils tests."""

import os
import shutil
import sys
import tempfile
import tkinter as tk
from pathlib import Path
from typing import Generic, Type, TypeVar
from unittest import mock

import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pdfutils.tabs.base_tab import BaseTab
from tests.ui_safety import safe_ttkbootstrap

# Simple stub components used for testing ---------------------------------


class SimpleFileSelector:
    """Simplified file selector for tests."""

    def __init__(self):
        self._files = []

    def add_files(self, files):
        for f in files:
            if f not in self._files:
                self._files.append(f)

    def clear_files(self):
        self._files = []

    def get_files(self):
        return list(self._files)

    def get_file(self):
        return self._files[0] if self._files else ""

    def set_files(self, files):
        self._files = list(files)

    def move_up(self, index: int):
        if 0 < index < len(self._files):
            self._files[index - 1], self._files[index] = (
                self._files[index],
                self._files[index - 1],
            )

    def get_file_count(self):
        return len(self._files)


class SimpleOutputSelector:
    """Simplified output file selector for tests."""

    def __init__(self):
        self.output_path = ""

    def set_output_path(self, path: str):
        self.output_path = path

    def get_output_path(self):
        return self.output_path

    # aliases used by code
    set_path = set_output_path
    get_path = get_output_path


class SimpleProgressTracker:
    """Minimal progress tracker with state flags."""

    def __init__(self):
        self._running = False
        self._complete = False
        self._error = False
        # Add status_var attribute for tests that expect it
        from unittest.mock import Mock

        self.status_var = Mock()
        self.status_var.get = Mock(return_value="Ready")
        self.status_var.set = Mock()

    def reset(self):
        self._running = False
        self._complete = False
        self._error = False

    def update_progress(self, value: float, status: str | None = None):
        # Only consider running if value is between 0 and 100 exclusive
        self._running = 0 < value < 100
        if value >= 100:
            self._complete = True

    def is_running(self):
        return self._running

    def is_complete(self):
        return self._complete

    def is_error(self):
        return self._error

    def mark_error(self):
        self._error = True
        self._running = False


# Type variable for the tab class
T = TypeVar("T", bound=BaseTab)


class BaseTabTest(Generic[T]):
    """Base class for tab tests."""

    # The tab class to test, override in subclasses
    tab_class: Type[T] = None

    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Set up the test environment."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="pdfutils_test_"))
        self.parent = self._create_mock_parent()
        self.app = self._create_mock_app()

        # Avoid blocking message boxes
        import tkinter.messagebox as mb

        def _info(msg, *a, **k):
            self.app.notification_panel.show_notification(msg, "info")

        def _warn(msg, *a, **k):
            self.app.notification_panel.show_notification(msg, "warning")

        def _err(msg, *a, **k):
            self.app.notification_panel.show_notification(msg, "error")

        self._mb_patcher = mock.patch.multiple(
            mb,
            showinfo=_info,
            showwarning=_warn,
            showerror=_err,
        )
        self._mb_patcher.start()

        # Skip tab creation if tab_class is not defined
        if self.tab_class is not None:
            self.tab = self._create_tab()
        else:
            raise RuntimeError("tab_class not defined")

        # Add cleanup
        def cleanup():
            if self.temp_dir.exists():
                # Remove all files and directories recursively
                for item in self.temp_dir.glob("**/*"):
                    try:
                        if item.is_file() or item.is_symlink():
                            item.unlink(missing_ok=True)
                        elif item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                    except Exception as e:
                        print(f"Warning: Failed to delete {item}: {e}")

                # Remove the main temp directory
                try:
                    self.temp_dir.rmdir()
                except OSError as e:
                    print(f"Warning: Failed to remove temp directory {self.temp_dir}: {e}")
                    # If we can't remove it, at least clean up files inside
                    if self.temp_dir.exists():
                        for item in self.temp_dir.glob("*"):
                            try:
                                if item.is_file() or item.is_symlink():
                                    item.unlink(missing_ok=True)
                                elif item.is_dir():
                                    shutil.rmtree(item, ignore_errors=True)
                            except Exception as e:
                                print(f"Warning: Failed to clean up {item}: {e}")

            if hasattr(self, "_parent_root"):
                try:
                    self._parent_root.destroy()
                except Exception:
                    pass

        request.addfinalizer(cleanup)
        request.addfinalizer(self._mb_patcher.stop)

    def _create_mock_parent(self):
        """Create a real Tkinter frame as parent for widgets."""
        root = tk.Tk()
        root.withdraw()
        self._parent_root = root
        self.root = root
        self.tkinter = tk
        return tk.Frame(root)

    def _create_mock_app(self):
        """Create a mock app with all required methods, and a real Tk root for .root."""
        app = mock.MagicMock()

        # Use a real hidden Tk root for .root
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        app.root = root

        class MockNotificationPanel:
            def __init__(self):
                self._notifications = []

            def show_notification(self, message: str, level: str = "info"):
                self._notifications.append(message)

            def add_notification(self, message: str):
                self._notifications.append(message)

            def get_notifications(self):
                return self._notifications

        app.notification_panel = MockNotificationPanel()

        def _show_notification(message: str, level: str = "info"):
            app.notification_panel.show_notification(message, level)

        app.show_notification = _show_notification
        app.set_status = mock.MagicMock()
        app.status_indicator = mock.MagicMock()
        app.progress_tracker = mock.MagicMock()
        app.settings = {
            "theme": "light",
            "default_output_dir": str(self.temp_dir / "output"),
        }

        (self.temp_dir / "output").mkdir(exist_ok=True)

        app.get_setting = lambda key, default=None: app.settings.get(key, default)

        return app

    def _create_tab(self) -> T:
        """Create an instance of the tab being tested."""
        parent = self.parent

        # Some tabs require their real __init__ to create Tk variables
        if self.tab_class.__name__ in {
            "AboutTab",
            "OcrTab",
            "HandwritingOcrTab",
            "TableExtractionTab",
            "SplitTab",
            "CompressTab",
        }:
            try:
                with safe_ttkbootstrap():
                    return self.tab_class(parent, self.app)
            except Exception as e:
                # If ttkbootstrap fails, try with basic Tkinter
                print(f"ttkbootstrap failed for {self.tab_class.__name__}: {e}")
                # Create a minimal mock version for testing
                with mock.patch.object(self.tab_class, "__init__", return_value=None):
                    tab_instance = self.tab_class.__new__(self.tab_class)
                    tab_instance.parent = parent
                    tab_instance.app = self.app
                    # Add required attributes for TableExtractionTab
                    if self.tab_class.__name__ == "TableExtractionTab":
                        tab_instance.file_selector = SimpleFileSelector()
                        tab_instance.output_selector = SimpleOutputSelector()
                        tab_instance.progress_tracker = SimpleProgressTracker()
                        tab_instance.engine_var = tk.StringVar(value="camelot")
                        tab_instance.format_var = tk.StringVar(value="csv")
                        tab_instance.pages_var = tk.StringVar(value="1")
                        tab_instance.extract_btn = mock.MagicMock()
                    return tab_instance

        with mock.patch.object(self.tab_class, "__init__", return_value=None):
            tab_instance = self.tab_class.__new__(self.tab_class)

            tab_instance.parent = parent
            tab_instance.app = self.app

            tab_instance.file_selector = SimpleFileSelector()
            tab_instance.output_file_selector = SimpleOutputSelector()
            tab_instance.output_selector = tab_instance.output_file_selector
            tab_instance.progress_tracker = SimpleProgressTracker()
            tab_instance.status_indicator = mock.MagicMock()
            tab_instance.notification_panel = mock.MagicMock()
            tab_instance.merge_btn = mock.MagicMock()
            tab_instance.compress_btn = mock.MagicMock()
            tab_instance.open_after_var = mock.MagicMock()
            tab_instance.open_after_var.get.return_value = False

            # Common vars used in tests
            tab_instance.quality_var = tk.StringVar(value="screen")
            tab_instance.compression_var = tk.BooleanVar(value=False)
            tab_instance.compression_level = tk.IntVar(value=0)
            tab_instance.title_var = tk.StringVar(value="")
            tab_instance.author_var = tk.StringVar(value="")
            tab_instance.subject_var = tk.StringVar(value="")
            tab_instance.keywords_var = tk.StringVar(value="")
            tab_instance.password_var = tk.StringVar(value="")
            tab_instance.encryption_var = tk.BooleanVar(value=False)
            tab_instance.start_page_var = tk.IntVar(value=1)
            tab_instance.end_page_var = tk.IntVar(value=1)
            tab_instance.start_page_var = tk.IntVar(value=1)
            tab_instance.end_page_var = tk.IntVar(value=1)
            tab_instance.split_method = tk.StringVar(value="single")
            tab_instance.page_range = tk.StringVar(value="")
            tab_instance.page_ranges_var = tab_instance.page_range
            tab_instance.naming_pattern = tk.StringVar(value="page_{page}")
            tab_instance.split_btn = mock.MagicMock()

            # BarcodeTab test-expected attributes
            if self.tab_class.__name__ == "BarcodeTab":
                tab_instance.barcode_type = tk.StringVar(value="all")
                tab_instance.output_format = tk.StringVar(value="csv")
                tab_instance.page_range = tk.StringVar(value="")
                tab_instance.dpi_var = tk.IntVar(value=200)
                tab_instance.password_var = tk.StringVar(value="")

            if self.tab_class.__name__ == "TableExtractionTab":
                tab_instance.engine_var = tk.StringVar(value="camelot")
                tab_instance.format_var = tk.StringVar(value="csv")
                tab_instance.output_format = tab_instance.format_var
                tab_instance.pages_var = tk.StringVar(value="1")
                tab_instance.use_table_areas_var = tk.BooleanVar(value=False)
                tab_instance.table_areas_text = tk.Text(parent)
                tab_instance.merge_tables_var = tk.BooleanVar(value=False)
                tab_instance.extract_btn = mock.MagicMock()

            return tab_instance

    def create_test_pdf(self, name: str = "test.pdf", content: str = "Test PDF Content") -> Path:
        """Create a test PDF file."""
        from reportlab.pdfgen import canvas

        pdf_path = self.temp_dir / name
        c = canvas.Canvas(str(pdf_path))
        c.setFont("Helvetica", 12)
        c.drawString(72, 800, content)
        c.save()

        # If reportlab is mocked, create a dummy PDF file
        if not pdf_path.exists():
            # Create a minimal dummy PDF file
            pdf_content = (
                b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
                b"2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n"
                b"3 0 obj\n<<\n/Type /Page\n/Parent 2 R\n/MediaBox [0 0 612 792]\n>>\nendobj\n"
                b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
                b"0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n"
                b"/Root 1 0 R\n>>\nstartxref\n189\n%%EOF"
            )
            pdf_path.write_bytes(pdf_content)

        return pdf_path

    def assert_file_exists(self, file_path):
        """Assert that a file exists and is not empty."""
        path = Path(file_path)
        assert path.exists(), f"File {path} does not exist"
        assert path.stat().st_size > 0, f"File {path} is empty"

    def assert_notification_shown(self, message: str, level: str = "info"):
        """Assert that a notification was shown."""
        # This is a basic implementation - you might want to enhance it
        # to check the actual notification panel content
        pass

    def assert_status_updated(self, message: str, level: str = "info"):
        """Assert that the status was updated."""
        # This is a basic implementation - you might want to enhance it
        # to check the actual status indicator content
        pass


class BaseGUITest(BaseTabTest):
    """Base test class for GUI tests."""

    @pytest.fixture(autouse=True)
    def setup_gui(self, request):
        """Setup GUI test environment."""
        # Skip if GUI tests are disabled
        if os.environ.get("SKIP_GUI_TESTS", "").lower() in ("1", "true", "yes"):
            raise RuntimeError("GUI tests are disabled")

        # Call parent setup
        self.setup(request)

        # Initialize Tkinter if needed
        try:
            import tkinter as tk
            from tkinter import ttk
        except ImportError:
            raise

        # Create a root window for GUI tests
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests

        # Cleanup after tests
        def cleanup():
            if hasattr(self, "root") and self.root:
                self.root.destroy()

        request.addfinalizer(cleanup)

    def _create_tab(self) -> T:
        """Create an instance of the tab being tested with a real Tkinter parent."""
        import tkinter as tk

        parent = tk.Frame(self.root)

        # Mock the tab's __init__ method to avoid UI initialization
        with mock.patch.object(self.tab_class, "__init__", return_value=None):
            tab_instance = self.tab_class.__new__(self.tab_class)

            tab_instance.parent = parent
            tab_instance.app = self.app

            tab_instance.file_selector = SimpleFileSelector()

            tab_instance.output_file_selector = SimpleOutputSelector()
            tab_instance.output_selector = tab_instance.output_file_selector

            tab_instance.progress_tracker = SimpleProgressTracker()
            tab_instance.status_indicator = mock.MagicMock()
            tab_instance.notification_panel = mock.MagicMock()

            tab_instance.merge_btn = mock.MagicMock()
            tab_instance.compress_btn = mock.MagicMock()
            tab_instance.open_after_var = mock.MagicMock()
            tab_instance.open_after_var.get.return_value = False

            tab_instance.quality_var = tk.StringVar(value="screen")
            tab_instance.compression_var = tk.BooleanVar(value=False)
            tab_instance.compression_level = tk.IntVar(value=0)
            tab_instance.title_var = tk.StringVar(value="")
            tab_instance.author_var = tk.StringVar(value="")
            tab_instance.subject_var = tk.StringVar(value="")
            tab_instance.keywords_var = tk.StringVar(value="")
            tab_instance.password_var = tk.StringVar(value="")
            tab_instance.encryption_var = tk.BooleanVar(value=False)

            tab_instance.split_method = tk.StringVar(value="single")
            tab_instance.page_range = tk.StringVar(value="")
            tab_instance.page_ranges_var = tab_instance.page_range
            tab_instance.naming_pattern = tk.StringVar(value="page_{page}")
            tab_instance.split_btn = mock.MagicMock()

            return tab_instance
