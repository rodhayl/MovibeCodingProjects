"""
Pytest-style tests for cookie precedence logic

Tests that manual cookie imports override browser cookie detection.
"""

import os
import tempfile

import pytest

from cookie_manager import CookieManager


NETSCAPE_SAMPLE = """# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1791957520	VISITOR_INFO1_LIVE	abcd1234
.youtube.com	TRUE	/	TRUE	1791957520	SID	xyz
"""


@pytest.fixture
def cookie_manager_with_chrome():
    """Provide a CookieManager instance with simulated Chrome detection"""
    cm = CookieManager()
    # Simulate detected Chrome so browser path would normally be preferred
    cm.chrome_info = {
        "available": True,
        "name": "Chrome",
        "profile_path": os.path.join(
            "C:",
            "Users",
            "User",
            "AppData",
            "Local",
            "Google",
            "Chrome",
            "User Data",
            "Default",
        ),
        "user_data_dir": os.path.join(
            "C:", "Users", "User", "AppData", "Local", "Google", "Chrome", "User Data"
        ),
    }
    return cm


def test_manual_import_overrides_browser(cookie_manager_with_chrome):
    """Test that manual cookie import takes precedence over browser cookies"""
    # Write a temp cookie file and import it
    with tempfile.NamedTemporaryFile(
        "w", delete=False, suffix=".txt", encoding="utf-8", newline="\n"
    ) as f:
        f.write(NETSCAPE_SAMPLE)
        manual_path = f.name

    try:
        assert cookie_manager_with_chrome.import_cookie_file(manual_path) is True

        data = cookie_manager_with_chrome.get_cookies_for_ytdlp_enhanced()
        # Should prefer manual import even if Chrome available
        assert isinstance(data, dict)
        assert data.get("source") == "manual_import"
        assert "cookie_file" in data
        assert os.path.exists(data["cookie_file"])
    finally:
        try:
            os.unlink(manual_path)
        except Exception:
            pass
