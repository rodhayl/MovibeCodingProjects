#!/usr/bin/env python3
"""
Comprehensive Format Availability Tests

Tests that all video and audio formats are properly:
1. Detected and extracted from YouTube
2. Categorized correctly (video-only, audio-only, combined)
3. Available for download in single videos
4. Available for download in playlists
5. Can be combined (manual video+audio selection)

These tests use real YouTube videos with fresh cookies to verify the complete
format handling pipeline works end-to-end.

Run with: pytest tests/test_format_availability.py -v -s
"""

import os
import queue
import shutil
import tempfile
import time
from pathlib import Path

import pytest
import yt_dlp

from cookie_manager import get_cookie_manager
from download_threads import DownloadThread
from playlist_downloader import PlaylistVideoDownloader


# Skip all tests if cookie file doesn't exist
COOKIE_FILE = Path(__file__).parent.parent / "youtube.com_cookies.txt"
pytestmark = pytest.mark.skipif(
    not COOKIE_FILE.exists(),
    reason="youtube.com_cookies.txt not found - required for format tests"
)


@pytest.fixture
def temp_download_dir():
    """Create temporary directory for downloads"""
    temp_dir = tempfile.mkdtemp(prefix="format_test_")
    yield temp_dir
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up {temp_dir}: {e}")


@pytest.fixture
def update_queue():
    """Create queue for download updates"""
    return queue.Queue()


@pytest.fixture
def loaded_cookies():
    """Ensure cookies are loaded before each test"""
    cookie_manager = get_cookie_manager()
    success = cookie_manager.import_cookies_from_file(str(COOKIE_FILE))
    assert success, "Failed to load cookies"
    return cookie_manager


class TestFormatExtraction:
    """Test that all format types are properly extracted from YouTube videos"""

    def test_extract_all_format_types(self, loaded_cookies):
        """Verify we can extract video-only, audio-only, and combined formats"""
        # Use a known video with multiple formats
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }
        
        # Add cookies
        from utils import setup_ytdlp_cookies
        setup_ytdlp_cookies(ydl_opts, loaded_cookies, test_url, None, "test")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
        
        assert info is not None, "Should extract video info"
        assert "formats" in info, "Should have formats"
        
        formats = info["formats"]
        assert len(formats) > 0, "Should have at least one format"
        
        # Categorize formats
        video_only = []
        audio_only = []
        combined = []
        
        for fmt in formats:
            vcodec = fmt.get("vcodec", "none")
            acodec = fmt.get("acodec", "none")
            format_id = fmt.get("format_id", "")
            
            if vcodec != "none" and acodec != "none":
                combined.append(format_id)
            elif vcodec != "none":
                video_only.append(format_id)
            elif acodec != "none":
                audio_only.append(format_id)
        
        # Verify we have all three types
        assert len(video_only) > 0, f"Should have video-only formats. Found {len(formats)} total formats"
        assert len(audio_only) > 0, f"Should have audio-only formats. Found {len(formats)} total formats"
        assert len(combined) > 0, f"Should have combined formats. Found {len(formats)} total formats"
        
        print(f"\n[OK] Found {len(video_only)} video-only, {len(audio_only)} audio-only, {len(combined)} combined formats")
        print(f"  Video-only formats (sample): {video_only[:5]}")
        print(f"  Audio-only formats (sample): {audio_only[:5]}")
        print(f"  Combined formats (sample): {combined[:5]}")

    def test_extract_format_details(self, loaded_cookies):
        """Verify format metadata is properly extracted"""
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        
        ydl_opts = {"quiet": True, "no_warnings": True}
        from utils import setup_ytdlp_cookies
        setup_ytdlp_cookies(ydl_opts, loaded_cookies, test_url, None, "test")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
        
        # Check first format has expected fields
        first_format = info["formats"][0]
        assert "format_id" in first_format, "Format should have format_id"
        assert "ext" in first_format, "Format should have ext"
        
        # Find a video format and check it has height
        video_format = None
        for fmt in info["formats"]:
            if fmt.get("vcodec", "none") != "none":
                video_format = fmt
                break
        
        assert video_format is not None, "Should find at least one video format"
        # Height might not always be present for all formats, so just check it's there or None
        assert "height" in video_format or "width" in video_format, "Video format should have dimensions"
        
        print(f"\n[OK] Format metadata properly extracted")
        print(f"  Sample format: {video_format.get('format_id')} - {video_format.get('height')}p {video_format.get('ext')}")


