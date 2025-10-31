#!/usr/bin/env python3
"""
Playlist Downloader Module

This module provides completely independent playlist download functionality,
separated from single video downloads with zero shared dependencies.
"""

import os
import re
import threading
import time
from typing import Any

import yt_dlp

from app_logger import AppLogger
from cookie_manager import get_cookie_manager
from utils import check_ffmpeg


class _PlaylistSuppressLogger:
    """Custom logger to suppress yt-dlp output for playlist downloads."""

    def debug(self, msg):
        """Suppress debug messages."""
        pass

    def info(self, msg):
        """Suppress info messages."""
        pass

    def warning(self, msg):
        """Suppress warning messages."""
        pass

    def error(self, msg):
        """Suppress error messages."""
        pass


class PlaylistVideoDownloader:
    """Individual video downloader for playlist videos with playlist-specific configuration."""

    def __init__(
        self,
        url: str,
        format_id: str,
        output_path: str,
        update_queue,
        video_index: int,
        total_videos: int,
        video_format_id: str | None = None,
        audio_format_id: str | None = None,
    ):
        """Initialize playlist video downloader.

        Args:
            url: Video URL to download
            format_id: Format identifier for download
            output_path: Directory to save the video
            update_queue: Queue for UI updates
            video_index: Current video index in playlist (1-based)
            total_videos: Total number of videos in playlist
            video_format_id: Specific video format ID (for manual selection)
            audio_format_id: Specific audio format ID (for manual selection)
        """
        self.url = url
        self.format_id = format_id
        self.output_path = output_path
        self.update_queue = update_queue
        self.video_index = video_index
        self.total_videos = total_videos
        self.video_format_id = video_format_id
        self.audio_format_id = audio_format_id

        # Independent logging for playlist videos
        self.logger = AppLogger.get_instance()
        self.correlation_id = None

        # Independent state management for playlist videos
        self.download_start_time = None
        self.last_progress_time = None
        self.cancelled = False
        self.thread = None
        self._lock = threading.Lock()
        self.success = False
        self.last_error = ""

        # Playlist-specific configuration
        self.playlist_video_config = {
            "max_retries": 2,  # Fewer retries for playlist videos
            "retry_delay": 1.0,
            "progress_update_interval": 1.0,  # Less frequent updates for playlist
            "timeout": 180,  # Shorter timeout for playlist videos
        }

    def start(self):
        """Start playlist video download in background thread."""
        self.thread = threading.Thread(
            target=self._run_playlist_video_download, daemon=True
        )
        self.thread.start()

    def cancel(self):
        """Cancel playlist video download."""
        with self._lock:
            self.cancelled = True

    def is_running(self) -> bool:
        """Check if download is currently running."""
        return self.thread is not None and self.thread.is_alive()

    def _run_playlist_video_download(self):
        """Run playlist video download in background thread."""
        try:
            self.correlation_id = self.logger.new_correlation_id()
            self.download_start_time = time.time()
            self.last_progress_time = self.download_start_time

            # Send initial status for playlist video
            self._send_playlist_status_update(
                f"Starting download {self.video_index}/{self.total_videos}..."
            )
            self.logger.log_info(
                f"Starting playlist video download {self.video_index}/{self.total_videos}: {self.url}"
            )

            # Determine format selection mode for playlist video
            if self.video_format_id and self.audio_format_id:
                format_id = f"{self.video_format_id}+{self.audio_format_id}"
                is_merging = True
            else:
                format_id = self.format_id
                is_merging = "+" in self.format_id and self.format_id not in [
                    "bestvideo",
                    "bestaudio",
                ]

            # Check FFmpeg availability for playlist video
            ffmpeg_available = check_ffmpeg()
            if is_merging and not ffmpeg_available:
                self._send_playlist_status_update(
                    f"Video {self.video_index}/{self.total_videos}: FFmpeg not available, using best single format..."
                )
                format_id = "best"
                is_merging = False

            # Create fallback sequence for playlist video
            format_attempts = self._create_playlist_video_quality_fallbacks(
                format_id, is_merging
            )

            download_success = False
            last_error = ""
            downloaded_file_path = None

            # Try each format until one works
            for attempt_idx, attempt_format in enumerate(format_attempts):
                with self._lock:
                    if self.cancelled:
                        self._send_playlist_status_update(
                            f"Video {self.video_index}/{self.total_videos} cancelled"
                        )
                        return

                try:
                    self.logger.log_info(
                        f"Playlist video {self.video_index} download attempt {attempt_idx + 1}: {attempt_format}"
                    )
                    self._send_playlist_status_update(
                        f"Downloading {self.video_index}/{self.total_videos} (format: {attempt_format})..."
                    )

                    # Generate unique filename template for playlist video
                    base_template = os.path.join(
                        self.output_path, "%(title)s [%(format_id)s].%(ext)s"
                    )
                    unique_template, expected_filename = (
                        self._generate_playlist_video_filename(base_template)
                    )

                    # Configure yt-dlp options for playlist video
                    ydl_opts = self._create_playlist_video_ydl_options(
                        attempt_format, unique_template
                    )

                    # Enhanced cookie support for playlist video
                    self._setup_playlist_video_cookies(ydl_opts)

                    # Perform playlist video download
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([self.url])

                        # Verify the download was successful
                        if expected_filename and os.path.exists(expected_filename):
                            downloaded_file_path = expected_filename
                            download_success = True
                            self.logger.log_info(
                                f"Playlist video {self.video_index} download successful: {downloaded_file_path}"
                            )
                        else:
                            # Try to find any newly created file
                            downloaded_file_path = (
                                self._find_playlist_video_downloaded_file(
                                    unique_template
                                )
                            )
                            if downloaded_file_path:
                                download_success = True
                                self.logger.log_info(
                                    f"Playlist video {self.video_index} download successful: {downloaded_file_path}"
                                )
                            else:
                                self.logger.log_warning(
                                    f"Playlist video {self.video_index} download completed but no file found for format {attempt_format}"
                                )
                                continue

                    break

                except Exception as e:
                    last_error = str(e)
                    self.logger.log_warning(
                        f"Playlist video {self.video_index} format {attempt_format} failed: {last_error}"
                    )
                    continue

            # Report final status for playlist video download
            if download_success and not self.cancelled:
                self.success = True
                if downloaded_file_path:
                    filename = os.path.basename(downloaded_file_path)
                    self._send_playlist_video_finished_update(
                        f"Video {self.video_index}/{self.total_videos} completed: {filename}"
                    )
                else:
                    self._send_playlist_video_finished_update(
                        f"Video {self.video_index}/{self.total_videos} completed successfully"
                    )
            elif self.cancelled:
                self._send_playlist_status_update(
                    f"Video {self.video_index}/{self.total_videos} cancelled"
                )
            else:
                self.success = False
                error_msg = (
                    f"Video {self.video_index}/{self.total_videos} failed: {last_error}"
                    if last_error
                    else f"Video {self.video_index}/{self.total_videos} failed"
                )
                self.last_error = last_error
                self._send_playlist_video_error_update(error_msg)

        except Exception as e:
            self.logger.log_error(
                f"Playlist video {self.video_index} download error: {e}", exception=e
            )
            self._send_playlist_video_error_update(
                f"Video {self.video_index}/{self.total_videos} error: {str(e)}"
            )

    def _create_playlist_video_quality_fallbacks(
        self, format_id: str, is_merging: bool
    ) -> list:
        """Create quality-aware fallback sequence for playlist video downloads."""
        fallbacks = []

        # Add the requested format first
        fallbacks.append(format_id)

        # Add playlist-specific fallbacks (more conservative for batch downloads)
        if is_merging:
            fallbacks.extend(
                [
                    "bestvideo[height<=720]+bestaudio",  # Lower quality for playlist efficiency
                    "bestvideo[height<=480]+bestaudio",
                    "bestvideo+bestaudio",
                    "best[height<=720]",
                    "best[height<=480]",
                    "best",
                ]
            )
        else:
            fallbacks.extend(["best[height<=720]", "best[height<=480]", "best"])

        # Remove duplicates while preserving order
        seen = set()
        unique_fallbacks = []
        for fmt in fallbacks:
            if fmt not in seen:
                seen.add(fmt)
                unique_fallbacks.append(fmt)

        return unique_fallbacks

    def _generate_playlist_video_filename(self, base_template: str) -> tuple:
        """Generate unique filename template for playlist video downloads."""
        timestamp = int(time.time() * 1000)
        unique_template = base_template.replace(
            "%(title)s", f"%(title)s_pv_{self.video_index}_{timestamp}"
        )

        # Try to predict the expected filename
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if info:
                    title = info.get("title", "video")
                    # Clean title for filename
                    clean_title = re.sub(r'[<>:"/\\|?*]', "_", title)
                    expected_filename = os.path.join(
                        self.output_path,
                        f"{clean_title}_pv_{self.video_index}_{timestamp} [{self.format_id}].mp4",
                    )
                    return unique_template, expected_filename
        except Exception:
            pass

        return unique_template, None

    def _create_playlist_video_ydl_options(
        self, format_id: str, template: str
    ) -> dict[str, Any]:
        """Create yt-dlp options specifically for playlist video downloads."""
        from utils import create_base_ytdlp_opts

        ydl_opts = create_base_ytdlp_opts(
            format_id=format_id,
            quiet=True,
            no_warnings=True,
            socket_timeout=self.playlist_video_config["timeout"],
            retries=self.playlist_video_config["max_retries"],
        )

        # Add playlist-specific options
        ydl_opts["outtmpl"] = template
        ydl_opts["progress_hooks"] = [self._playlist_video_progress_hook]
        ydl_opts["logger"] = _PlaylistSuppressLogger()

        return ydl_opts

    def _setup_playlist_video_cookies(self, ydl_opts: dict[str, Any]):
        """Setup cookies specifically for playlist video downloads."""
        from utils import setup_ytdlp_cookies

        setup_ytdlp_cookies(
            ydl_opts=ydl_opts,
            cookie_manager=get_cookie_manager(),
            url=self.url,
            logger=self.logger,
            context="playlist",
        )

    def _find_playlist_video_downloaded_file(self, template: str) -> str | None:
        """Find downloaded file for playlist video downloads."""
        try:
            # Extract directory from template
            template_dir = os.path.dirname(template)
            if not os.path.exists(template_dir):
                return None

            # Look for recently created files
            current_time = time.time()
            for filename in os.listdir(template_dir):
                filepath = os.path.join(template_dir, filename)
                if os.path.isfile(filepath):
                    # Check if file was created recently (within last 60 seconds)
                    if current_time - os.path.getctime(filepath) < 60:
                        # Check if it's a video file
                        if any(
                            filename.lower().endswith(ext)
                            for ext in [".mp4", ".mkv", ".webm", ".avi", ".mov"]
                        ):
                            return filepath
        except Exception as e:
            self.logger.log_warning(
                f"Error finding playlist video downloaded file: {e}"
            )

        return None

    def _playlist_video_progress_hook(self, d: dict[str, Any]):
        """Progress hook specifically for playlist video downloads."""
        if d["status"] == "downloading":
            current_time = time.time()

            # Throttle progress updates for playlist videos
            if (current_time - self.last_progress_time) < self.playlist_video_config[
                "progress_update_interval"
            ]:
                return

            self.last_progress_time = current_time

            # Calculate progress
            if "total_bytes" in d and d["total_bytes"]:
                progress = (d["downloaded_bytes"] / d["total_bytes"]) * 100
            elif "total_bytes_estimate" in d and d["total_bytes_estimate"]:
                progress = (d["downloaded_bytes"] / d["total_bytes_estimate"]) * 100
            else:
                progress = 0

            # Send progress update for current video
            self._send_playlist_video_progress_update(progress)

            # Update status with download info
            speed = d.get("speed", 0)
            if speed:
                speed_str = f"{speed / 1024 / 1024:.1f} MB/s"
                self._send_playlist_status_update(
                    f"Downloading {self.video_index}/{self.total_videos}... {progress:.1f}% ({speed_str})"
                )
            else:
                self._send_playlist_status_update(
                    f"Downloading {self.video_index}/{self.total_videos}... {progress:.1f}%"
                )

        elif d["status"] == "finished":
            self._send_playlist_video_progress_update(100)
            self._send_playlist_status_update(
                f"Processing video {self.video_index}/{self.total_videos}..."
            )

    def _send_playlist_status_update(self, text: str):
        """Send playlist status update to UI queue."""
        self.update_queue.put({"type": "playlist_status", "text": text})

    def _send_playlist_video_progress_update(self, progress: float):
        """Send playlist video progress update to UI queue."""
        self.update_queue.put({"type": "playlist_video_progress", "value": progress})

    def _send_playlist_video_finished_update(self, text: str):
        """Send playlist video finished update to UI queue."""
        self.update_queue.put({"type": "playlist_video_finished", "text": text})

    def _send_playlist_video_error_update(self, text: str):
        """Send playlist video error update to UI queue."""
        self.update_queue.put({"type": "playlist_video_error", "text": text})


