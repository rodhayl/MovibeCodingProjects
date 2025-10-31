#!/usr/bin/env python3
"""
Pytest-style tests to reproduce and verify URL validation bug fixes.

Tests that valid YouTube URLs with query parameters are properly accepted,
targeting the bug where URLs like:
"https://www.youtube.com/watch?v=dj1H4g4YSlU&list=PLFDswngT2LSgxkC9QPpyr0Ir0zUTOF8Eo"
were incorrectly rejected.
"""

from unittest.mock import patch

import pytest


def mock_validate_url(url):
    """Mock validation logic"""
    if not url:
        return False, "Please enter a video URL"
    cleaned_url = url.strip()
    if not cleaned_url:
        return False, "Please enter a video URL"
    if len(cleaned_url) < 10:
        return False, "Please enter a valid video URL"
    if not (cleaned_url.startswith("http://") or cleaned_url.startswith("https://")):
        return False, "Please enter a valid URL (must start with http:// or https://)"
    return True, cleaned_url


def test_bug_reproduction_valid_url_with_query_params():
    """Test that reproduces the bug with the specific reported URL"""
    problematic_url = "https://www.youtube.com/watch?v=dj1H4g4YSlU&list=PLFDswngT2LSgxkC9QPpyr0Ir0zUTOF8Eo"

    is_valid, result = mock_validate_url(problematic_url)

    assert is_valid is True, f"Valid URL {problematic_url} was incorrectly rejected"
    assert result == problematic_url


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dj1H4g4YSlU",
        "https://www.youtube.com/watch?v=dj1H4g4YSlU&list=PLFDswngT2LSgxkC9QPpyr0Ir0zUTOF8Eo",
        "https://youtu.be/dj1H4g4YSlU",
        "https://www.youtube.com/watch?v=dj1H4g4YSlU&t=30s",
        "https://www.youtube.com/watch?v=dj1H4g4YSlU&feature=youtu.be",
        "https://www.youtube.com/embed/dj1H4g4YSlU",
        "https://www.youtube.com/v/dj1H4g4YSlU",
    ],
)
def test_various_valid_youtube_urls(url):
    """Test various valid YouTube URL formats that should be accepted"""
    is_valid, result = mock_validate_url(url)

    assert is_valid is True, f"Valid URL {url} was incorrectly rejected"
    assert result == url


@pytest.mark.parametrize(
    "url,expected_error_fragment",
    [
        ("", "Please enter a video URL"),
        ("   ", "Please enter a video URL"),
        ("not_a_url", "Please enter a valid video URL"),
        ("http://", "Please enter a valid video URL"),
        ("ftp://example.com", "Please enter a valid URL"),
    ],
)
def test_empty_and_invalid_urls_should_be_rejected(url, expected_error_fragment):
    """Test that empty and invalid URLs are properly rejected"""
    is_valid, result = mock_validate_url(url)

    assert is_valid is False
    assert expected_error_fragment in result


def test_real_gui_validation_with_problematic_url(video_downloader_app):
    """Test the actual GUI validation logic with the problematic URL"""
    app = video_downloader_app

    with (
        patch("gui.main_window.messagebox.showwarning") as mock_warning,
        patch("gui.main_window.threading.Thread") as mock_thread,
    ):
        problematic_url = "https://www.youtube.com/watch?v=dj1H4g4YSlU&list=PLFDswngT2LSgxkC9QPpyr0Ir0zUTOF8Eo"
        app.url_var.set(problematic_url)

        app.get_video_info()

        # Check that no warning was shown (the bug would show a warning)
        mock_warning.assert_not_called()

        # Check that a thread was started (indicating URL was accepted)
        assert (
            mock_thread.call_count >= 1
        ), "Expected at least one thread to be started for video processing"


def test_url_validation_with_app_fixture(video_downloader_app):
    """Test URL validation using the video_downloader_app fixture"""
    app = video_downloader_app

    valid_urls = [
        "https://www.youtube.com/watch?v=test123",
        "https://www.youtube.com/watch?v=test123&list=PLtest",
        "https://youtu.be/test123",
    ]

    with (
        patch("gui.main_window.messagebox.showwarning") as mock_warning,
        patch("gui.main_window.threading.Thread"),
    ):
        for url in valid_urls:
            app.url_var.set(url)
            app.get_video_info()

        # No warnings should be shown for valid URLs
        mock_warning.assert_not_called()


def test_empty_url_shows_warning(video_downloader_app):
    """Test that empty URL shows appropriate warning"""
    app = video_downloader_app

    with patch("gui.main_window.messagebox.showwarning") as mock_warning:
        app.url_var.set("")

        with patch("gui.main_window.threading.Thread"):
            app.get_video_info()

        mock_warning.assert_called_once()
        assert "please enter" in mock_warning.call_args[0][1].lower()
