"""
Pytest-style tests for yt-dlp cookie options integration

Tests that DownloadThread properly uses cookie manager data in yt-dlp options.
"""

import os
import queue
import tempfile
from unittest.mock import patch

import pytest

from cookie_manager import CookieManager


NETSCAPE_SAMPLE = """# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1791957520	VISITOR_INFO1_LIVE	abcd1234
.youtube.com	TRUE	/	TRUE	1791957520	SID	xyz
"""


class DummyYDL:
    """Mock YoutubeDL that captures options without network calls"""

    def __init__(self, opts):
        # expose options for assertion
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def download(self, urls):
        # no-op to avoid network
        return 0


@pytest.fixture
def cookie_manager_with_manual_import():
    """Provide a CookieManager with manually imported cookies"""
    cm = CookieManager()
    with tempfile.NamedTemporaryFile(
        "w", delete=False, suffix=".txt", encoding="utf-8", newline="\n"
    ) as f:
        f.write(NETSCAPE_SAMPLE)
        manual_path = f.name

    assert cm.import_cookie_file(manual_path) is True

    yield cm, manual_path

    # Cleanup
    try:
        if os.path.exists(manual_path):
            os.unlink(manual_path)
    except Exception:
        pass


@pytest.fixture
def tmpdir_path():
    """Provide a temporary directory for test outputs"""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    # Cleanup could be added here if needed


def test_downloadthread_uses_cookiefile_from_manual_import(
    cookie_manager_with_manual_import, tmpdir_path
):
    """Test that DownloadThread uses cookiefile from manual import"""
    cm, manual_path = cookie_manager_with_manual_import

    # Lazy import to ensure patches take effect
    from download_threads import DownloadThread

    # Minimal queue for updates
    q = queue.Queue()

    # Patch: return our cm and reduce fallbacks to a single format
    with patch("download_threads.get_cookie_manager", return_value=cm), patch(
        "download_threads.yt_dlp.YoutubeDL", side_effect=lambda opts: DummyYDL(opts)
    ), patch.object(
        DownloadThread, "_create_quality_aware_fallbacks", return_value=["best"]
    ):

        dt = DownloadThread(
            url="https://www.youtube.com/watch?v=dummy",
            format_id="best",
            output_path=tmpdir_path,
            update_queue=q,
        )

        # Run synchronously to capture ydl_opts via DummyYDL
        dt.run()

        # Verify the cookie manager returns proper data
        data = cm.get_cookies_for_ytdlp_enhanced()
        assert data.get("source") == "manual_import"
        cookie_file = data.get("cookie_file")
        assert cookie_file and os.path.exists(cookie_file)
