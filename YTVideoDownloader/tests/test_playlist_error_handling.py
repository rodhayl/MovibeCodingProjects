#!/usr/bin/env python3
"""
Pytest-style tests for playlist download error handling and recovery.
Tests various error conditions, network failures, and recovery mechanisms.
"""

import os
import queue
import shutil
import tempfile
import time
from unittest.mock import Mock, patch

import pytest

from download_threads import DownloadThread


@pytest.fixture
def temp_dir():
    """Provide temporary directory"""
    temp = tempfile.mkdtemp()
    yield temp
    if os.path.exists(temp):
        shutil.rmtree(temp)


@pytest.fixture
def update_queue():
    """Provide update queue"""
    return queue.Queue()


@pytest.fixture
def sample_video_urls():
    """Provide sample video URLs"""
    return [
        "https://www.youtube.com/watch?v=video1",
        "https://www.youtube.com/watch?v=video2",
        "https://www.youtube.com/watch?v=video3",
    ]


def get_queue_messages(queue_obj):
    """Helper to get all messages from queue"""
    messages = []
    while not queue_obj.empty():
        try:
            messages.append(queue_obj.get_nowait())
        except queue.Empty:
            break
    return messages


def test_network_connection_error(temp_dir, update_queue, sample_video_urls):
    """Test handling of network connection errors"""
    with patch("download_threads.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.download.side_effect = Exception("Network is unreachable")

        thread = DownloadThread(
            url=sample_video_urls[0],
            format_id="best",
            output_path=temp_dir,
            update_queue=update_queue,
        )

        thread.start()
        if thread.thread:
            thread.thread.join(timeout=10.0)

        assert mock_ydl.download.call_count > 1

        messages = get_queue_messages(update_queue)
        error_messages = [msg for msg in messages if msg.get("type") == "error"]
        assert len(error_messages) > 0


def test_http_403_forbidden_error(temp_dir, update_queue, sample_video_urls):
    """Test handling of HTTP 403 Forbidden errors"""
    with patch("download_threads.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        error_403 = Exception("HTTP Error 403: Forbidden")
        mock_ydl.download.side_effect = error_403

        thread = DownloadThread(
            url=sample_video_urls[0],
            format_id="best",
            output_path=temp_dir,
            update_queue=update_queue,
        )

        thread.start()
        if thread.thread:
            thread.thread.join(timeout=10.0)

        messages = get_queue_messages(update_queue)
        error_messages = [msg for msg in messages if msg.get("type") == "error"]

        auth_error_found = any(
            "403" in str(msg.get("text", ""))
            or "forbidden" in str(msg.get("text", "")).lower()
            for msg in error_messages
        )
        assert auth_error_found, "Expected 403/Forbidden error message not found"


def test_video_unavailable_error(temp_dir, update_queue, sample_video_urls):
    """Test handling of unavailable video errors"""
    with patch("download_threads.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_ydl.download.side_effect = Exception("Video unavailable")

        thread = DownloadThread(
            url=sample_video_urls[0],
            format_id="best",
            output_path=temp_dir,
            update_queue=update_queue,
        )

        thread.start()
        if thread.thread:
            thread.thread.join(timeout=10.0)

        messages = get_queue_messages(update_queue)
        error_messages = [msg for msg in messages if msg.get("type") == "error"]

        unavailable_error_found = any(
            "unavailable" in str(msg.get("text", "")).lower() for msg in error_messages
        )
        assert unavailable_error_found, "Expected 'unavailable' error message not found"


def test_cancellation_during_download(temp_dir, update_queue, sample_video_urls):
    """Test cancellation while download is in progress"""
    with patch("download_threads.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        def slow_failing_download(url_list):
            time.sleep(0.5)
            raise Exception("Slow network error")

        mock_ydl.download.side_effect = slow_failing_download

        thread = DownloadThread(
            url=sample_video_urls[0],
            format_id="best",
            output_path=temp_dir,
            update_queue=update_queue,
        )

        thread.start()

        time.sleep(0.2)
        thread.cancel()

        if thread.thread:
            thread.thread.join(timeout=5.0)

        assert thread.cancelled is True


def test_multiple_format_attempts_on_error(temp_dir, update_queue, sample_video_urls):
    """Test that multiple formats are attempted when one fails"""
    with patch("download_threads.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        # Fail multiple times to trigger fallback attempts
        mock_ydl.download.side_effect = [
            Exception("Format 1 failed"),
            Exception("Format 2 failed"),
            Exception("Format 3 failed"),
        ]

        thread = DownloadThread(
            url=sample_video_urls[0],
            format_id="best",
            output_path=temp_dir,
            update_queue=update_queue,
        )

        thread.start()
        if thread.thread:
            thread.thread.join(timeout=10.0)

        # Should have tried multiple formats (at least 2)
        assert mock_ydl.download.call_count >= 2


def test_error_message_queue_format(temp_dir, update_queue, sample_video_urls):
    """Test that error messages are properly formatted in the queue"""
    with patch("download_threads.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        test_error = "Test error message"
        mock_ydl.download.side_effect = Exception(test_error)

        thread = DownloadThread(
            url=sample_video_urls[0],
            format_id="best",
            output_path=temp_dir,
            update_queue=update_queue,
        )

        thread.start()
        if thread.thread:
            thread.thread.join(timeout=10.0)

        messages = get_queue_messages(update_queue)
        error_messages = [msg for msg in messages if msg.get("type") == "error"]

        assert len(error_messages) > 0
        for msg in error_messages:
            assert "type" in msg
            assert "text" in msg
            assert msg["type"] == "error"
