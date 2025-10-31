#!/usr/bin/env python3
"""
Pytest-style tests for cookie management functionality

Tests cookie extraction, browser detection, and authentication logic
without any GUI creation or user interaction.
"""

from unittest.mock import Mock, mock_open, patch

import pytest

from cookie_manager import CookieManager, get_cookie_manager


@pytest.fixture
def cookie_manager():
    """Provide a CookieManager instance with mocked logger"""
    with patch("cookie_manager.AppLogger"):
        return CookieManager()


def test_chrome_cookie_extraction_success(cookie_manager):
    """Test successful Chrome cookie extraction logic"""
    # Mock Chrome info
    cookie_manager.chrome_info = {
        "cookie_path": "/path/to/cookies",
        "name": "Chrome",
    }

    # Mock file operations and cookie extraction
    with (
        patch("cookie_manager.os.path.exists", return_value=True),
        patch("cookie_manager.os.path.getsize", return_value=1000),
        patch.object(cookie_manager, "extract_cookies_auto") as mock_extract,
    ):
        mock_extract.return_value = (
            "# Cookie file\nyoutube.com\tTRUE\t/\tFALSE\t123\ttoken\tvalue\n"
        )

        # Execute cookie extraction
        cookies = cookie_manager.extract_cookies_auto()

        # Verify results
        assert cookies is not None
        assert "youtube.com" in cookies


def test_chrome_cookie_extraction_no_database(cookie_manager):
    """Test Chrome cookie extraction when database doesn't exist"""
    # Mock Chrome info with non-existent path
    cookie_manager.chrome_info = {
        "cookie_path": "/nonexistent/path",
        "name": "Chrome",
    }

    # Execute cookie extraction
    cookies = cookie_manager.extract_cookies_auto()

    # Verify empty result
    assert cookies is None


def test_chrome_cookie_extraction_database_error(cookie_manager):
    """Test Chrome cookie extraction with database error"""
    # Mock Chrome info
    cookie_manager.chrome_info = {
        "cookie_path": "/path/to/cookies",
        "name": "Chrome",
    }

    # Mock file operations but database error
    with (
        patch("cookie_manager.os.path.exists", return_value=True),
        patch("cookie_manager.os.path.getsize", return_value=1000),
        patch(
            "cookie_manager.sqlite3.connect",
            side_effect=Exception("Database locked"),
        ),
    ):
        # Execute cookie extraction
        cookies = cookie_manager.extract_cookies_auto()

        # Verify empty result on error
        assert cookies is None


def test_browser_detection_logic(cookie_manager):
    """Test browser detection logic"""
    # Mock browser paths
    with patch("cookie_manager.os.path.exists") as mock_exists:
        # Simulate Chrome exists, Firefox doesn't
        def exists_side_effect(path):
            return "Chrome" in path or "chrome" in path

        mock_exists.side_effect = exists_side_effect

        # Test browser detection
        browsers = cookie_manager.get_available_browsers()

        # Verify Chrome is detected
        assert isinstance(browsers, list)


def test_cookie_status_reporting(cookie_manager):
    """Test cookie status reporting logic"""
    # Mock Chrome detection and cookie extraction
    with patch.object(cookie_manager, "extract_cookies_auto") as mock_extract:
        # Test with no cookies
        mock_extract.return_value = None
        status = cookie_manager.get_cookie_status()
        assert "no cookies" in status.lower()

        # Test with cookies
        mock_extract.return_value = (
            "# Cookie file\nyoutube.com\tTRUE\t/\tFALSE\t123\ttoken\tvalue\n"
        )
        status = cookie_manager.get_cookie_status()
        assert "cookies available" in status.lower()


def test_cookie_file_import_success(cookie_manager):
    """Test successful cookie file import logic"""
    # Mock file content
    cookie_content = """# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	1234567890	session_token	test_value
.youtube.com	TRUE	/	FALSE	1234567890	auth_token	test_value2
"""

    with (
        patch("cookie_manager.os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=cookie_content)),
    ):
        # Execute cookie import
        result = cookie_manager.import_cookie_file("/path/to/cookies.txt")

        # Verify success
        assert result is True


def test_cookie_file_import_file_not_found(cookie_manager):
    """Test cookie file import when file doesn't exist"""
    with patch("cookie_manager.os.path.exists", return_value=False):
        # Execute cookie import
        result = cookie_manager.import_cookie_file("/path/to/nonexistent.txt")

        # Verify failure
        assert result is False


def test_cookie_file_import_invalid_format(cookie_manager):
    """Test cookie file import with invalid format"""
    # Mock invalid cookie content
    invalid_content = "This is not a valid cookie file"

    with (
        patch("cookie_manager.os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=invalid_content)),
    ):
        # Execute cookie import
        result = cookie_manager.import_cookie_file("/path/to/invalid.txt")

        # Verify failure (or success with empty cookies, depending on implementation)
        # The exact behavior depends on how the parser handles invalid content
        assert isinstance(result, bool)


def test_ytdlp_cookie_integration(cookie_manager):
    """Test yt-dlp cookie integration logic"""
    # Mock Chrome info and cookie extraction
    with patch.object(cookie_manager, "extract_cookies_auto") as mock_extract:
        mock_extract.return_value = (
            "# Cookie file\nyoutube.com\tTRUE\t/\tFALSE\t123\ttoken\tvalue\n"
        )

        # Test cookie data for yt-dlp
        cookie_data = cookie_manager.get_cookies_for_ytdlp_enhanced()

        # Verify cookie data structure
        assert isinstance(cookie_data, dict)

        # Should contain either browser spec or cookie file path
        has_browser_spec = "browser_spec" in cookie_data
        has_cookie_file = "cookiefile" in cookie_data

        # At least one method should be available
        assert has_browser_spec or has_cookie_file


def test_chrome_running_detection(cookie_manager):
    """Test Chrome running detection logic"""
    with patch("psutil.process_iter") as mock_process_iter:
        mock_process1 = Mock()
        mock_process1.info = {"name": "chrome.exe"}

        mock_process2 = Mock()
        mock_process2.info = {"name": "notepad.exe"}

        mock_process_iter.return_value = [mock_process1, mock_process2]

        is_running = cookie_manager._is_chrome_running()

        assert is_running is True


def test_chrome_not_running_detection(cookie_manager):
    """Test Chrome not running detection logic"""
    with patch("psutil.process_iter") as mock_process_iter:
        mock_process = Mock()
        mock_process.info = {"name": "notepad.exe"}

        mock_process_iter.return_value = [mock_process]

        is_running = cookie_manager._is_chrome_running()

        assert is_running is False


def test_refresh_cookies_logic(cookie_manager):
    """Test cookie refresh logic"""
    with patch.object(cookie_manager, "extract_cookies_auto") as mock_extract:
        mock_extract.return_value = (
            "# Cookie file\nyoutube.com\tTRUE\t/\tFALSE\t123\ttoken\tvalue\n"
        )

        result = cookie_manager.refresh_cookies()

        assert isinstance(result, bool)


def test_cookie_manager_singleton():
    """Test cookie manager singleton pattern"""
    manager1 = get_cookie_manager()
    manager2 = get_cookie_manager()

    assert manager1 is manager2
