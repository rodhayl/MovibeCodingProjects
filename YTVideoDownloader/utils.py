#!/usr/bin/env python3
"""
Utility Functions for YouTube Video Downloader

This module contains shared utility functions used across the application
to avoid circular import dependencies.
"""

import os
import platform
import re
import subprocess
import sys

from app_logger import AppLogger, log_function_calls


def html_to_text(html_content: str) -> str:
    """Convert HTML content to plain text.

    This utility function removes HTML tags and converts common HTML entities
    to their text equivalents. Used by cookie help system components.

    Args:
        html_content (str): HTML content to convert

    Returns:
        str: Plain text with HTML tags removed and entities converted
    """
    import re

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", html_content)
    # Replace HTML entities
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return text.strip()


def download_ffmpeg() -> bool:
    """Check for FFmpeg binaries in the bin directory.

    Enhanced version with better platform detection and error handling.
    Uses platform.system() instead of os.name for better cross-platform compatibility.

    Returns:
        bool: True if FFmpeg binary is found, False otherwise
    """
    print("Checking for FFmpeg binaries...")

    # Check if FFmpeg binaries exist in bin directory
    ffmpeg_exe = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    ffmpeg_path = os.path.join("bin", ffmpeg_exe)

    if os.path.exists(ffmpeg_path):
        print(f"Found FFmpeg binary at {ffmpeg_path}")
        return True
    else:
        print(f"FFmpeg binary not found at {ffmpeg_path}")
        print(
            "The executable will be created but FFmpeg functionality will be limited."
        )
        print("Please add FFmpeg binaries to the bin directory for full functionality.")
        return False


@log_function_calls(timeout=10.0)
def get_downloads_folder():
    """
    Get the actual downloads folder path based on OS settings.
    Returns the correct path even if user has customized the Downloads folder location.

    Returns:
        str: Path to the downloads folder
    """
    logger = AppLogger.get_instance()
    try:
        if os.name == "nt":  # Windows
            result = _get_windows_downloads_folder()
            logger.log_debug(f"Windows downloads folder: {result}")
            return result
        else:  # macOS and Linux
            result = _get_unix_downloads_folder()
            logger.log_debug(f"Unix downloads folder: {result}")
            return result
    except Exception as e:
        # Fallback to default if any method fails
        fallback = os.path.join(os.path.expanduser("~"), "Downloads")
        logger.log_warning(
            f"Failed to get downloads folder, using fallback: {fallback}",
            extra_data={"error": str(e)},
        )
        return fallback