class TestSingleVideoFormatDownload:
    """Test downloading with specific formats in single video mode"""

    def test_download_with_specific_video_and_audio(self, temp_download_dir, update_queue, loaded_cookies):
        """Test downloading with manually selected video+audio formats"""
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        
        # First, get available formats
        ydl_opts = {"quiet": True, "no_warnings": True}
        from utils import setup_ytdlp_cookies
        setup_ytdlp_cookies(ydl_opts, loaded_cookies, test_url, None, "test")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
        
        # Find suitable video and audio formats
        video_format_id = None
        audio_format_id = None
        
        for fmt in info["formats"]:
            vcodec = fmt.get("vcodec", "none")
            acodec = fmt.get("acodec", "none")
            format_id = fmt.get("format_id", "")
            
            # Get a mid-quality video format (prefer 360p or 480p)
            if vcodec != "none" and acodec == "none" and video_format_id is None:
                height = fmt.get("height", 0)
                if 200 <= height <= 480:
                    video_format_id = format_id
            
            # Get an audio format
            if acodec != "none" and vcodec == "none" and audio_format_id is None:
                audio_format_id = format_id
            
            if video_format_id and audio_format_id:
                break
        
        assert video_format_id is not None, "Should find a video format"
        assert audio_format_id is not None, "Should find an audio format"
        
        print(f"\n[INFO] Using video format: {video_format_id}, audio format: {audio_format_id}")
        
        # Create download with manual format selection
        thread = DownloadThread(
            url=test_url,
            format_id=None,  # Not used when video_format_id and audio_format_id are set
            output_path=temp_download_dir,
            update_queue=update_queue,
            video_format_id=video_format_id,
            audio_format_id=audio_format_id
        )
        
        thread.start()
        if thread.thread:
            thread.thread.join(timeout=60.0)
        
        # Check results
        messages = []
        while not update_queue.empty():
            try:
                messages.append(update_queue.get_nowait())
            except queue.Empty:
                break
        
        finished = [m for m in messages if m.get("type") == "finished"]
        errors = [m for m in messages if m.get("type") == "error"]
        
        if errors:
            print(f"\n[ERROR] Download errors: {errors}")
        
        assert len(finished) > 0, f"Should complete download. Messages: {messages}"
        
        # Verify file was created
        video_files = list(Path(temp_download_dir).glob("*.*"))
        assert len(video_files) > 0, "Should create video file"
        
        file_size = video_files[0].stat().st_size
        print(f"[OK] Downloaded with manual format selection: {video_files[0].name} ({file_size / 1024:.1f} KB)")

    def test_download_video_only_format(self, temp_download_dir, update_queue, loaded_cookies):
        """Test downloading a video-only format (no audio)"""
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        
        # Get a video-only format
        ydl_opts = {"quiet": True, "no_warnings": True}
        from utils import setup_ytdlp_cookies
        setup_ytdlp_cookies(ydl_opts, loaded_cookies, test_url, None, "test")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
        
        video_only_format = None
        for fmt in info["formats"]:
            if fmt.get("vcodec", "none") != "none" and fmt.get("acodec", "none") == "none":
                video_only_format = fmt.get("format_id")
                break
        
        assert video_only_format is not None, "Should find video-only format"
        
        print(f"\n[INFO] Testing video-only format: {video_only_format}")
        
        thread = DownloadThread(
            url=test_url,
            format_id=video_only_format,
            output_path=temp_download_dir,
            update_queue=update_queue
        )
        
        thread.start()
        if thread.thread:
            thread.thread.join(timeout=60.0)
        
        # Check for completion
        messages = []
        while not update_queue.empty():
            try:
                messages.append(update_queue.get_nowait())
            except queue.Empty:
                break
        
        finished = [m for m in messages if m.get("type") == "finished"]
        assert len(finished) > 0, "Should complete download"
        
        print(f"[OK] Video-only format downloaded successfully")

    def test_download_audio_only_format(self, temp_download_dir, update_queue, loaded_cookies):
        """Test downloading an audio-only format"""
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        
        # Get an audio-only format
        ydl_opts = {"quiet": True, "no_warnings": True}
        from utils import setup_ytdlp_cookies
        setup_ytdlp_cookies(ydl_opts, loaded_cookies, test_url, None, "test")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
        
        audio_only_format = None
        for fmt in info["formats"]:
            if fmt.get("acodec", "none") != "none" and fmt.get("vcodec", "none") == "none":
                audio_only_format = fmt.get("format_id")
                break
        
        assert audio_only_format is not None, "Should find audio-only format"
        
        print(f"\n[INFO] Testing audio-only format: {audio_only_format}")
        
        thread = DownloadThread(
            url=test_url,
            format_id=audio_only_format,
            output_path=temp_download_dir,
            update_queue=update_queue
        )
        
        thread.start()
        if thread.thread:
            thread.thread.join(timeout=60.0)
        
        # Check for completion
        messages = []
        while not update_queue.empty():
            try:
                messages.append(update_queue.get_nowait())
            except queue.Empty:
                break
        
        finished = [m for m in messages if m.get("type") == "finished"]
        assert len(finished) > 0, "Should complete download"
        
        print(f"[OK] Audio-only format downloaded successfully")


