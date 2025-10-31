#!/usr/bin/env python3
"""
Random Format Combination Tests

Tests that ANY video format can be combined with ANY audio format and downloaded
successfully for both single videos and playlists. This verifies the manual
format selection feature works for all possible combinations.

Test Playlist: https://www.youtube.com/watch?v=LXeSNISmTgQ&list=PLeCPCQfHe9emt_AIVU_QBdxnQpVMZV6hg

Run with: pytest tests/test_random_format_combinations.py -v -s
"""

import os
import queue
import random
import shutil
import tempfile
from pathlib import Path

import pytest
import yt_dlp

from cookie_manager import get_cookie_manager
from download_threads import DownloadThread
from playlist_downloader import PlaylistVideoDownloader
from utils import normalize_playlist_url


# Skip all tests if cookie file doesn't exist
COOKIE_FILE = Path(__file__).parent.parent / "youtube.com_cookies.txt"
pytestmark = pytest.mark.skipif(
    not COOKIE_FILE.exists(),
    reason="youtube.com_cookies.txt not found"
)

# Test URLs
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=LXeSNISmTgQ"
TEST_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLeCPCQfHe9emt_AIVU_QBdxnQpVMZV6hg"


@pytest.fixture
def temp_download_dir():
    """Create temporary directory for downloads"""
    temp_dir = tempfile.mkdtemp(prefix="random_fmt_")
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
    """Ensure cookies are loaded"""
    cookie_manager = get_cookie_manager()
    success = cookie_manager.import_cookies_from_file(str(COOKIE_FILE))
    assert success, "Failed to load cookies"
    return cookie_manager


@pytest.fixture(scope="module")
def available_formats():
    """Extract all available formats once for the module"""
    cookie_manager = get_cookie_manager()
    cookie_manager.import_cookies_from_file(str(COOKIE_FILE))
    
    ydl_opts = {"quiet": True, "no_warnings": True}
    from utils import setup_ytdlp_cookies
    setup_ytdlp_cookies(ydl_opts, cookie_manager, TEST_VIDEO_URL, None, "test")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(TEST_VIDEO_URL, download=False)
    
    video_formats = []
    audio_formats = []
    
    for fmt in info["formats"]:
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")
        format_id = fmt.get("format_id", "")
        height = fmt.get("height", 0)
        abr = fmt.get("abr", 0)
        ext = fmt.get("ext", "")
        
        if vcodec != "none" and acodec == "none":
            # Video-only format
            video_formats.append({
                "id": format_id,
                "height": height,
                "ext": ext,
                "description": f"{height}p {ext}" if height else f"video {ext}"
            })
        elif acodec != "none" and vcodec == "none":
            # Audio-only format
            audio_formats.append({
                "id": format_id,
                "abr": abr,
                "ext": ext,
                "description": f"{int(abr)}k {ext}" if abr else f"audio {ext}"
            })
    
    return {
        "video": video_formats,
        "audio": audio_formats,
        "video_url": TEST_VIDEO_URL
    }


