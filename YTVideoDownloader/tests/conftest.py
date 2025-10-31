from unittest.mock import Mock, patch

import pytest


# If the system's Tcl/Tk is not available (headless or broken install), we
# replace CustomTkinter widget classes with lightweight stubs so that
# importing `gui.main_window` will not attempt to create a real Tk root.
try:
    import tkinter as _tk

    try:
        # Try to create and destroy a root window to detect a working Tcl/Tk
        root = _tk.Tk()
        root.destroy()
        _have_tk = True
    except Exception:
        _have_tk = False
except Exception:
    _have_tk = False

if not _have_tk:
    try:
        import customtkinter as _ctk

        class _CTKStub:
            def __init__(self, *args, **kwargs):
                # store attributes if tests want to inspect
                pass

            def configure(self, *args, **kwargs):
                return None

            def set(self, *args, **kwargs):
                return None

            def get(self, *args, **kwargs):
                return ""

            def grid(self, *args, **kwargs):
                return None

            def grid_remove(self, *args, **kwargs):
                return None

            def after(self, *args, **kwargs):
                return None

            def destroy(self, *args, **kwargs):
                return None

        # Replace common widget classes with the stub so class bases bind to them
        for _name in (
            "CTk",
            "CTkFrame",
            "CTkTabview",
            "CTkLabel",
            "CTkEntry",
            "CTkButton",
            "CTkCheckBox",
            "CTkComboBox",
            "CTkProgressBar",
        ):
            try:
                setattr(_ctk, _name, _CTKStub)
            except Exception:
                pass
    except Exception:
        # If customtkinter is not available at import-time, don't crash here;
        # the tests will handle it or raise later when importing GUI modules.
        pass

    # If Tcl/Tk is unavailable, ensure VideoDownloaderApp.__init__ won't try
    # to create a real CTk root. Replace the constructor with a lightweight
    # initializer that mirrors the important attributes without initializing
    # tkinter internals. This helps tests that import the class at module
    # import time (so base classes may be bound) but still want to create
    # instances in a headless environment.
    try:
        import queue as _queue
        from unittest.mock import Mock as _Mock

        import gui.main_window as _gw

        cls = getattr(_gw, "VideoDownloaderApp", None)
        if cls is not None:

            def _light_init(self, *args, **kwargs):
                # minimal attributes expected by tests
                try:
                    from app_logger import AppLogger as _AppLogger

                    self.logger = _AppLogger.get_instance()
                except Exception:
                    self.logger = _Mock()

                self._destroyed = False
                self.formats = []
                self.video_formats = []
                self.audio_formats = []
                self.format_id_map = {}
                self.video_format_id_map = {}
                self.audio_format_id_map = {}
                self.playlist_info = None
                self.current_video_url = None
                self.current_video_info = None
                self.single_video_downloader = None
                self.playlist_downloader = None

                # Try to obtain cookie manager if available
                try:
                    from cookie_manager import get_cookie_manager as _gcm

                    try:
                        self.cookie_manager = _gcm()
                    except Exception:
                        self.cookie_manager = None
                except Exception:
                    self.cookie_manager = None

                # Lightweight queue and common GUI placeholders
                self.update_queue = _queue.Queue()
                self.cookie_status_var = _Mock()
                self.cookie_status_label = _Mock()
                self.refresh_cookies_btn = _Mock()
                self.import_cookies_btn = _Mock()
                self.browser_refresh_btn = _Mock()
                self.browser_combo = _Mock()
                self.cookie_operation_in_progress = False
                self.after = _Mock()

            # Replace the constructor
            try:
                cls.__init__ = _light_init
            except Exception:
                pass
    except Exception:
        pass


