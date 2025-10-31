#!/usr/bin/env python3
"""
Pytest-style tests for download functionality

Tests download thread management, progress tracking, and format selection
without any GUI creation or user interaction.
"""

import os
import queue
import shutil
import tempfile
from unittest.mock import Mock, patch

import pytest

from download_threads import DownloadThread


@pytest.fixture
def test_url():
    """Provide a test YouTube URL"""
    return "https://www.youtube.com/watch?v=test123"


@pytest.fixture
def test_output_path():
    """Provide a temporary output directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def update_queue():
    """Provide a fresh update queue"""
    return queue.Queue()


def test_download_thread_initialization_automatic_format(
    test_url, test_output_path, update_queue
):
    """Test DownloadThread initialization with automatic format selection"""
    thread = DownloadThread(
        url=test_url,
        format_id="best",
        output_path=test_output_path,
        update_queue=update_queue,
    )

    assert thread.url == test_url
    assert thread.format_id == "best"
    assert thread.output_path == test_output_path
    assert thread.video_format_id is None
    assert thread.audio_format_id is None
    assert thread.cancelled is False


def test_download_thread_initialization_manual_format(
    test_url, test_output_path, update_queue
):
    """Test DownloadThread initialization with manual format selection"""
    thread = DownloadThread(
        url=test_url,
        format_id=None,
        output_path=test_output_path,
        update_queue=update_queue,
        video_format_id="137",
        audio_format_id="140",
    )

    assert thread.url == test_url
    assert thread.format_id is None
    assert thread.video_format_id == "137"
    assert thread.audio_format_id == "140"
    assert thread.cancelled is False


def test_format_string_construction_manual_selection(
    test_url, test_output_path, update_queue
):
    """Test format string construction for manual selection"""
    thread = DownloadThread(
        url=test_url,
        format_id=None,
        output_path=test_output_path,
        update_queue=update_queue,
        video_format_id="137",
        audio_format_id="140",
    )

    with (
        patch("download_threads.yt_dlp.YoutubeDL") as mock_ytdl,
        patch("download_threads.check_ffmpeg", return_value=True),
    ):
        mock_ytdl_instance = Mock()
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        mock_ytdl.return_value.__exit__.return_value = None

        thread.run()

        mock_ytdl.assert_called()
        call_args_list = mock_ytdl.call_args_list
        found_correct_format = False

        for call_args in call_args_list:
            if call_args and len(call_args) > 0:
                ydl_opts = call_args[0][0] if call_args[0] else {}
                if isinstance(ydl_opts, dict) and "format" in ydl_opts:
                    if ydl_opts["format"] == "137+140":
                        found_correct_format = True
                        break

        assert (
            found_correct_format
        ), "Expected format '137+140' not found in yt-dlp calls"


def test_format_string_construction_automatic_selection(
    test_url, test_output_path, update_queue
):
    """Test format string construction for automatic selection"""
    thread = DownloadThread(
        url=test_url,
        format_id="best",
        output_path=test_output_path,
        update_queue=update_queue,
    )

    with (
        patch("download_threads.yt_dlp.YoutubeDL") as mock_ytdl,
        patch("download_threads.check_ffmpeg", return_value=True),
    ):
        mock_ytdl_instance = Mock()
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        mock_ytdl.return_value.__exit__.return_value = None

        thread.run()

        mock_ytdl.assert_called()
        call_args_list = mock_ytdl.call_args_list
        found_best_format = False

        for call_args in call_args_list:
            if call_args and len(call_args) > 0:
                ydl_opts = call_args[0][0] if call_args[0] else {}
                if isinstance(ydl_opts, dict) and "format" in ydl_opts:
                    format_str = ydl_opts["format"]
                    if format_str.startswith("best"):
                        found_best_format = True
                        break

        assert (
            found_best_format
        ), "Expected format starting with 'best' not found in yt-dlp calls"


def test_download_success_flow(test_url, test_output_path, update_queue):
    """Test successful download flow"""
    with (
        patch("download_threads.check_ffmpeg", return_value=True),
        patch("download_threads.yt_dlp.YoutubeDL") as mock_ytdl,
    ):
        mock_ytdl_instance = Mock()

        def create_test_file(url_list):
            test_file = os.path.join(test_output_path, "test_video.mp4")
            with open(test_file, "w") as f:
                f.write("test video content")

        mock_ytdl_instance.download.side_effect = create_test_file
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        mock_ytdl.return_value.__exit__.return_value = None

        thread = DownloadThread(
            url=test_url,
            format_id="best",
            output_path=test_output_path,
            update_queue=update_queue,
        )

        thread.run()

        mock_ytdl_instance.download.assert_called_once_with([test_url])

        messages = []
        while not update_queue.empty():
            messages.append(update_queue.get())

        status_messages = [msg for msg in messages if msg.get("type") == "status"]
        finished_messages = [msg for msg in messages if msg.get("type") == "finished"]

        assert len(status_messages) > 0
        assert len(finished_messages) == 1
        assert (
            "Download completed:" in finished_messages[0]["text"]
            or "completed successfully" in finished_messages[0]["text"]
        )


def test_download_error_flow(test_url, test_output_path, update_queue):
    """Test download error handling flow"""
    with (
        patch("download_threads.check_ffmpeg", return_value=True),
        patch("download_threads.yt_dlp.YoutubeDL") as mock_ytdl,
    ):
        mock_ytdl_instance = Mock()
        mock_ytdl_instance.download.side_effect = Exception("Download failed")
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        mock_ytdl.return_value.__exit__.return_value = None

        thread = DownloadThread(
            url=test_url,
            format_id="best",
            output_path=test_output_path,
            update_queue=update_queue,
        )

        thread.run()

        messages = []
        while not update_queue.empty():
            messages.append(update_queue.get())

        error_messages = [msg for msg in messages if msg.get("type") == "error"]
        assert len(error_messages) == 1
        assert "Download failed" in error_messages[0]["text"]


def test_progress_hook_with_total_bytes(test_url, test_output_path, update_queue):
    """Test progress hook with total bytes information"""
    thread = DownloadThread(
        url=test_url,
        format_id="best",
        output_path=test_output_path,
        update_queue=update_queue,
    )

    progress_data = {
        "status": "downloading",
        "downloaded_bytes": 5000000,  # 5MB
        "total_bytes": 10000000,  # 10MB
        "speed": 1024000,  # 1MB/s
    }

    thread.progress_hook(progress_data)

    messages = []
    while not update_queue.empty():
        messages.append(update_queue.get())

    progress_messages = [msg for msg in messages if msg.get("type") == "progress"]
    status_messages = [msg for msg in messages if msg.get("type") == "status"]

    assert len(progress_messages) == 1
    assert progress_messages[0]["value"] == 50  # 50% progress

    assert len(status_messages) == 1
    assert "50%" in status_messages[0]["text"]


def test_progress_hook_with_percent_string(test_url, test_output_path, update_queue):
    """Test progress hook with percent string information"""
    thread = DownloadThread(
        url=test_url,
        format_id="best",
        output_path=test_output_path,
        update_queue=update_queue,
    )

    progress_data = {"status": "downloading", "_percent_str": "75.5%"}

    thread.progress_hook(progress_data)

    messages = []
    while not update_queue.empty():
        messages.append(update_queue.get())

    progress_messages = [msg for msg in messages if msg.get("type") == "progress"]
    assert len(progress_messages) == 1
    assert progress_messages[0]["value"] == 75


def test_quality_aware_fallbacks(test_url, test_output_path, update_queue):
    """Test quality-aware fallback sequence generation"""
    thread = DownloadThread(
        url=test_url,
        format_id="best",
        output_path=test_output_path,
        update_queue=update_queue,
    )

    fallbacks_merging = thread._create_quality_aware_fallbacks("137+140", True)
    assert "137+140" in fallbacks_merging
    assert "best[height<=720]" in fallbacks_merging
    assert "best[height<=480]" in fallbacks_merging
    assert "best" in fallbacks_merging

    fallbacks_best = thread._create_quality_aware_fallbacks("best", False)
    assert "best" in fallbacks_best
    assert "best[height<=1080]" in fallbacks_best
    assert "best[height<=720]" in fallbacks_best
    assert "best[height<=480]" in fallbacks_best


def test_ffmpeg_unavailable_fallback(test_url, test_output_path, update_queue):
    """Test fallback when FFmpeg is unavailable for merging"""
    with patch("download_threads.check_ffmpeg", return_value=False):
        thread = DownloadThread(
            url=test_url,
            format_id=None,
            output_path=test_output_path,
            update_queue=update_queue,
            video_format_id="137",
            audio_format_id="140",
        )

        with patch("download_threads.yt_dlp.YoutubeDL") as mock_ytdl:
            mock_ytdl_instance = Mock()
            mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
            mock_ytdl.return_value.__exit__.return_value = None

            thread.run()

            messages = []
            while not update_queue.empty():
                messages.append(update_queue.get())

            status_messages = [msg for msg in messages if msg.get("type") == "status"]
            ffmpeg_warnings = [
                msg for msg in status_messages if "FFmpeg not available" in msg["text"]
            ]

            assert len(ffmpeg_warnings) > 0


def test_cookie_integration_in_download():
    """Test cookie integration in download process"""
    with (
        patch("download_threads.get_cookie_manager") as mock_get_cookie_manager,
        patch("download_threads.yt_dlp.YoutubeDL") as mock_ytdl,
    ):
        mock_cookie_manager = Mock()
        mock_cookie_manager.get_cookies_for_ytdlp.return_value = (
            "chrome",
            "/path/to/cookies",
        )
        mock_get_cookie_manager.return_value = mock_cookie_manager

        mock_ytdl_instance = Mock()
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        mock_ytdl.return_value.__exit__.return_value = None

        thread = DownloadThread(
            url="https://www.youtube.com/watch?v=test123",
            format_id="best",
            output_path="/test/output",
            update_queue=queue.Queue(),
        )

        thread.run()

        assert (
            mock_get_cookie_manager.call_count > 0
        ), "Cookie manager should be called at least once"
        mock_ytdl.assert_called()
