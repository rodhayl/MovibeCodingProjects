#!/usr/bin/env python3
"""
Pytest-style tests for video info extraction functionality.
Tests video info extraction, format parsing, and error handling without GUI components.
"""

import pytest


def mock_extract_video_info(url):
    """Mock video info extraction logic"""
    if "invalid" in url:
        raise Exception("Video not found")

    return {
        "title": "Test Video",
        "duration": 300,
        "formats": [
            {
                "format_id": "137",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "none",
                "height": 1080,
            },
            {
                "format_id": "140",
                "ext": "m4a",
                "vcodec": "none",
                "acodec": "mp4a",
                "abr": 128,
            },
            {
                "format_id": "18",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "mp4a",
                "height": 360,
            },
        ],
    }


def parse_formats(formats_data):
    """Parse formats into categories"""
    formats = ["best", "worst", "bestvideo+bestaudio"]
    video_formats = []
    audio_formats = []

    for fmt in formats_data:
        format_id = fmt.get("format_id", "")
        ext = fmt.get("ext", "")
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")
        height = fmt.get("height")
        abr = fmt.get("abr")

        if vcodec != "none" and acodec != "none":
            quality = f"{height}p" if height else "unknown"
            formats.append(f"{format_id} ({quality} {ext})")
        elif vcodec != "none":
            quality = f"{height}p" if height else "unknown"
            video_formats.append(f"{format_id} ({quality} {ext})")
        elif acodec != "none":
            bitrate = f"{abr}k" if abr else "unknown"
            audio_formats.append(f"{format_id} ({bitrate} {ext})")

    return formats, video_formats, audio_formats


@pytest.fixture
def test_urls():
    """Provide test URLs"""
    return {
        "valid": "https://www.youtube.com/watch?v=test123",
        "invalid": "https://www.youtube.com/watch?v=invalid",
    }


def test_video_info_extraction_success(test_urls):
    """Test successful video info extraction logic"""
    test_url = test_urls["valid"]

    video_info = mock_extract_video_info(test_url)

    assert "title" in video_info
    assert "duration" in video_info
    assert "formats" in video_info
    assert video_info["title"] == "Test Video"
    assert video_info["duration"] == 300
    assert isinstance(video_info["formats"], list)
    assert len(video_info["formats"]) > 0

    formats, video_formats, audio_formats = parse_formats(video_info["formats"])

    assert "best" in formats
    assert "137 (1080p mp4)" in video_formats
    assert "140 (128k m4a)" in audio_formats


def test_video_info_extraction_error(test_urls):
    """Test video info extraction error handling"""
    test_url = test_urls["invalid"]

    with pytest.raises(Exception) as exc_info:
        mock_extract_video_info(test_url)

    assert "Video not found" in str(exc_info.value)


def test_format_parsing():
    """Test format parsing logic"""
    test_formats = [
        {
            "format_id": "137",
            "ext": "mp4",
            "vcodec": "avc1",
            "acodec": "none",
            "height": 1080,
        },
        {
            "format_id": "140",
            "ext": "m4a",
            "vcodec": "none",
            "acodec": "mp4a",
            "abr": 128,
        },
    ]

    formats, video_formats, audio_formats = parse_formats(test_formats)

    assert "best" in formats
    assert len(video_formats) == 1
    assert len(audio_formats) == 1
    assert "137 (1080p mp4)" in video_formats
    assert "140 (128k m4a)" in audio_formats


def test_empty_formats_handling():
    """Test handling of empty formats list"""
    formats, video_formats, audio_formats = parse_formats([])

    assert "best" in formats
    assert "worst" in formats
    assert "bestvideo+bestaudio" in formats
    assert len(video_formats) == 0
    assert len(audio_formats) == 0


def test_format_with_missing_fields():
    """Test format parsing with missing fields"""
    test_formats = [
        {
            "format_id": "unknown",
            "ext": "mp4",
        }
    ]

    formats, video_formats, audio_formats = parse_formats(test_formats)

    # Should still include default formats
    assert "best" in formats
    # Format with missing vcodec/acodec should not be categorized
    assert len(video_formats) == 0
    assert len(audio_formats) == 0


def test_duration_formatting():
    """Test duration formatting logic"""

    def format_duration(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    assert format_duration(300) == "05:00"
    assert format_duration(3661) == "01:01:01"
    assert format_duration(90) == "01:30"
    assert format_duration(0) == "00:00"


def test_title_sanitization():
    """Test title sanitization for filenames"""

    def sanitize_title(title):
        invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
        for char in invalid_chars:
            title = title.replace(char, "_")
        return title

    assert sanitize_title("Normal Title") == "Normal Title"
    assert sanitize_title("Title: With Colon") == "Title_ With Colon"
    assert sanitize_title("Title/With/Slashes") == "Title_With_Slashes"
    assert sanitize_title("Title?Question*") == "Title_Question_"
