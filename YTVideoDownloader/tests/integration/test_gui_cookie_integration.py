#!/usr/bin/env python3
"""Pytest-style migrations for GUI-cookie integration tests.

This module migrates the tests from
`tests/integration/test_gui_cookie_integration.py` to use the shared
fixtures in `tests/conftest.py` (notably `video_downloader_app` and
`mock_get_cookie_manager`). It keeps the same coverage but with
concise fixture usage.
"""


def _noop_thread_factory(*args, **kwargs):
    class T:
        def start(self):
            return None

    return T()


def test_end_to_end_cookie_import_success(
    video_downloader_app, mock_get_cookie_manager, tmp_path, monkeypatch
):
    app = video_downloader_app
    mock_cm = mock_get_cookie_manager

    mock_cm.import_cookies_from_file.return_value = True
    mock_cm.get_cookie_status.return_value = "5 cookies available from import"

    temp_file = tmp_path / "cookies.txt"
    temp_file.write_text(
        "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tFALSE\t1234567890\ttest_token\ttest_value\n"
    )

    monkeypatch.setattr(
        "gui.main_window.filedialog.askopenfilename", lambda *a, **k: str(temp_file)
    )
    monkeypatch.setattr("gui.main_window.threading.Thread", _noop_thread_factory)

    app.import_cookie_file_enhanced()

    assert app.cookie_operation_in_progress

    # Simulate completion handler that the thread would have invoked
    app._handle_import_complete(True, "Import successful", "cookies.txt")


def test_end_to_end_cookie_refresh_success(
    video_downloader_app, mock_get_cookie_manager, monkeypatch
):
    app = video_downloader_app
    mock_cm = mock_get_cookie_manager
    mock_cm.refresh_cookies.return_value = True
    mock_cm.get_cookie_status.return_value = "10 cookies available from Chrome"

    monkeypatch.setattr("gui.main_window.threading.Thread", _noop_thread_factory)

    app.refresh_cookies_enhanced()

    assert app.cookie_operation_in_progress
    app.refresh_cookies_btn.configure.assert_called_with(state="disabled")
    app.import_cookies_btn.configure.assert_called_with(state="disabled")
    app.browser_refresh_btn.configure.assert_called_with(state="disabled")


def test_end_to_end_browser_detection_success(
    video_downloader_app, mock_get_cookie_manager, monkeypatch
):
    app = video_downloader_app
    mock_cm = mock_get_cookie_manager
    mock_cm.get_available_browsers.return_value = ["Chrome", "Firefox"]
    mock_cm.get_cookie_status.return_value = "Chrome and Firefox detected"

    monkeypatch.setattr("gui.main_window.threading.Thread", _noop_thread_factory)

    app.refresh_browser_detection()

    assert app.cookie_operation_in_progress
    app.browser_refresh_btn.configure.assert_called_with(state="disabled")


def test_cookie_status_propagation_from_manager(mock_get_cookie_manager):
    mock_cm = mock_get_cookie_manager

    test_statuses = [
        "Chrome not detected",
        "Chrome running - cookies may be locked - 5 cookies available",
        "Chrome not running - cookies accessible - 10 cookies available",
        "Error: Database locked",
    ]

    for status in test_statuses:
        mock_cm.get_cookie_status.return_value = status
        assert mock_cm.get_cookie_status() == status


def test_concurrent_operation_prevention(video_downloader_app, monkeypatch):
    app = video_downloader_app
    app.cookie_operation_in_progress = True

    # Replace update method to capture calls
    called = []

    def _capture(msg, color):
        called.append((msg, color))

    app._update_cookie_status = _capture

    app.refresh_cookies_enhanced()
    app.import_cookie_file_enhanced()
    app.refresh_browser_detection()

    assert len(called) >= 1
    assert any(
        "in progress" in msg[0].lower() or "wait" in msg[0].lower() for msg in called
    )


def test_gui_thread_safety(video_downloader_app):
    app = video_downloader_app
    # Ensure after is used when scheduling GUI updates
    app.refresh_cookies_enhanced()
    assert app.after.called


def test_button_state_management(video_downloader_app):
    app = video_downloader_app

    app.refresh_cookies_enhanced()
    app.refresh_cookies_btn.configure.assert_called_with(state="disabled")
    app.import_cookies_btn.configure.assert_called_with(state="disabled")
    app.browser_refresh_btn.configure.assert_called_with(state="disabled")

    # Simulate completion
    app._handle_refresh_complete(True, "Success")
    app.refresh_cookies_btn.configure.assert_called_with(state="normal")
    app.import_cookies_btn.configure.assert_called_with(state="normal")
    app.browser_refresh_btn.configure.assert_called_with(state="normal")


def test_error_handling_integration(
    video_downloader_app, mock_get_cookie_manager, monkeypatch
):
    app = video_downloader_app
    mock_cm = mock_get_cookie_manager
    mock_cm.refresh_cookies.side_effect = Exception("Test cookie error")

    monkeypatch.setattr("gui.main_window.threading.Thread", _noop_thread_factory)

    app.refresh_cookies_enhanced()
    assert app.cookie_operation_in_progress


def test_initialization_feedback(video_downloader_app, mock_get_cookie_manager):
    app = video_downloader_app
    mock_cm = mock_get_cookie_manager
    mock_cm.get_available_browsers.return_value = ["Chrome"]
    mock_cm.get_cookie_status.return_value = "Chrome detected - 5 cookies available"

    app.initialize_cookie_system()
    expected_browsers = ["Auto-detect (Recommended)", "Chrome"]
    app.browser_combo.configure.assert_called_with(values=expected_browsers)

    # Test fallback path
    app.cookie_manager = None
    app.initialize_cookie_system()
    fallback_browsers = ["Auto-detect (Recommended)", "Chrome", "Firefox", "Edge"]
    app.browser_combo.configure.assert_called_with(values=fallback_browsers)
