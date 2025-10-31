#!/usr/bin/env python3
"""
Pytest-style tests for playlist functionality in the YouTube Video Downloader.
Tests playlist URL detection, normalization, download scenarios, error handling, and progress tracking.
"""

import os
import queue
import shutil
import tempfile
from unittest.mock import Mock, patch

import pytest

from download_threads import DownloadThread
from utils import is_playlist_url, normalize_playlist_url


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/playlist?list=PL123456789",
        "https://www.youtube.com/watch?v=abc123&list=PL123456789",
        "https://www.youtube.com/watch?list=PL123456789&v=abc123",
        "https://www.youtube.com/user/username/playlists",
        "https://www.youtube.com/channel/UC123456789/playlists",
    ],
)
def test_playlist_url_detection(url):
    """Test playlist URL detection"""
    assert (
        is_playlist_url(url) is True
    ), f"Expected {url} to be identified as a playlist URL"


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=abc123",
        "https://www.vimeo.com/123456",
        "https://example.com/video.mp4",
    ],
)
def test_non_playlist_url_detection(url):
    """Test that non-playlist URLs are correctly identified"""
    assert (
        is_playlist_url(url) is False
    ), f"Expected {url} to NOT be identified as a playlist URL"


@pytest.mark.parametrize(
    "original,expected",
    [
        (
            "https://www.youtube.com/watch?v=abc123&list=PL123456789",
            "https://www.youtube.com/playlist?list=PL123456789",
        ),
        (
            "https://www.youtube.com/watch?list=PL123456789&v=abc123",
            "https://www.youtube.com/playlist?list=PL123456789",
        ),
        (
            "https://www.youtube.com/playlist?list=PL123456789",
            "https://www.youtube.com/playlist?list=PL123456789",
        ),
        (
            "https://www.youtube.com/watch?v=aLYrV61rJG4&list=PLIivdWyY5sqLXR1eSkiM5bE6pFlXC-OSs&index=5",
            "https://www.youtube.com/playlist?list=PLIivdWyY5sqLXR1eSkiM5bE6pFlXC-OSs",
        ),
        (
            "https://www.youtube.com/watch?list=PL123456789&v=abc123&index=10&t=100",
            "https://www.youtube.com/playlist?list=PL123456789",
        ),
        (
            "https://www.youtube.com/playlist?list=PL123456789&index=5",
            "https://www.youtube.com/playlist?list=PL123456789",
        ),
        (
            "https://www.youtube.com/watch?v=test&list=PLtest&index=3&t=100&feature=shared",
            "https://www.youtube.com/playlist?list=PLtest",
        ),
    ],
)
def test_url_normalization(original, expected):
    """Test URL normalization"""
    result = normalize_playlist_url(original)
    assert (
        result == expected
    ), f"Normalization failed for {original}. Expected: {expected}, Got: {result}"


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


def test_download_thread_initialization(temp_dir, update_queue, sample_video_urls):
    """Test DownloadThread initialization with valid parameters"""
    thread = DownloadThread(
        url=sample_video_urls[0],
        format_id="best",
        output_path=temp_dir,
        update_queue=update_queue,
    )

    assert thread is not None
    assert thread.url == sample_video_urls[0]
    assert thread.format_id == "best"
    assert thread.output_path == temp_dir
    assert thread.update_queue == update_queue
    assert thread.cancelled is False


def test_download_thread_cancel(temp_dir, update_queue, sample_video_urls):
    """Test download thread cancellation functionality"""
    thread = DownloadThread(
        url=sample_video_urls[0],
        format_id="best",
        output_path=temp_dir,
        update_queue=update_queue,
    )

    assert thread.cancelled is False
    thread.cancel()
    assert thread.cancelled is True


def test_successful_download_scenario(temp_dir, update_queue, sample_video_urls):
    """Test successful download scenario with progress tracking"""
    with patch("download_threads.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.download.return_value = None

        thread = DownloadThread(
            url=sample_video_urls[0],
            format_id="best",
            output_path=temp_dir,
            update_queue=update_queue,
        )

        thread.start()
        if thread.thread:
            thread.thread.join(timeout=5.0)

        assert mock_ydl.download.called

        messages = []
        while not update_queue.empty():
            try:
                messages.append(update_queue.get_nowait())
            except queue.Empty:
                break

        assert len(messages) > 0