class TestSingleVideoRandomCombinations:
    """Test random video+audio format combinations for single videos"""

    def test_random_combination_1(self, temp_download_dir, update_queue, loaded_cookies, available_formats):
        """Test random video+audio combination #1"""
        self._test_random_combination(temp_download_dir, update_queue, available_formats, seed=1)

    def test_random_combination_2(self, temp_download_dir, update_queue, loaded_cookies, available_formats):
        """Test random video+audio combination #2"""
        self._test_random_combination(temp_download_dir, update_queue, available_formats, seed=2)

    def test_random_combination_3(self, temp_download_dir, update_queue, loaded_cookies, available_formats):
        """Test random video+audio combination #3"""
        self._test_random_combination(temp_download_dir, update_queue, available_formats, seed=3)

    def test_random_combination_4(self, temp_download_dir, update_queue, loaded_cookies, available_formats):
        """Test random video+audio combination #4"""
        self._test_random_combination(temp_download_dir, update_queue, available_formats, seed=4)

    def test_random_combination_5(self, temp_download_dir, update_queue, loaded_cookies, available_formats):
        """Test random video+audio combination #5"""
        self._test_random_combination(temp_download_dir, update_queue, available_formats, seed=5)

    def _test_random_combination(self, temp_download_dir, update_queue, available_formats, seed):
        """Helper method to test a random video+audio combination"""
        random.seed(seed)  # Reproducible randomness
        
        video_formats = available_formats["video"]
        audio_formats = available_formats["audio"]
        video_url = available_formats["video_url"]
        
        # Select random video and audio format
        video_fmt = random.choice(video_formats)
        audio_fmt = random.choice(audio_formats)
        
        video_id = video_fmt["id"]
        audio_id = audio_fmt["id"]
        
        print(f"\n[TEST] Combination #{seed}:")
        print(f"       Video: {video_id} ({video_fmt['description']})")
        print(f"       Audio: {audio_id} ({audio_fmt['description']})")
        
        # Create download thread with manual format selection
        thread = DownloadThread(
            url=video_url,
            format_id=None,  # Not used for manual selection
            output_path=temp_download_dir,
            update_queue=update_queue,
            video_format_id=video_id,
            audio_format_id=audio_id
        )
        
        thread.start()
        if thread.thread:
            thread.thread.join(timeout=90.0)
        
        # Collect messages
        messages = []
        while not update_queue.empty():
            try:
                messages.append(update_queue.get_nowait())
            except queue.Empty:
                break
        
        # Check for success
        finished = [m for m in messages if m.get("type") == "finished"]
        errors = [m for m in messages if m.get("type") == "error"]
        
        if errors:
            print(f"[ERROR] Download errors: {[e.get('text') for e in errors]}")
        
        assert len(finished) > 0, f"Should complete download with {video_id}+{audio_id}. Errors: {errors}"
        
        # Verify file exists
        video_files = list(Path(temp_download_dir).glob("*.*"))
        assert len(video_files) > 0, "Should create merged file"
        
        # Verify filename contains the format IDs
        filename = video_files[0].name
        assert video_id in filename or "+" in filename, f"Filename should indicate format: {filename}"
        
        file_size = video_files[0].stat().st_size
        print(f"[OK] Downloaded: {filename}")
        print(f"     Size: {file_size / 1024:.1f} KB")


class TestPlaylistRandomCombinations:
    """Test random video+audio format combinations for playlist videos"""

    def test_playlist_random_combination_1(self, temp_download_dir, update_queue, loaded_cookies, available_formats):
        """Test random combination #1 in playlist context"""
        self._test_playlist_random_combination(temp_download_dir, update_queue, available_formats, seed=10)

    def test_playlist_random_combination_2(self, temp_download_dir, update_queue, loaded_cookies, available_formats):
        """Test random combination #2 in playlist context"""
        self._test_playlist_random_combination(temp_download_dir, update_queue, available_formats, seed=20)

    def test_playlist_random_combination_3(self, temp_download_dir, update_queue, loaded_cookies, available_formats):
        """Test random combination #3 in playlist context"""
        self._test_playlist_random_combination(temp_download_dir, update_queue, available_formats, seed=30)

    def _test_playlist_random_combination(self, temp_download_dir, update_queue, available_formats, seed):
        """Helper method to test random combination in playlist downloader"""
        random.seed(seed)
        
        video_formats = available_formats["video"]
        audio_formats = available_formats["audio"]
        video_url = available_formats["video_url"]
        
        # Select random formats
        video_fmt = random.choice(video_formats)
        audio_fmt = random.choice(audio_formats)
        
        video_id = video_fmt["id"]
        audio_id = audio_fmt["id"]
        
        print(f"\n[PLAYLIST TEST] Combination seed={seed}:")
        print(f"                Video: {video_id} ({video_fmt['description']})")
        print(f"                Audio: {audio_id} ({audio_fmt['description']})")
        
        # Create PlaylistVideoDownloader with manual formats
        downloader = PlaylistVideoDownloader(
            url=video_url,
            format_id=None,
            output_path=temp_download_dir,
            update_queue=update_queue,
            video_index=1,
            total_videos=1,
            video_format_id=video_id,
            audio_format_id=audio_id
        )
        
        downloader.start()
        if downloader.thread:
            downloader.thread.join(timeout=90.0)
        
        # Collect messages
        messages = []
        while not update_queue.empty():
            try:
                messages.append(update_queue.get_nowait())
            except queue.Empty:
                break
        
        # Check success
        finished = [m for m in messages if m.get("type") in ["playlist_video_finished", "finished"]]
        errors = [m for m in messages if m.get("type") in ["playlist_video_error", "error"]]
        
        if errors:
            print(f"[ERROR] Errors: {[e.get('text') for e in errors]}")
        
        assert len(finished) > 0 or downloader.success, \
            f"Should complete with {video_id}+{audio_id}. Success={downloader.success}, Errors: {errors}"
        
        # Verify file
        video_files = list(Path(temp_download_dir).glob("*.*"))
        assert len(video_files) > 0, "Should create file"
        
        filename = video_files[0].name
        file_size = video_files[0].stat().st_size
        
        print(f"[OK] Playlist download: {filename}")
        print(f"     Size: {file_size / 1024:.1f} KB")