def _get_windows_downloads_folder():
    """Get Windows Downloads folder using Registry or Known Folder API."""
    try:
        # Method 1: Try Registry
        try:
            import winreg

            sub_key = (
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                return winreg.QueryValueEx(key, downloads_guid)[0]
        except (ImportError, FileNotFoundError, Exception):
            pass

        # Method 2: Try Known Folder API
        try:
            import ctypes
            from ctypes import wintypes
            from uuid import UUID

            # ctypes GUID structure
            class GUID(ctypes.Structure):
                _fields_ = [
                    ("Data1", wintypes.DWORD),
                    ("Data2", wintypes.WORD),
                    ("Data3", wintypes.WORD),
                    ("Data4", wintypes.BYTE * 8),
                ]

                def __init__(self, uuidstr):
                    uuid = UUID(uuidstr)
                    ctypes.Structure.__init__(self)
                    (
                        self.Data1,
                        self.Data2,
                        self.Data3,
                        self.Data4[0],
                        self.Data4[1],
                        rest,
                    ) = uuid.fields
                    for i in range(2, 8):
                        self.Data4[i] = rest >> (8 - i - 1) * 8 & 0xFF

            sh_get_known_folder_path = ctypes.windll.shell32.SHGetKnownFolderPath
            sh_get_known_folder_path.argtypes = [
                ctypes.POINTER(GUID),
                wintypes.DWORD,
                wintypes.HANDLE,
                ctypes.POINTER(ctypes.c_wchar_p),
            ]

            def _get_known_folder_path(uuidstr):
                pathptr = ctypes.c_wchar_p()
                guid = GUID(uuidstr)
                if sh_get_known_folder_path(
                    ctypes.byref(guid), 0, 0, ctypes.byref(pathptr)
                ):
                    raise ctypes.WinError()
                return pathptr.value

            folderid_download = "{374DE290-123F-4565-9164-39C4925E467B}"
            return _get_known_folder_path(folderid_download)
        except (ImportError, Exception):
            pass

    except Exception:
        pass

    # Fallback
    return os.path.join(os.path.expanduser("~"), "Downloads")


def _get_unix_downloads_folder():
    """Get Unix-like system (macOS/Linux) Downloads folder."""
    try:
        # Try xdg-user-dir command
        import subprocess

        result = subprocess.run(
            ["xdg-user-dir", "DOWNLOAD"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            path = result.stdout.strip()
            if os.path.exists(path):
                return path
    except (FileNotFoundError, subprocess.SubprocessError, Exception):
        pass

    # Fallback
    try:
        from pathlib import Path

        downloads_path = Path.home() / "Downloads"
        return str(downloads_path)
    except Exception:
        return os.path.join(os.path.expanduser("~"), "Downloads")


@log_function_calls(timeout=15.0)
def get_bundled_ffmpeg_path():
    """Get path to bundled FFmpeg binary"""
    logger = AppLogger.get_instance()

    # First check for manually bundled FFmpeg in bin directory
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        app_dir = os.path.dirname(sys.executable)
        logger.log_debug(
            "Running as compiled executable", extra_data={"app_dir": app_dir}
        )
    else:
        # Running as script
        app_dir = os.path.dirname(os.path.abspath(__file__))
        logger.log_debug("Running as script", extra_data={"app_dir": app_dir})

    if os.name == "nt":  # Windows
        manual_path = os.path.join(app_dir, "bin", "ffmpeg.exe")
    else:  # macOS/Linux
        manual_path = os.path.join(app_dir, "bin", "ffmpeg")

    logger.log_debug(f"Checking manual FFmpeg path: {manual_path}")

    # Check if the manual path exists and is a valid FFmpeg binary (not just a placeholder)
    if os.path.exists(manual_path):
        file_size = os.path.getsize(manual_path)
        logger.log_debug(f"Found FFmpeg binary, size: {file_size} bytes")
        # A real FFmpeg binary should be much larger than 1KB
        if file_size > 1024:
            logger.log_info(f"Using bundled FFmpeg: {manual_path}")
            return manual_path
        else:
            logger.log_warning(
                f"FFmpeg binary too small ({file_size} bytes), likely placeholder"
            )
    else:
        logger.log_debug("Manual FFmpeg path does not exist")

    # If not found, try to get FFmpeg from imageio
    try:
        logger.log_debug("Attempting to use imageio FFmpeg")
        import imageio_ffmpeg as ffmpeg

        imageio_path = ffmpeg.get_ffmpeg_exe()
        if os.path.exists(imageio_path):
            logger.log_info(f"Using imageio FFmpeg: {imageio_path}")
            return imageio_path
        else:
            logger.log_warning("imageio FFmpeg path does not exist")
    except ImportError:
        logger.log_debug("imageio_ffmpeg not available")
    except Exception as e:
        logger.log_warning(f"Error getting imageio FFmpeg: {str(e)}")

    # If neither is found, return None
    logger.log_warning("No FFmpeg binary found")
    return None


@log_function_calls(timeout=30.0)
def check_ffmpeg():
    """Check for FFmpeg in multiple locations"""
    logger = AppLogger.get_instance()

    from app_logger import log_operation

    with log_operation("ffmpeg_availability_check", timeout=25.0):
        # 1. Check bundled FFmpeg first (including imageio)
        logger.log_debug("Checking bundled FFmpeg")
        bundled_path = get_bundled_ffmpeg_path()
        if bundled_path and os.path.exists(bundled_path):
            logger.log_info(f"FFmpeg found at bundled path: {bundled_path}")
            return True

        # 2. Check system PATH
        logger.log_debug("Checking system PATH for FFmpeg")
        try:
            # Try to run ffmpeg -version
            logger.log_debug("Running 'ffmpeg -version' command")
            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                logger.log_info("FFmpeg found in system PATH")
                logger.log_debug(f"FFmpeg version output: {result.stdout[:200]}...")
                return True
            else:
                logger.log_warning(
                    f"FFmpeg command failed with return code: {result.returncode}"
                )
                logger.log_debug(f"FFmpeg stderr: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.log_error("FFmpeg version check timed out")
            return False
        except FileNotFoundError:
            logger.log_debug("FFmpeg not found in system PATH")
            return False
        except subprocess.SubprocessError as e:
            logger.log_error(f"Subprocess error checking FFmpeg: {str(e)}")
            return False
        except Exception as e:
            logger.log_error(f"Unexpected error checking FFmpeg: {str(e)}", exception=e)
            return False


def is_playlist_url(url):
    """Check if the URL is a playlist URL"""
    playlist_patterns = [
        r"youtube\.com/playlist\?list=",
        r"youtube\.com/watch\?v=.+&list=",
        r"youtube\.com/watch\?list=.+&v=",
        r"youtube\.com/.+/playlists",
        r"youtube\.com/channel/.+/playlists",
        r"youtube\.com/user/.+/playlists",
    ]

    for pattern in playlist_patterns:
        if re.search(pattern, url):
            return True
    return False


def normalize_playlist_url(url):
    """Normalize YouTube playlist URLs by removing all parameters except list"""
    # Extract the list parameter from any YouTube URL format
    match = re.search(r"list=([^&]*)", url)
    if match:
        return f"https://www.youtube.com/playlist?list={match.group(1)}"

    # If no list parameter found, return original URL
    return url


def clean_url_for_video_info(url):
    """Clean URL for video info extraction - remove playlist parameters

    This function extracts only the video ID from mixed URLs that contain
    both video and playlist parameters, preventing HTTP 400 errors when
    using authenticated requests with yt-dlp.
    """
    # Pattern to match YouTube video IDs
    patterns = [
        r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"

    # If no video ID found, return original URL
    return url


class PlaylistInfo:
    """Class to hold playlist information"""

    def __init__(self):
        self.title = ""
        self.description = ""
        self.video_count = 0
        self.videos = []  # List of PlaylistVideo objects
        self.thumbnail_url = ""


class PlaylistVideo:
    """Class to hold individual video information in a playlist"""

    def __init__(self):
        self.id = ""
        self.title = ""
        self.duration = 0
        self.selected = True
        self.available_formats = []
        self.status = "pending"  # pending, downloading, completed, error


# Shared yt-dlp helper functions
def setup_ytdlp_cookies(
    ydl_opts: dict, cookie_manager, url: str, logger=None, context: str = ""
) -> None:
    """Setup cookies for yt-dlp options.

    This shared function configures cookie authentication for yt-dlp downloads,
    supporting both browser cookie extraction and cookie file import methods.

    Args:
        ydl_opts (dict): yt-dlp options dictionary to configure
        cookie_manager: Cookie manager instance (or None)
        url (str): URL being downloaded (to check if YouTube)
        logger: Optional logger instance for logging
        context (str): Optional context string for log messages (e.g., "playlist", "info")
    """
    try:
        if cookie_manager and "youtube.com" in url.lower():
            cookie_data = cookie_manager.get_cookies_for_ytdlp_enhanced()
            if cookie_data:
                auth_method = cookie_data.get("source", "unknown")

                # Set user agent if provided
                ua = cookie_data.get("user_agent")
                if ua:
                    ydl_opts["user_agent"] = ua

                # Set HTTP headers
                headers = ydl_opts.setdefault("http_headers", {})
                headers.setdefault("Origin", "https://www.youtube.com")
                headers.setdefault("Referer", "https://www.youtube.com/")

                # Configure cookie source
                if auth_method == "cookies_from_browser":
                    browser_spec = cookie_data.get("browser_spec")
                    if browser_spec:
                        if ":" in browser_spec:
                            browser, profile = browser_spec.split(":", 1)
                            if profile:
                                ydl_opts["cookiesfrombrowser"] = (browser, profile)
                            else:
                                ydl_opts["cookiesfrombrowser"] = (browser,)
                        else:
                            ydl_opts["cookiesfrombrowser"] = (browser_spec,)

                        if logger:
                            prefix = f"[{context}] " if context else ""
                            logger.log_info(
                                f"{prefix}Using cookies from browser: {browser_spec}"
                            )

                elif "cookie_file" in cookie_data:
                    cookie_path = cookie_data["cookie_file"]
                    ydl_opts["cookiefile"] = cookie_path

                    # Log cookie file diagnostics if logger provided
                    if logger:
                        try:
                            exists = os.path.exists(cookie_path)
                            size = os.path.getsize(cookie_path) if exists else 0
                            keys = []
                            if exists:
                                with open(
                                    cookie_path, encoding="utf-8", errors="ignore"
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
                                        keys.append(key)
                                prefix = f"[{context}] " if context else ""
                                logger.log_info(
                                    f"{prefix}Using cookie file: {cookie_path} (exists={exists}, size={size}, keys={keys})"
                                )
                        except Exception as diag_e:
                            prefix = f"[{context}] " if context else ""
                            logger.log_warning(
                                f"{prefix}Cookie diagnostics failed: {diag_e}"
                            )

    except Exception as e:
        if logger:
            prefix = f"[{context}] " if context else ""
            logger.log_warning(f"{prefix}Cookie setup failed: {str(e)}")


def create_base_ytdlp_opts(
    format_id: str = "bestvideo+bestaudio",
    quiet: bool = True,
    no_warnings: bool = True,
    socket_timeout: int = 60,
    retries: int = 3,
) -> dict:
    """Create base yt-dlp options dictionary.

    Args:
        format_id: Format string for yt-dlp (default: best video+audio)
        quiet: Suppress yt-dlp output
        no_warnings: Suppress yt-dlp warnings
        socket_timeout: Socket timeout in seconds
        retries: Number of retries for failed downloads

    Returns:
        dict: Base yt-dlp options dictionary
    """
    ydl_opts = {
        "format": format_id,
        "ignoreerrors": False,
        "no_warnings": no_warnings,
        "quiet": quiet,
        "socket_timeout": socket_timeout,
        "retries": retries,
    }

    # Add FFmpeg location if available
    bundled_path = get_bundled_ffmpeg_path()
    if bundled_path and os.path.exists(bundled_path):
        ydl_opts["ffmpeg_location"] = bundled_path

    return ydl_opts
