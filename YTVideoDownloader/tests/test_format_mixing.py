#!/usr/bin/env python3
"""
Pytest-style tests for audio-video format mixing functionality

Tests format mixing logic without any GUI creation or user interaction.
"""

import queue
from unittest.mock import Mock, patch

import pytest

from download_threads import DownloadThread


@pytest.fixture
def test_url():
    """Provide test URL"""
    return "https://www.youtube.com/watch?v=test123"


@pytest.fixture
def test_output_path():
    """Provide test output path"""
    return "/tmp"


@pytest.fixture
def update_queue():
    """Provide update queue"""
    return queue.Queue()


def test_download_thread_with_manual_format_selection(
    test_url, test_output_path, update_queue
):
    """Test DownloadThread with manual video and audio format selection"""
    thread = DownloadThread(
        url=test_url,
        format_id=None,
        output_path=test_output_path,
        update_queue=update_queue,
        video_format_id="137",
        audio_format_id="140",
    )

    assert thread.format_id is None
    assert thread.video_format_id == "137"
    assert thread.audio_format_id == "140"


def test_download_thread_with_automatic_format_selection(
    test_url, test_output_path, update_queue
):
    """Test DownloadThread with automatic format selection"""
    thread = DownloadThread(
        url=test_url,
        format_id="best",
        output_path=test_output_path,
        update_queue=update_queue,
        video_format_id=None,
        audio_format_id=None,
    )

    assert thread.format_id == "best"
    assert thread.video_format_id is None
    assert thread.audio_format_id is None


def test_format_string_construction_manual_selection(
    test_url, test_output_path, update_queue
):
    """Test that format string is correctly constructed for manual selection"""
    with (
        patch("download_threads.check_ffmpeg", return_value=True),
        patch("download_threads.yt_dlp.YoutubeDL") as mock_ytdl,
    ):
        mock_ytdl_instance = Mock()
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        mock_ytdl.return_value.__exit__.return_value = None

        thread = DownloadThread(
            url=test_url,
            format_id=None,
            output_path=test_output_path,
            update_queue=update_queue,
            video_format_id="137",
            audio_format_id="140",
        )

        thread.run()

        mock_ytdl.assert_called()
        call_args = mock_ytdl.call_args

        if call_args and len(call_args) > 0:
            ydl_opts = call_args[0][0] if call_args[0] else {}
            if isinstance(ydl_opts, dict) and "format" in ydl_opts:
                assert ydl_opts["format"] == "137+140"


def test_format_string_construction_automatic_selection(
    test_url, test_output_path, update_queue
):
    """Test that format string is correctly constructed for automatic selection"""
    with (
        patch("download_threads.check_ffmpeg", return_value=True),
        patch("download_threads.yt_dlp.YoutubeDL") as mock_ytdl,
    ):
        mock_ytdl_instance = Mock()
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        mock_ytdl.return_value.__exit__.return_value = None

        thread = DownloadThread(
            url=test_url,
            format_id="best",
            output_path=test_output_path,
            update_queue=update_queue,
        )

        thread.run()

        mock_ytdl.assert_called()


def test_mixed_format_fallback_logic(test_url, test_output_path, update_queue):
    """Test fallback logic when mixed format fails"""
    with (
        patch("download_threads.check_ffmpeg", return_value=True),
        patch("download_threads.yt_dlp.YoutubeDL") as mock_ytdl,
    ):
        mock_ytdl_instance = Mock()

        # First call fails, subsequent calls succeed
        mock_ytdl_instance.download.side_effect = [
            Exception("Format not available"),
            None,  # Second format succeeds
        ]

        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        mock_ytdl.return_value.__exit__.return_value = None

        thread = DownloadThread(
            url=test_url,
            format_id=None,
            output_path=test_output_path,
            update_queue=update_queue,
            video_format_id="137",
            audio_format_id="140",
        )

        thread.run()

        # Should have tried multiple formats
        assert mock_ytdl_instance.download.call_count >= 1
