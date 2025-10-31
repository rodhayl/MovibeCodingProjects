#!/usr/bin/env python3
"""
Pytest-style tests for detecting download failures that are incorrectly reported as successful.
Specifically tests the truncated YouTube ID issue where yt-dlp fails silently.
"""

import os
import queue
import shutil
import tempfile
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
def truncated_urls():
    """Provide truncated YouTube URLs that cause silent failures"""
    return [
        "https://www.youtube.com/watch?v=I005",
        "https://www.youtube.com/watch?v=I00A",
        "https://www.youtube.com/watch?v=ABC",
        "https://www.youtube.com/watch?v=12",
    ]


@pytest.fixture
def valid_url():
    """Provide valid YouTube URL"""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def get_queue_messages(queue_obj):
    """Helper to get all messages from queue"""
    messages = []
    while not queue_obj.empty():
        try:
            messages.append(queue_obj.get_nowait())
        except queue.Empty:
            break
    return messages


def count_files_in_directory(directory):
    """Count files in directory"""
    if not os.path.exists(directory):
        return 0
    return len(
        [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    )


@pytest.mark.parametrize(
    "truncated_url",
    [
        "https://www.youtube.com/watch?v=I005",
        "https://www.youtube.com/watch?v=I00A",
        "https://www.youtube.com/watch?v=ABC",
        "https://www.youtube.com/watch?v=12",
    ],
)
def test_truncated_youtube_id_detection(temp_dir, update_queue, truncated_url):
    """Test that truncated YouTube IDs are properly detected as failures"""
    files_before = count_files_in_directory(temp_dir)

    thread = DownloadThread(
        url=truncated_url,
        format_id="best",
        output_path=temp_dir,
        update_queue=update_queue,
    )

    thread.start()
    if thread.thread:
        thread.thread.join(timeout=15.0)

    files_after = count_files_in_directory(temp_dir)
    messages = get_queue_messages(update_queue)

    files_created = files_after > files_before

    finished_messages = [msg for msg in messages if msg.get("type") == "finished"]
    error_messages = [msg for msg in messages if msg.get("type") == "error"]

    if not files_created:
        assert (
            len(finished_messages) == 0
        ), f"Download incorrectly reported as finished for {truncated_url} when no files were created"
        assert (
            len(error_messages) > 0
        ), f"Download should report error for {truncated_url} when no files were created"
    else:
        assert (
            len(finished_messages) > 0
        ), f"Download should report success for {truncated_url} when files were created"


def test_yt_dlp_silent_failure_simulation(temp_dir, update_queue, truncated_urls):
    """Test simulation of yt-dlp completing without error but not creating files"""
    with patch("download_threads.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        # Simulate yt-dlp completing without error but not creating files
        mock_ydl.download.return_value = None

        files_before = count_files_in_directory(temp_dir)

        thread = DownloadThread(
            url=truncated_urls[0],
            format_id="best",
            output_path=temp_dir,
            update_queue=update_queue,
        )

        thread.start()
        if thread.thread:
            thread.thread.join(timeout=10.0)

        files_after = count_files_in_directory(temp_dir)
        messages = get_queue_messages(update_queue)

        files_created = files_after > files_before

        finished_messages = [msg for msg in messages if msg.get("type") == "finished"]
        error_messages = [msg for msg in messages if msg.get("type") == "error"]

        if not files_created:
            assert (
                len(finished_messages) == 0
            ), "Download incorrectly reported as finished when no files were created"
            assert (
                len(error_messages) > 0
            ), "Download should report error when no files were created"


def test_successful_download_detection(temp_dir, update_queue, valid_url):
    """Test that legitimate successful downloads are still reported correctly"""
    with patch("download_threads.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        def create_test_file(url_list):
            test_file = os.path.join(temp_dir, "test_video.mp4")
            with open(test_file, "w") as f:
                f.write("test video content")

        mock_ydl.download.side_effect = create_test_file

        files_before = count_files_in_directory(temp_dir)

        thread = DownloadThread(
            url=valid_url,
            format_id="best",
            output_path=temp_dir,
            update_queue=update_queue,
        )

        thread.start()
        if thread.thread:
            thread.thread.join(timeout=10.0)

        files_after = count_files_in_directory(temp_dir)
        messages = get_queue_messages(update_queue)

        files_created = files_after > files_before

        finished_messages = [msg for msg in messages if msg.get("type") == "finished"]
        error_messages = [msg for msg in messages if msg.get("type") == "error"]

        assert files_created is True, "Test file should have been created"
        assert (
            len(finished_messages) > 0
        ), "Download should report success when files were created"
        assert (
            len(error_messages) == 0
        ), "No errors should be reported for successful download"
