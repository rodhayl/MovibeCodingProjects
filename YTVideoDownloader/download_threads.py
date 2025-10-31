#!/usr/bin/env python3
"""
Download Thread Classes for CustomTkinter Video Downloader

This module contains the DownloadThread and PlaylistDownloadThread classes
that handle video and playlist downloads using threading and queue communication.
"""

import os
import threading
import time

import yt_dlp

from app_logger import AppLogger
from cookie_manager import get_cookie_manager

# Import utility functions
from utils import check_ffmpeg, get_bundled_ffmpeg_path


class _SuppressLogger:
    """Custom logger to suppress yt-dlp output.

    Shared logger class used by both DownloadThread and PlaylistDownloadThread
    to suppress verbose yt-dlp logging output during downloads.
    """

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


class DownloadThread:
    """Thread for downloading individual videos using CustomTkinter threading"""

    def __init__(
        self,
        url,
        format_id,
        output_path,
        update_queue,
        video_format_id=None,
        audio_format_id=None,
    ):
        self.url = url
        self.format_id = format_id
        self.output_path = output_path
        self.update_queue = update_queue
        self.video_format_id = video_format_id
        self.audio_format_id = audio_format_id
        self.logger = AppLogger.get_instance()
        self.correlation_id = None
        self.download_start_time = None
        self.last_progress_time = None
        self.cancelled = False
        self.thread = None
        self._lock = threading.Lock()  # Thread safety for state changes

    def start(self):
        """Start download in background thread"""
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        """Run download in background thread"""
        try:
            self.correlation_id = self.logger.new_correlation_id()
            self.download_start_time = time.time()
            self.last_progress_time = self.download_start_time

            # Send initial status
            self.update_queue.put({"type": "status", "text": "Starting download..."})

            # Determine format selection mode
            if self.video_format_id and self.audio_format_id:
                format_id = f"{self.video_format_id}+{self.audio_format_id}"
                is_merging = True
            else:
                format_id = self.format_id
                is_merging = "+" in self.format_id and self.format_id not in [
                    "bestvideo",
                    "bestaudio",
                ]

            # Check FFmpeg availability
            ffmpeg_available = check_ffmpeg()
            if is_merging and not ffmpeg_available:
                self.update_queue.put(
                    {
                        "type": "status",
                        "text": "FFmpeg not available. Using best single format...",
                    }
                )
                format_id = "best"
                is_merging = False

            # Create fallback sequence
            manual_selected = bool(self.video_format_id and self.audio_format_id)
            if manual_selected:
                format_attempts = [format_id]
            else:
                format_attempts = self._create_quality_aware_fallbacks(
                    format_id, is_merging
                )

            download_success = False
            last_error = ""
            downloaded_file_path = None

            # Try each format until one works
            last_cookie_debug = None
            for _attempt_idx, attempt_format in enumerate(format_attempts):
                with self._lock:
                    if self.cancelled:
                        break

                try:
                    self.logger.log_info(
                        f"Attempting download with format: {attempt_format}"
                    )

                    # Generate unique filename template to avoid conflicts
                    base_template = os.path.join(
                        self.output_path, "%(title)s [%(format_id)s].%(ext)s"
                    )
                    unique_template, expected_filename = self._generate_unique_filename(
                        base_template
                    )

                    ydl_opts = {
                        "format": attempt_format,
                        "outtmpl": unique_template,
                        "progress_hooks": [self.progress_hook],
                        "ignoreerrors": False,
                        "no_warnings": True,
                        "quiet": True,
                        "logger": _SuppressLogger(),
                    }

                    # Add FFmpeg location if available
                    bundled_path = get_bundled_ffmpeg_path()
                    if bundled_path and os.path.exists(bundled_path):
                        ydl_opts["ffmpeg_location"] = bundled_path

                    # Enhanced cookie support
                    try:
                        cookie_manager = get_cookie_manager()
                        if cookie_manager and "youtube.com" in self.url.lower():
                            cookie_data = (
                                cookie_manager.get_cookies_for_ytdlp_enhanced()
                            )
                            if cookie_data:
                                auth_method = cookie_data.get("source", "unknown")
                                # Align User-Agent with browser when using cookies
                                ua = cookie_data.get("user_agent")
                                if ua:
                                    ydl_opts["user_agent"] = ua
                                # Ensure Origin/Referer headers match YouTube
                                headers = ydl_opts.setdefault("http_headers", {})
                                headers.setdefault("Origin", "https://www.youtube.com")
                                headers.setdefault(
                                    "Referer", "https://www.youtube.com/"
                                )
                                # Keep summary for error diagnostics
                                last_cookie_debug = {
                                    "source": auth_method,
                                    "user_agent": bool(ua),
                                }
                                if auth_method == "cookies_from_browser":
                                    browser_spec = cookie_data.get("browser_spec")
                                    if browser_spec:
                                        # Split like "chrome:Profile 1" into (browser, profile)
                                        if ":" in browser_spec:
                                            browser, profile = browser_spec.split(
                                                ":", 1
                                            )
                                            if profile:
                                                ydl_opts["cookiesfrombrowser"] = (
                                                    browser,
                                                    profile,
                                                )
                                            else:
                                                ydl_opts["cookiesfrombrowser"] = (
                                                    browser,
                                                )
                                        else:
                                            ydl_opts["cookiesfrombrowser"] = (
                                                browser_spec,
                                            )
                                        self.logger.log_info(
                                            f"Using cookies from browser: {browser_spec}"
                                        )
                                        if last_cookie_debug is not None:
                                            last_cookie_debug["cookiesfrombrowser"] = (
                                                browser_spec
                                            )
                                elif "cookie_file" in cookie_data:
                                    # Map returned key to yt-dlp option name
                                    cookie_path = cookie_data["cookie_file"]
                                    ydl_opts["cookiefile"] = cookie_path
                                    # Diagnostics: confirm file exists and key presence
                                    try:
                                        exists = os.path.exists(cookie_path)
                                        size = (
                                            os.path.getsize(cookie_path)
                                            if exists
                                            else 0
                                        )
                                        present_keys = []
                                        if exists:
                                            with open(
                                                cookie_path,
                                                encoding="utf-8",
                                                errors="ignore",
                                            ) as cf:
                                                text = cf.read()
                                            for key in [
                                                "__Secure-3PAPISID",
                                                "__Secure-3PSID",
                                                "SAPISID",
                                                "APISID",
                                                "SID",
                                                "HSID",
                                                "SSID",
                                                "VISITOR_INFO1_LIVE",
                                                "CONSENT",
                                            ]:
                                                if key in text:
                                                    present_keys.append(key)
                                        self.logger.log_info(
                                            f"Using cookie file: {cookie_path} (exists={exists}, size={size} bytes, keys={present_keys})"
                                        )
                                        if last_cookie_debug is not None:
                                            last_cookie_debug["cookiefile"] = (
                                                cookie_path
                                            )
                                            last_cookie_debug["cookie_keys"] = (
                                                present_keys
                                            )
                                    except Exception as diag_e:
                                        self.logger.log_warning(
                                            f"Cookie diagnostics failed: {diag_e}"
                                        )
                    except Exception as e:
                        self.logger.log_warning(f"Cookie setup failed: {str(e)}")

                    # Perform download
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([self.url])

                        # Verify the download by locating the produced file
                        if expected_filename and os.path.exists(expected_filename):
                            downloaded_file_path = expected_filename
                            download_success = True
                            self.logger.log_info(
                                f"Download successful: {downloaded_file_path}"
                            )
                        else:
                            downloaded_file_path = self._find_downloaded_file(
                                unique_template
                            )
                            if downloaded_file_path:
                                download_success = True
                                self.logger.log_info(
                                    f"Download successful: {downloaded_file_path}"
                                )
                            else:
                                self.logger.log_warning(
                                    f"Download completed but no file found for format {attempt_format}"
                                )
                                # If merging formats were requested, try fallbacks
                                if is_merging:
                                    continue

                    break

                except Exception as e:
                    last_error = str(e)
                    # Improve guidance for common auth issues
                    if "sign in to confirm" in last_error.lower():
                        self.logger.log_warning(
                            "YouTube requested sign-in despite cookies. Check that your cookie file is fresh and contains SID/SAPISID, and that the user-agent matches.",
                            extra_data={
                                "cookie_debug": last_cookie_debug,
                                "format": attempt_format,
                            },
                        )
                    self.logger.log_warning(
                        f"Format {attempt_format} failed: {last_error}"
                    )
                    continue

            # Report final status based on actual download results
            if download_success and not self.cancelled:
                if downloaded_file_path:
                    filename = os.path.basename(downloaded_file_path)
                    self.update_queue.put(
                        {"type": "finished", "text": f"Download completed: {filename}"}
                    )
                else:
                    self.update_queue.put(
                        {"type": "finished", "text": "Download completed successfully"}
                    )
            elif self.cancelled:
                self.update_queue.put({"type": "status", "text": "Download cancelled"})
            else:
                # Actual download failure
                if "truncated" in last_error.lower() or "invalid" in last_error.lower():
                    error_msg = "Download failed: Invalid or truncated video URL."
                else:
                    error_msg = (
                        f"Download failed: {last_error}"
                        if last_error
                        else "Download failed: Unknown error occurred."
                    )
                # Attach last cookie debug context for troubleshooting
                self.logger.log_error(
                    f"Download failed for URL: {self.url} - {error_msg}",
                    extra_data={"cookie_debug": last_cookie_debug},
                )
                self.update_queue.put({"type": "error", "text": error_msg})

        except Exception as e:
            self.update_queue.put(
                {"type": "error", "text": f"Download error: {str(e)}"}
            )

    def progress_hook(self, d):
        """Progress hook for yt-dlp"""
        with self._lock:
            if self.cancelled:
                return  # Skip progress updates if cancelled

        if d["status"] == "downloading":
            if "total_bytes" in d and d["total_bytes"]:
                percent = int((d["downloaded_bytes"] / d["total_bytes"]) * 100)
            elif "_percent_str" in d:
                percent_str = d["_percent_str"].strip().replace("%", "")
                try:
                    percent = int(float(percent_str))
                except (ValueError, TypeError):
                    percent = 0
            else:
                percent = 0

            # Thread-safe queue update
            try:
                self.update_queue.put(
                    {"type": "progress", "value": percent}, timeout=1.0
                )
            except Exception as e:
                self.logger.log_warning(f"Failed to update progress: {e}")

            if hasattr(d, "speed") and d.get("speed"):
                speed_str = (
                    f" ({d['speed']:.1f} KB/s)"
                    if d["speed"] < 1024 * 1024
                    else f" ({d['speed'] / (1024 * 1024):.1f} MB/s)"
                )
            else:
                speed_str = ""

            self.update_queue.put(
                {"type": "status", "text": f"Downloading... {percent}%{speed_str}"}
            )

    def _create_quality_aware_fallbacks(self, format_id, is_merging):
        """Create quality-aware fallback sequence"""
        fallbacks = [format_id]

        if is_merging:
            fallbacks.extend(["best[height<=720]", "best[height<=480]", "best"])
        else:
            if "best" in format_id:
                fallbacks.extend(
                    ["best[height<=1080]", "best[height<=720]", "best[height<=480]"]
                )
            elif "worst" in format_id:
                fallbacks.extend(["worst[height>=360]", "worst"])

        return fallbacks

    def cancel(self):
        """Cancel download operation"""
        with self._lock:
            self.cancelled = True
            self.logger.log_info(f"Download cancelled for URL: {self.url}")

    def _generate_unique_filename(self, base_template):
        """Generate unique filename by adding incremental suffix if file exists

        Returns:
            tuple: (template, expected_filename) where template is the yt-dlp template
                   and expected_filename is the actual file path that will be created
        """
        try:
            # First, try to get video info to determine the actual filename that would be used
            temp_ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "logger": _SuppressLogger(),
                "outtmpl": base_template,
                "simulate": True,  # Don't actually download
            }

            with yt_dlp.YoutubeDL(temp_ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if info:
                    # Get the filename that would be used
                    original_filename = ydl.prepare_filename(info)

                    # Check if file exists and generate unique name if needed
                    if os.path.exists(original_filename):
                        base_name, ext = os.path.splitext(original_filename)
                        counter = 1

                        # Find the next available filename
                        new_filename = f"{base_name}_{counter}{ext}"
                        while os.path.exists(new_filename):
                            counter += 1
                            new_filename = f"{base_name}_{counter}{ext}"

                        # Create new template with suffix that matches the expected filename
                        dir_path = os.path.dirname(base_template)
                        new_template = os.path.join(
                            dir_path, f"%(title)s_{counter} [%(format_id)s].%(ext)s"
                        )
                        self.logger.log_info(
                            f"File exists, using incremental name with suffix _{counter}"
                        )
                        return new_template, new_filename
                    else:
                        # File doesn't exist, use original template
                        return base_template, original_filename

            # If unable to determine filename, return original template with None
            return base_template, None

        except Exception as e:
            self.logger.log_warning(f"Error generating unique filename: {e}")
            return base_template, None

    def _find_downloaded_file(self, template):
        """Find the downloaded file by searching the output directory

        Args:
            template: The yt-dlp output template used for download

        Returns:
            str: Path to the downloaded file, or None if not found
        """
        try:
            if not os.path.exists(self.output_path):
                return None

            # Only consider likely media files and recent modifications
            allowed_exts = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4a", ".mp3"}
            now = time.time()
            # Use download_start_time as baseline if available
            min_mtime = getattr(self, "download_start_time", now - 300)

            candidates = []
            for f in os.listdir(self.output_path):
                fp = os.path.join(self.output_path, f)
                if not os.path.isfile(fp):
                    continue
                _, ext = os.path.splitext(fp)
                if ext.lower() not in allowed_exts:
                    continue
                try:
                    mtime = os.path.getmtime(fp)
                except OSError:
                    continue
                # Only consider files created/modified after the download started (with some slack)
                if mtime >= (min_mtime - 5):
                    candidates.append((fp, mtime))

            if not candidates:
                return None

            # Pick the most recently modified candidate
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

        except Exception as e:
            self.logger.log_warning(f"Error finding downloaded file: {e}")
            return None