class TestFormatRespectVerification:
    """Verify that downloaded files actually use the requested formats"""

    def test_verify_format_in_filename(self, temp_download_dir, update_queue, loaded_cookies, available_formats):
        """Verify that the downloaded filename contains the requested format IDs"""
        video_formats = available_formats["video"]
        audio_formats = available_formats["audio"]
        video_url = available_formats["video_url"]
        
        # Pick specific formats for verification
        video_fmt = video_formats[0] if len(video_formats) > 0 else None
        audio_fmt = audio_formats[0] if len(audio_formats) > 0 else None
        
        assert video_fmt is not None, "Need at least one video format"
        assert audio_fmt is not None, "Need at least one audio format"
        
        video_id = video_fmt["id"]
        audio_id = audio_fmt["id"]
        
        print(f"\n[VERIFY] Testing format verification:")
        print(f"         Requesting video: {video_id}")
        print(f"         Requesting audio: {audio_id}")
        
        thread = DownloadThread(
            url=video_url,
            format_id=None,
            output_path=temp_download_dir,
            update_queue=update_queue,
            video_format_id=video_id,
            audio_format_id=audio_id
        )
        
        thread.start()
        if thread.thread:
            thread.thread.join(timeout=90.0)
        
        # Get messages
        messages = []
        while not update_queue.empty():
            try:
                messages.append(update_queue.get_nowait())
            except queue.Empty:
                break
        
        finished = [m for m in messages if m.get("type") == "finished"]
        assert len(finished) > 0, "Should complete download"
        
        # Check filename contains the format combination
        video_files = list(Path(temp_download_dir).glob("*.*"))
        assert len(video_files) > 0, "Should create file"
        
        filename = video_files[0].name
        
        # Filename should contain the format combination in brackets
        # Format: "Title [video_id+audio_id].ext"
        expected_format_string = f"{video_id}+{audio_id}"
        
        assert expected_format_string in filename, \
            f"Filename should contain '{expected_format_string}', got: {filename}"
        
        print(f"[OK] Format verified in filename: {filename}")
        print(f"     Contains expected format string: [{expected_format_string}]")


