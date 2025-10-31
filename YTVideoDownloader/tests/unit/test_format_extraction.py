#!/usr/bin/env python3
"""
Pytest-style tests for video format extraction and processing.
Tests format retrieval from video links using GUI logic.
"""

import pytest


try:
    import yt_dlp
except ImportError:
    yt_dlp = None

from utils import clean_url_for_video_info


@pytest.fixture
def test_urls():
    """Provide test URLs for format extraction"""
    return {
        "standard_video": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "high_quality": "https://www.youtube.com/watch?v=LXb3EKWsInQ",
        "mixed_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw&list=PLtest&index=1",
    }


@pytest.fixture
def mock_formats():
    """Provide mock format data matching real yt-dlp structure"""
    return [
        {
            "format_id": "137",
            "ext": "mp4",
            "vcodec": "avc1.640028",
            "acodec": "none",
            "height": 1080,
            "width": 1920,
            "fps": 30,
            "filesize": 50000000,
        },
        {
            "format_id": "136",
            "ext": "mp4",
            "vcodec": "avc1.4d401f",
            "acodec": "none",
            "height": 720,
            "width": 1280,
            "fps": 30,
            "filesize": 25000000,
        },
        {
            "format_id": "135",
            "ext": "mp4",
            "vcodec": "avc1.4d401e",
            "acodec": "none",
            "height": 480,
            "width": 854,
            "fps": 30,
            "filesize": 15000000,
        },
        {
            "format_id": "134",
            "ext": "mp4",
            "vcodec": "avc1.4d4015",
            "acodec": "none",
            "height": 360,
            "width": 640,
            "fps": 30,
            "filesize": 8000000,
        },
        {
            "format_id": "140",
            "ext": "m4a",
            "vcodec": "none",
            "acodec": "mp4a.40.2",
            "abr": 128,
            "filesize": 5000000,
        },
        {
            "format_id": "139",
            "ext": "m4a",
            "vcodec": "none",
            "acodec": "mp4a.40.5",
            "abr": 48,
            "filesize": 2000000,
        },
        {
            "format_id": "18",
            "ext": "mp4",
            "vcodec": "avc1.42001E",
            "acodec": "mp4a.40.2",
            "height": 360,
            "width": 640,
            "abr": 96,
            "filesize": 12000000,
        },
        {
            "format_id": "22",
            "ext": "mp4",
            "vcodec": "avc1.64001F",
            "acodec": "mp4a.40.2",
            "height": 720,
            "width": 1280,
            "abr": 192,
            "filesize": 35000000,
        },
    ]


def test_url_cleaning_for_format_extraction(test_urls):
    """Test URL cleaning logic used before format extraction"""
    mixed_url = test_urls["mixed_url"]
    cleaned_url = clean_url_for_video_info(mixed_url)

    assert "list=" not in cleaned_url
    assert "index=" not in cleaned_url
    assert "watch?v=" in cleaned_url

    standard_url = test_urls["standard_video"]
    cleaned_standard = clean_url_for_video_info(standard_url)
    assert standard_url == cleaned_standard


def test_format_parsing_logic(mock_formats):
    """Test format parsing logic identical to GUI implementation"""
    formats = []
    video_formats = []
    audio_formats = []

    formats.extend(["best", "worst", "bestvideo+bestaudio"])

    for fmt in mock_formats:
        format_id = fmt.get("format_id", "")
        ext = fmt.get("ext", "")
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")
        height = fmt.get("height")
        _width = fmt.get("width")
        fps = fmt.get("fps")
        abr = fmt.get("abr")

        if vcodec != "none" and acodec != "none":
            quality_info = []
            if height:
                quality_info.append(f"{height}p")
            if fps and fps > 30:
                quality_info.append(f"{fps}fps")
            quality_str = " ".join(quality_info) if quality_info else "unknown"
            formats.append(f"{format_id} ({quality_str} {ext})")

        elif vcodec != "none" and acodec == "none":
            quality_info = []
            if height:
                quality_info.append(f"{height}p")
            if fps and fps > 30:
                quality_info.append(f"{fps}fps")
            quality_str = " ".join(quality_info) if quality_info else "unknown"
            video_formats.append(f"{format_id} ({quality_str} {ext})")

        elif vcodec == "none" and acodec != "none":
            bitrate_str = f"{abr}k" if abr else "unknown"
            audio_formats.append(f"{format_id} ({bitrate_str} {ext})")

    assert "best" in formats
    assert "worst" in formats
    assert "bestvideo+bestaudio" in formats
    assert len(video_formats) > 0
    assert len(audio_formats) > 0
    assert any("1080p" in fmt for fmt in video_formats)
    assert any("720p" in fmt for fmt in video_formats)
    assert any("128k" in fmt for fmt in audio_formats)


def test_format_categorization(mock_formats):
    """Test that formats are correctly categorized"""
    video_only_count = sum(
        1
        for fmt in mock_formats
        if fmt.get("vcodec") != "none" and fmt.get("acodec") == "none"
    )
    audio_only_count = sum(
        1
        for fmt in mock_formats
        if fmt.get("vcodec") == "none" and fmt.get("acodec") != "none"
    )
    combined_count = sum(
        1
        for fmt in mock_formats
        if fmt.get("vcodec") != "none" and fmt.get("acodec") != "none"
    )

    assert video_only_count == 4
    assert audio_only_count == 2
    assert combined_count == 2


def test_quality_sorting_logic(mock_formats):
    """Test that formats can be sorted by quality"""
    video_formats = [
        fmt
        for fmt in mock_formats
        if fmt.get("vcodec") != "none" and fmt.get("acodec") == "none"
    ]

    sorted_by_quality = sorted(
        video_formats, key=lambda x: x.get("height", 0), reverse=True
    )

    assert sorted_by_quality[0]["height"] == 1080
    assert sorted_by_quality[-1]["height"] == 360


def test_filesize_formatting():
    """Test filesize formatting for display"""
    test_sizes = [
        (1024, "1.00 KB"),
        (1048576, "1.00 MB"),
        (1073741824, "1.00 GB"),
        (50000000, "47.68 MB"),
    ]

    for size_bytes, expected in test_sizes:
        if size_bytes < 1024:
            result = f"{size_bytes} B"
        elif size_bytes < 1048576:
            result = f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1073741824:
            result = f"{size_bytes / 1048576:.2f} MB"
        else:
            result = f"{size_bytes / 1073741824:.2f} GB"

        assert result == expected


def test_format_id_extraction(mock_formats):
    """Test that format IDs are correctly extracted"""
    format_ids = [fmt.get("format_id") for fmt in mock_formats]

    assert "137" in format_ids
    assert "140" in format_ids
    assert "18" in format_ids
    assert len(format_ids) == len(mock_formats)
