#!/usr/bin/env python3
"""Pytest-style tests for GUI Cookie Management Feedback

This module is a migrated version of the `TestGUICookieFeedback` unittest
class in `tests/unit/test_gui_cookie_feedback.py`. It demonstrates using the
`video_downloader_app` and `mock_get_cookie_manager` fixtures from
`tests/conftest.py` to remove repetitive setUp boilerplate.
"""


def test_import_cookie_file_success_feedback(
    video_downloader_app, mock_get_cookie_manager, monkeypatch
):
    app = video_downloader_app
    mock_cm = mock_get_cookie_manager

    # Patch filedialog and os helpers
    monkeypatch.setattr(
        "gui.main_window.filedialog.askopenfilename",
        lambda *a, **k: "/path/to/cookies.txt",
    )
    monkeypatch.setattr("gui.main_window.os.path.exists", lambda p: True)
    monkeypatch.setattr("gui.main_window.os.access", lambda p, mode: True)
    monkeypatch.setattr("gui.main_window.os.path.getsize", lambda p: 1000)

    # Ensure cookie manager import returns True
    mock_cm.import_cookies_from_file.return_value = True
    mock_cm.get_cookie_status.return_value = "5 cookies available"

    # Patch threading.Thread to avoid executing thread body in test
    monkeypatch.setattr(
        "gui.main_window.threading.Thread",
        lambda *a, **k: type("T", (), {"start": lambda self: None})(),
    )

    app.import_cookie_file_enhanced()

    # Verify operation in progress flag is set
    assert app.cookie_operation_in_progress

    # Buttons should have been disabled (mock objects have configure)
    app.refresh_cookies_btn.configure.assert_called_with(state="disabled")
    app.import_cookies_btn.configure.assert_called_with(state="disabled")
    app.browser_refresh_btn.configure.assert_called_with(state="disabled")