class TestPlaylistFormatDownload:
    """Test that playlist video downloads also support all format types"""

    def test_playlist_video_with_manual_formats(self, temp_download_dir, update_queue, loaded_cookies):
        """Test PlaylistVideoDownloader with manual video+audio format selection"""
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        
        # Get available formats
        ydl_opts = {"quiet": True, "no_warnings": True}
        from utils import setup_ytdlp_cookies
        setup_ytdlp_cookies(ydl_opts, loaded_cookies, test_url, None, "test")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
        
        # Find video and audio formats
        video_format_id = None
        audio_format_id = None
        
        for fmt in info["formats"]:
            vcodec = fmt.get("vcodec", "none")
            acodec = fmt.get("acodec", "none")
            format_id = fmt.get("format_id", "")
            
            if vcodec != "none" and acodec == "none" and video_format_id is None:
                height = fmt.get("height", 0)
                if 200 <= height <= 480:
                    video_format_id = format_id
            
            if acodec != "none" and vcodec == "none" and audio_format_id is None:
                audio_format_id = format_id
            
            if video_format_id and audio_format_id:
                break
        
        assert video_format_id is not None, "Should find video format"
        assert audio_format_id is not None, "Should find audio format"
        
        print(f"\n[INFO] Testing playlist video downloader with video: {video_format_id}, audio: {audio_format_id}")
        
        # Create PlaylistVideoDownloader with manual formats
        downloader = PlaylistVideoDownloader(
            url=test_url,
            format_id=None,  # Not used when manual formats specified
            output_path=temp_download_dir,
            update_queue=update_queue,
            video_index=1,
            total_videos=1,
            video_format_id=video_format_id,
            audio_format_id=audio_format_id
        )
        
        downloader.start()
        if downloader.thread:
            downloader.thread.join(timeout=60.0)
        
        # Check results
        messages = []
        while not update_queue.empty():
            try:
                messages.append(update_queue.get_nowait())
            except queue.Empty:
                break
        
        # Look for finished messages
        finished = [m for m in messages if m.get("type") in ["playlist_video_finished", "finished"]]
        errors = [m for m in messages if m.get("type") in ["playlist_video_error", "error"]]
        
        if errors:
            print(f"\n[ERROR] Playlist download errors: {errors}")
        
        assert len(finished) > 0 or downloader.success, f"Should complete download. Success: {downloader.success}, Messages: {messages}"
        
        # Verify file was created
        video_files = list(Path(temp_download_dir).glob("*.*"))
        assert len(video_files) > 0, "Should create video file"
        
        print(f"[OK] Playlist video downloaded with manual formats: {video_files[0].name}")


class TestFormatMergingRequirements:
    """Test FFmpeg requirements for format merging"""

    def test_ffmpeg_availability_check(self):
        """Verify FFmpeg detection works"""
        from utils import check_ffmpeg
        
        ffmpeg_available = check_ffmpeg()
        
        # We should be able to detect FFmpeg (either bundled or system)
        # This is informational - don't fail the test
        print(f"\n[INFO] FFmpeg available: {ffmpeg_available}")
        
        if ffmpeg_available:
            from utils import get_bundled_ffmpeg_path
            ffmpeg_path = get_bundled_ffmpeg_path()
            print(f"[INFO] FFmpeg path: {ffmpeg_path}")
        else:
            print("[WARNING] FFmpeg not available - format merging will be limited")


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