class PlaylistDownloader:
    """Independent playlist downloader with complete isolation from single video functionality."""

    def __init__(
        self,
        selected_videos: list[dict[str, Any]],
        format_id: str,
        output_path: str,
        update_queue,
        video_format_id: str | None = None,
        audio_format_id: str | None = None,
    ):
        """Initialize playlist downloader.

        Args:
            selected_videos: List of selected video dictionaries with 'url' and other info
            format_id: Format identifier for downloads
            output_path: Directory to save the videos
            update_queue: Queue for UI updates
            video_format_id: Specific video format ID (for manual selection)
            audio_format_id: Specific audio format ID (for manual selection)
        """
        self.selected_videos = selected_videos
        self.format_id = format_id
        self.output_path = output_path
        self.update_queue = update_queue
        self.video_format_id = video_format_id
        self.audio_format_id = audio_format_id

        # Independent logging for playlist
        self.logger = AppLogger.get_instance()
        self.correlation_id = None

        # Independent state management for playlist
        self.download_start_time = None
        self.cancelled = False
        self.thread = None
        self.current_video_downloader = None
        self._lock = threading.Lock()

        # Playlist-specific configuration
        self.playlist_config = {
            "max_concurrent_downloads": 1,  # Sequential downloads for stability
            "retry_failed_videos": True,
            "continue_on_error": True,
            "inter_video_delay": 1.0,  # Delay between video downloads
        }

        # Playlist download state
        self.current_video_index = 0
        self.total_videos = len(selected_videos)
        self.completed_videos = 0
        self.failed_videos = 0
        self.skipped_videos = 0

    def start(self):
        """Start playlist download in background thread."""
        self.thread = threading.Thread(target=self._run_playlist_download, daemon=True)
        self.thread.start()

    def cancel(self):
        """Cancel playlist download."""
        with self._lock:
            self.cancelled = True
            if self.current_video_downloader:
                self.current_video_downloader.cancel()

    def is_running(self) -> bool:
        """Check if playlist download is currently running."""
        return self.thread is not None and self.thread.is_alive()

    def _run_playlist_download(self):
        """Run playlist download in background thread."""
        try:
            self.correlation_id = self.logger.new_correlation_id()
            self.download_start_time = time.time()

            # Send initial status
            self._send_playlist_status_update(
                f"Starting playlist download of {self.total_videos} videos..."
            )
            self.logger.log_info(
                f"Starting playlist download: {self.total_videos} videos"
            )

            # Download each video sequentially
            for video_index, video_info in enumerate(self.selected_videos):
                with self._lock:
                    if self.cancelled:
                        self._send_playlist_status_update("Playlist download cancelled")
                        return

                self.current_video_index = video_index + 1

                # Extract video URL
                video_url = video_info.get("url", "")
                if not video_url:
                    self.logger.log_warning(
                        f"Skipping video {self.current_video_index}: No URL found"
                    )
                    self.skipped_videos += 1
                    continue

                # Update overall playlist progress
                overall_progress = (video_index / self.total_videos) * 100
                self._send_playlist_overall_progress_update(overall_progress)

                # Create and start video downloader
                self.current_video_downloader = PlaylistVideoDownloader(
                    url=video_url,
                    format_id=self.format_id,
                    output_path=self.output_path,
                    update_queue=self.update_queue,
                    video_index=self.current_video_index,
                    total_videos=self.total_videos,
                    video_format_id=self.video_format_id,
                    audio_format_id=self.audio_format_id,
                )

                self.current_video_downloader.start()

                # Wait for video download to complete
                while self.current_video_downloader.is_running():
                    with self._lock:
                        if self.cancelled:
                            self.current_video_downloader.cancel()
                            break
                    time.sleep(0.5)

                # Check if download was successful
                if not self.cancelled:
                    if getattr(self.current_video_downloader, "success", False):
                        self.completed_videos += 1
                        self.logger.log_info(
                            f"Completed playlist video {self.current_video_index}/{self.total_videos}"
                        )
                    else:
                        self.failed_videos += 1
                        err = getattr(self.current_video_downloader, "last_error", "")
                        self.logger.log_info(
                            f"Playlist video error: Video {self.current_video_index}/{self.total_videos} failed: {err}"
                        )

                # Add delay between videos if not cancelled
                if not self.cancelled and video_index < len(self.selected_videos) - 1:
                    time.sleep(self.playlist_config["inter_video_delay"])

            # Send final status
            if not self.cancelled:
                # Update final progress
                self._send_playlist_overall_progress_update(100)

                # Send completion message
                completion_msg = f"Playlist download completed! {self.completed_videos}/{self.total_videos} videos downloaded successfully."
                if self.failed_videos > 0:
                    completion_msg += f" {self.failed_videos} videos failed."
                if self.skipped_videos > 0:
                    completion_msg += f" {self.skipped_videos} videos skipped."

                self._send_playlist_finished_update(completion_msg)
                self.logger.log_info(
                    f"Playlist download completed: {self.completed_videos}/{self.total_videos} successful"
                )
            else:
                self._send_playlist_status_update("Playlist download cancelled")
                self.logger.log_info("Playlist download cancelled by user")

        except Exception as e:
            self.logger.log_error(f"Playlist download error: {e}", exception=e)
            self._send_playlist_error_update(f"Playlist download error: {str(e)}")

    def _send_playlist_status_update(self, text: str):
        """Send playlist status update to UI queue."""
        self.update_queue.put({"type": "playlist_status", "text": text})

    def _send_playlist_overall_progress_update(self, progress: float):
        """Send playlist overall progress update to UI queue."""
        self.update_queue.put({"type": "playlist_progress", "value": progress})

    def _send_playlist_finished_update(self, text: str):
        """Send playlist finished update to UI queue."""
        self.update_queue.put({"type": "playlist_finished", "text": text})

    def _send_playlist_error_update(self, text: str):
        """Send playlist error update to UI queue."""
        self.update_queue.put({"type": "playlist_error", "text": text})