class TestEdgeCaseFormats:
    """Test edge cases and special format scenarios"""

    def test_highest_quality_video_with_highest_quality_audio(self, temp_download_dir, update_queue, loaded_cookies, available_formats):
        """Test combining the highest quality video with highest quality audio"""
        video_formats = available_formats["video"]
        audio_formats = available_formats["audio"]
        video_url = available_formats["video_url"]
        
        # Find highest quality video (by height)
        video_fmt = max(video_formats, key=lambda f: f.get("height", 0))
        # Find highest quality audio (by bitrate)
        audio_fmt = max(audio_formats, key=lambda f: f.get("abr", 0))
        
        video_id = video_fmt["id"]
        audio_id = audio_fmt["id"]
        
        print(f"\n[HIGHEST QUALITY]")
        print(f"  Video: {video_id} ({video_fmt['description']})")
        print(f"  Audio: {audio_id} ({audio_fmt['description']})")
        
        thread = DownloadThread(
            url=video_url,
            format_id=None,
            output_path=temp_download_dir,
            update_queue=update_queue,
            video_format_id=video_id,
            audio_format_id=audio_id
        )
        
        thread.start()
        if thread.thread:
            thread.thread.join(timeout=120.0)
        
        messages = []
        while not update_queue.empty():
            try:
                messages.append(update_queue.get_nowait())
            except queue.Empty:
                break
        
        finished = [m for m in messages if m.get("type") == "finished"]
        errors = [m for m in messages if m.get("type") == "error"]
        
        if errors:
            print(f"[ERROR] {errors}")
        
        assert len(finished) > 0, f"Should download highest quality. Errors: {errors}"
        
        video_files = list(Path(temp_download_dir).glob("*.*"))
        file_size = video_files[0].stat().st_size if video_files else 0
        
        print(f"[OK] Highest quality downloaded: {video_files[0].name if video_files else 'unknown'}")
        print(f"     Size: {file_size / (1024 * 1024):.2f} MB")

    def test_lowest_quality_video_with_lowest_quality_audio(self, temp_download_dir, update_queue, loaded_cookies, available_formats):
        """Test combining the lowest quality video with lowest quality audio"""
        video_formats = available_formats["video"]
        audio_formats = available_formats["audio"]
        video_url = available_formats["video_url"]
        
        # Find lowest quality video (by height)
        video_fmt = min([f for f in video_formats if f.get("height", 0) > 0], key=lambda f: f.get("height", 999))
        # Find lowest quality audio (by bitrate)
        audio_fmt = min([f for f in audio_formats if f.get("abr", 0) > 0], key=lambda f: f.get("abr", 999))
        
        video_id = video_fmt["id"]
        audio_id = audio_fmt["id"]
        
        print(f"\n[LOWEST QUALITY]")
        print(f"  Video: {video_id} ({video_fmt['description']})")
        print(f"  Audio: {audio_id} ({audio_fmt['description']})")
        
        thread = DownloadThread(
            url=video_url,
            format_id=None,
            output_path=temp_download_dir,
            update_queue=update_queue,
            video_format_id=video_id,
            audio_format_id=audio_id
        )
        
        thread.start()
        if thread.thread:
            thread.thread.join(timeout=60.0)
        
        messages = []
        while not update_queue.empty():
            try:
                messages.append(update_queue.get_nowait())
            except queue.Empty:
                break
        
        finished = [m for m in messages if m.get("type") == "finished"]
        assert len(finished) > 0, "Should download lowest quality"
        
        video_files = list(Path(temp_download_dir).glob("*.*"))
        file_size = video_files[0].stat().st_size if video_files else 0
        
        print(f"[OK] Lowest quality downloaded: {video_files[0].name if video_files else 'unknown'}")
        print(f"     Size: {file_size / 1024:.1f} KB")

    def test_mismatched_formats_different_containers(self, temp_download_dir, update_queue, loaded_cookies, available_formats):
        """Test combining formats with different containers (e.g., mp4 video + webm audio)"""
        video_formats = available_formats["video"]
        audio_formats = available_formats["audio"]
        video_url = available_formats["video_url"]
        
        # Try to find mp4 video and webm audio (or vice versa)
        video_fmt = None
        audio_fmt = None
        
        for vf in video_formats:
            if vf["ext"] == "mp4":
                video_fmt = vf
                break
        
        for af in audio_formats:
            if af["ext"] in ["webm", "opus"]:
                audio_fmt = af
                break
        
        # Fallback to any formats if specific containers not found
        if video_fmt is None:
            video_fmt = video_formats[0]
        if audio_fmt is None:
            audio_fmt = audio_formats[0]
        
        video_id = video_fmt["id"]
        audio_id = audio_fmt["id"]
        
        print(f"\n[MIXED CONTAINERS]")
        print(f"  Video: {video_id} ({video_fmt['ext']}) - {video_fmt['description']}")
        print(f"  Audio: {audio_id} ({audio_fmt['ext']}) - {audio_fmt['description']}")
        
        thread = DownloadThread(
            url=video_url,
            format_id=None,
            output_path=temp_download_dir,
            update_queue=update_queue,
            video_format_id=video_id,
            audio_format_id=audio_id
        )
        
        thread.start()
        if thread.thread:
            thread.thread.join(timeout=90.0)
        
        messages = []
        while not update_queue.empty():
            try:
                messages.append(update_queue.get_nowait())
            except queue.Empty:
                break
        
        finished = [m for m in messages if m.get("type") == "finished"]
        assert len(finished) > 0, "Should handle mismatched containers (FFmpeg remuxes)"
        
        video_files = list(Path(temp_download_dir).glob("*.*"))
        print(f"[OK] Mixed containers handled: {video_files[0].name if video_files else 'unknown'}")


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