@pytest.fixture(autouse=True)
def patch_loggers():
    """Autouse fixture that patches AppLogger to avoid file I/O.

    Note: we intentionally do NOT patch CTk.__init__ here because some
    tests patch CustomTkinter in different ways; a dedicated fixture
    `mock_ctk_init` is provided if a test wants to stub the CTk ctor.
    """
    patches = []
    # Patch the GUI's AppLogger to prevent file I/O
    p1 = patch("gui.main_window.AppLogger")
    mock_app_logger = p1.start()
    patches.append(p1)

    # Patch cookie_manager's AppLogger too (some tests patch this separately)
    p2 = patch("cookie_manager.AppLogger")
    mock_cookie_logger = p2.start()
    patches.append(p2)

    try:
        yield {
            "mock_app_logger": mock_app_logger,
            "mock_cookie_logger": mock_cookie_logger,
        }
    finally:
        for p in reversed(patches):
            p.stop()


@pytest.fixture
def mock_ctk_init():
    """Fixture to patch gui.main_window.ctk.CTk.__init__ so constructing
    a VideoDownloaderApp won't open real windows. Tests can opt-in to use
    this when they need a CTk stub.
    """
    p = patch("gui.main_window.ctk.CTk.__init__")
    mock_ctk_init = p.start()
    mock_ctk_init.return_value = None
    try:
        yield mock_ctk_init
    finally:
        p.stop()


@pytest.fixture
def mock_get_cookie_manager():
    """Patch gui.main_window.get_cookie_manager and return a Mock CookieManager.

    Tests can use this fixture to get a fresh Mock(spec=CookieManager) and
    inspect calls or set return values for the cookie manager used by the app.
    """
    with patch("gui.main_window.get_cookie_manager") as mg:
        # Delay importing CookieManager to avoid circular imports during collection
        try:
            from cookie_manager import CookieManager

            mock_manager = Mock(spec=CookieManager)
        except Exception:
            # If CookieManager is not importable at collection time, fall back to a plain Mock
            mock_manager = Mock()

        mg.return_value = mock_manager
        yield mock_manager


@pytest.fixture
def video_downloader_app(mock_get_cookie_manager):
    """Factory fixture that builds a VideoDownloaderApp instance with heavy
    GUI setup methods patched out and common widget attributes replaced with Mocks.

    Usage:
        def test_x(video_downloader_app):
            app = video_downloader_app
            ...
    """
    # Import here so the patching above is active
    from gui.main_window import VideoDownloaderApp

    # Patch the expensive setup methods on the class so __init__ returns quickly
    with (
        patch.object(VideoDownloaderApp, "setup_window"),
        patch.object(VideoDownloaderApp, "setup_ui"),
        patch.object(VideoDownloaderApp, "setup_variables"),
        patch.object(VideoDownloaderApp, "process_queue"),
        patch.object(VideoDownloaderApp, "after"),
    ):
        app = VideoDownloaderApp()

    # Provide commonly used GUI attributes as mocks so tests can assert on them
    app.cookie_status_var = Mock()
    app.cookie_status_label = Mock()
    app.refresh_cookies_btn = Mock()
    app.import_cookies_btn = Mock()
    app.browser_refresh_btn = Mock()
    app.browser_combo = Mock()
    app.cookie_operation_in_progress = False
    app.logger = Mock()
    app.after = Mock()

    # Create a simple state holder class for Tkinter-like variables
    class MockVar:
        def __init__(self, value=""):
            self._value = value

        def get(self):
            return self._value

        def set(self, value):
            self._value = value

    # Additional mocks for state management tests (use MockVar for stateful attributes)
    app.url_var = MockVar()
    app.format_mode_var = MockVar()
    app.status_var = MockVar()
    app.get_info_btn = Mock()
    app.download_btn = Mock()
    app.format_combo = Mock()
    app.video_format_combo = Mock()
    app.audio_format_combo = Mock()
    app.progress_bar = Mock()
    app.auto_format_frame = Mock()
    app.manual_format_frame = Mock()
    app.tabview = Mock()
    app.current_tab = "Single Video"
    app.playlist_url_var = MockVar()
    app.output_dir_var = MockVar()
    app.current_video_url = None
    app.formats = []
    app.video_formats = []
    app.audio_formats = []

    yield app
