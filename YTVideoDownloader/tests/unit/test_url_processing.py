#!/usr/bin/env python3
"""
Logic-only tests for URL processing functionality

Tests URL validation, cleaning, normalization, and playlist detection
without any GUI creation or user interaction.
"""

import os
import sys
import unittest


# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from utils import clean_url_for_video_info, is_playlist_url, normalize_playlist_url


class TestURLProcessing(unittest.TestCase):
    """Test URL processing logic without GUI components"""

    def test_playlist_url_detection(self):
        """Test playlist URL detection logic"""
        # Test cases for playlist URLs
        playlist_urls = [
            "https://www.youtube.com/playlist?list=PL123456789",
            "https://www.youtube.com/watch?v=abc123&list=PL123456789",
            "https://www.youtube.com/watch?list=PL123456789&v=abc123",
            "https://www.youtube.com/user/username/playlists",
            "https://www.youtube.com/channel/UC123456789/playlists",
            "https://youtube.com/playlist?list=PLrAXtmRdnEQy4TyTh9EE-4CX6v79UADVl",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmRdnEQy4TyTh9EE-4CX6v79UADVl&index=1",
        ]

        # Test cases for non-playlist URLs
        non_playlist_urls = [
            "https://www.youtube.com/watch?v=abc123",
            "https://www.vimeo.com/123456",
            "https://example.com/video.mp4",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.dailymotion.com/video/x123456",
        ]

        # Test playlist URL detection
        for url in playlist_urls:
            with self.subTest(url=url):
                result = is_playlist_url(url)
                self.assertTrue(
                    result, f"Expected {url} to be identified as playlist URL"
                )

        # Test non-playlist URL detection
        for url in non_playlist_urls:
            with self.subTest(url=url):
                result = is_playlist_url(url)
                self.assertFalse(
                    result, f"Expected {url} to NOT be identified as playlist URL"
                )

    def test_playlist_url_normalization(self):
        """Test playlist URL normalization logic"""
        test_cases = [
            # (input_url, expected_output)
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
        ]

        for input_url, expected in test_cases:
            with self.subTest(input_url=input_url):
                result = normalize_playlist_url(input_url)
                self.assertEqual(
                    result,
                    expected,
                    f"Normalization failed for {input_url}. Expected: {expected}, Got: {result}",
                )

    def test_url_cleaning_for_video_info(self):
        """Test URL cleaning logic for video info extraction"""
        test_cases = [
            # (input_url, expected_output)
            (
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ),
            (
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ),
            (
                "https://youtu.be/dQw4w9WgXcQ",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ),
            (
                "https://www.youtube.com/embed/dQw4w9WgXcQ",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ),
            (
                "https://www.youtube.com/v/dQw4w9WgXcQ",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ),
            (
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s&feature=youtu.be",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ),
        ]

        for input_url, expected in test_cases:
            with self.subTest(input_url=input_url):
                result = clean_url_for_video_info(input_url)
                self.assertEqual(
                    result,
                    expected,
                    f"URL cleaning failed for {input_url}. Expected: {expected}, Got: {result}",
                )

    def test_url_validation_edge_cases(self):
        """Test URL validation with edge cases"""
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "not_a_url",  # Invalid URL format
            "http://",  # Incomplete URL
            "https://",  # Incomplete URL
            "ftp://example.com/file.mp4",  # Non-HTTP protocol
        ]

        for url in edge_cases:
            with self.subTest(url=repr(url)):
                # Test that functions handle edge cases gracefully
                try:
                    is_playlist_result = is_playlist_url(url)
                    self.assertIsInstance(is_playlist_result, bool)

                    normalize_result = normalize_playlist_url(url)
                    self.assertIsInstance(normalize_result, str)

                    clean_result = clean_url_for_video_info(url)
                    self.assertIsInstance(clean_result, str)
                except Exception as e:
                    self.fail(f"URL processing failed for edge case {repr(url)}: {e}")


if __name__ == "__main__":
    unittest.main()
