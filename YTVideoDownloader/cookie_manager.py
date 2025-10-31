#!/usr/bin/env python3
"""
Chrome-Only Cookie Management System for YouTube Video Downloader

This module provides Chrome-specific cookie management for yt-dlp to handle
YouTube's bot detection and authentication requirements automatically.

Features:
- Bulletproof Chrome browser detection on Windows
- Chrome cookie database access with SQLite
- Windows DPAPI cookie decryption
- Cookie validation and refresh mechanisms
- Rate limiting and request throttling
- Integration with existing error handling and logging systems
"""

import os
import platform
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
import winreg
from datetime import datetime
from pathlib import Path
from typing import Any


# Windows DPAPI for cookie decryption
try:
    import win32crypt

    WIN32CRYPT_AVAILABLE = True
except ImportError:
    win32crypt = None
    WIN32CRYPT_AVAILABLE = False

from app_logger import AppLogger, log_function_calls


class CookieManagerError(Exception):
    """Base exception for cookie management operations."""

    pass


class ChromeNotFoundError(CookieManagerError):
    """Exception raised when Chrome browser is not found."""

    pass


class CookieExtractionError(CookieManagerError):
    """Exception raised when cookie extraction fails."""

    pass


class CookieValidationError(CookieManagerError):
    """Exception raised when cookie validation fails."""

    pass


class RateLimiter:
    """Rate limiter for cookie extraction requests."""

    def __init__(self, max_requests: int = 10, time_window: int = 300):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = threading.Lock()

    def can_make_request(self) -> bool:
        """Check if a request can be made within rate limits."""
        with self.lock:
            now = time.time()
            # Remove old requests outside the time window
            self.requests = [
                req_time
                for req_time in self.requests
                if now - req_time < self.time_window
            ]
            return len(self.requests) < self.max_requests

    def record_request(self):
        """Record a new request."""
        with self.lock:
            self.requests.append(time.time())


class CookieManager:
    """Chrome-only cookie management system for YouTube downloads."""

    def __init__(self):
        self.logger = AppLogger.get_instance()
        self.cookie_cache = {}
        self.last_extraction_time = {}
        self.rate_limiter = RateLimiter()
        self.lock = threading.Lock()
        self.dpapi_failure_count = 0
        self.dpapi_failure_threshold = 5  # Only log every 5 failures
        self.failed_cookies_cache = set()  # Cache of cookies that consistently fail
        self.failed_domains_cache = (
            {}
        )  # Track domains that consistently fail with timestamps
        self.domain_failure_threshold = (
            3  # Number of failures before marking domain as problematic
        )
        self.domain_cooldown_period = 1800  # 30 minutes cooldown for failed domains
        self._temp_files = set()  # Track temporary files for cleanup
        self._is_shutdown = False  # Track shutdown state
        self._manual_cookie_file_path = None  # Track original manual path

        # Check Windows DPAPI availability
        self._check_crypto_availability()

        # Cookie file paths
        self.cookie_dir = Path(tempfile.gettempdir()) / "ytdl_cookies"
        self.cookie_dir.mkdir(exist_ok=True)

        # Chrome detection
        self.chrome_info = self._detect_chrome()
        if self.chrome_info:
            self.logger.log_info(
                f"Chrome detected: {self.chrome_info['name']} at {self.chrome_info['cookie_path']}"
            )
        else:
            self.logger.log_warning("Chrome browser not detected")

    def _get_default_chrome_user_agent(self) -> str:
        """Return a reasonable Windows Chrome User-Agent string.

        In absence of a reliable programmatic UA lookup, use a modern UA
        compatible with YouTube authenticated flows.
        """
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/127.0.0.0 Safari/537.36"
        )

    def _check_crypto_availability(self):
        """Check and log Windows DPAPI availability."""
        if not WIN32CRYPT_AVAILABLE:
            self.logger.log_warning(
                "Windows DPAPI (win32crypt) not available. Cookie decryption will be limited. "
                "Install pywin32 package for full functionality: pip install pywin32"
            )
        else:
            self.logger.log_info("Windows DPAPI available for cookie decryption")

    def get_crypto_status(self) -> dict[str, bool]:
        """Get status of cryptography libraries."""
        return {
            "win32crypt": WIN32CRYPT_AVAILABLE,
            "chrome_support": WIN32CRYPT_AVAILABLE,
        }

    @log_function_calls(timeout=30.0)
    def _detect_chrome(self) -> dict[str, str] | None:
        """Bulletproof Chrome detection on Windows."""
        if platform.system().lower() != "windows":
            self.logger.log_error("Chrome detection only supported on Windows")
            return None

        self.logger.log_info("Starting bulletproof Chrome detection...")

        # Method 1: Check Windows Registry
        chrome_path = self._get_chrome_from_registry()
        if chrome_path:
            self.logger.log_info(f"Chrome found via registry: {chrome_path}")

        # Method 2: Check standard installation paths
        if not chrome_path:
            chrome_path = self._get_chrome_from_standard_paths()
            if chrome_path:
                self.logger.log_info(f"Chrome found via standard paths: {chrome_path}")

        if not chrome_path:
            self.logger.log_error("Chrome executable not found")
            return None

        # Find Chrome user data directory
        user_data_dir = self._get_chrome_user_data_dir()
        if not user_data_dir:
            self.logger.log_error("Chrome user data directory not found")
            return None

        # Find the best profile with cookies
        profile_info = self._find_best_chrome_profile(user_data_dir)
        if not profile_info:
            self.logger.log_error("No Chrome profile with cookies found")
            return None

        chrome_info = {
            "name": "Google Chrome",
            "executable_path": chrome_path,
            "user_data_dir": str(user_data_dir),
            "profile_name": profile_info["name"],
            "cookie_path": profile_info["cookie_path"],
            "type": "chromium",
            "browser_key": "chrome",
        }

        # Preserve fallback information if present
        if profile_info.get("fallback", False):
            chrome_info["fallback"] = True
            chrome_info["reason"] = profile_info.get("reason", "unknown")
            chrome_info["cookie_count"] = profile_info.get("cookie_count", 0)

        self.logger.log_info(
            f"Chrome detection successful: Profile '{profile_info['name']}' with {profile_info['cookie_count']} cookies"
        )
        return chrome_info

    def _get_chrome_from_registry(self) -> str | None:
        """Get Chrome path from Windows Registry."""
        try:
            # Check HKEY_LOCAL_MACHINE first
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
            ) as key:
                chrome_path, _ = winreg.QueryValueEx(key, "")
                if os.path.exists(chrome_path):
                    self.logger.log_debug(
                        f"Chrome found in HKLM registry: {chrome_path}"
                    )
                    return chrome_path
        except (FileNotFoundError, OSError):
            pass

        try:
            # Check HKEY_CURRENT_USER
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
            ) as key:
                chrome_path, _ = winreg.QueryValueEx(key, "")
                if os.path.exists(chrome_path):
                    self.logger.log_debug(
                        f"Chrome found in HKCU registry: {chrome_path}"
                    )
                    return chrome_path
        except (FileNotFoundError, OSError):
            pass

        try:
            # Check Google Update registry
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Google\Update\Clients\{8A69D345-D564-463c-AFF1-A69D9E530F96}",
            ) as key:
                chrome_path, _ = winreg.QueryValueEx(key, "pv")
                # This gives us version, need to construct path
                program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
                chrome_exe = os.path.join(
                    program_files, "Google", "Chrome", "Application", "chrome.exe"
                )
                if os.path.exists(chrome_exe):
                    self.logger.log_debug(
                        f"Chrome found via Google Update registry: {chrome_exe}"
                    )
                    return chrome_exe
        except (FileNotFoundError, OSError):
            pass

        self.logger.log_debug("Chrome not found in Windows Registry")
        return None

    def _get_chrome_from_standard_paths(self) -> str | None:
        """Check standard Chrome installation paths."""
        standard_paths = [
            os.path.join(
                os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                "Google",
                "Chrome",
                "Application",
                "chrome.exe",
            ),
            os.path.join(
                os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
                "Google",
                "Chrome",
                "Application",
                "chrome.exe",
            ),
            os.path.join(
                os.environ.get("LOCALAPPDATA", ""),
                "Google",
                "Chrome",
                "Application",
                "chrome.exe",
            ),
        ]

        for path in standard_paths:
            if path and os.path.exists(path):
                self.logger.log_debug(f"Chrome found at standard path: {path}")
                return path

        self.logger.log_debug("Chrome not found in standard paths")
        return None

    def _get_chrome_user_data_dir(self) -> Path | None:
        """Get Chrome user data directory."""
        localappdata = os.environ.get("LOCALAPPDATA")
        if not localappdata:
            self.logger.log_error("LOCALAPPDATA environment variable not found")
            return None

        user_data_dir = Path(localappdata) / "Google" / "Chrome" / "User Data"
        if user_data_dir.exists() and user_data_dir.is_dir():
            self.logger.log_debug(f"Chrome user data directory found: {user_data_dir}")
            return user_data_dir

        self.logger.log_error(f"Chrome user data directory not found: {user_data_dir}")
        return None

    def _find_best_chrome_profile(self, user_data_dir: Path) -> dict[str, Any] | None:
        """Find the Chrome profile with the most recent YouTube cookies."""
        profiles = []
        fallback_profiles = []

        # Check all possible profile directories (scan actual directories first)
        actual_profiles = []
        try:
            self.logger.log_debug(
                f"Scanning Chrome user data directory: {user_data_dir}"
            )
            for item in user_data_dir.iterdir():
                self.logger.log_debug(
                    f"Found item in user data dir: {item.name} (is_dir: {item.is_dir()})"
                )
                if item.is_dir():
                    if item.name == "Default" or item.name.startswith("Profile "):
                        actual_profiles.append(item.name)
                        self.logger.log_debug(f"Added profile: {item.name}")
        except Exception as e:
            self.logger.log_warning(f"Error scanning Chrome profiles: {e}")

        # Add standard patterns as fallback
        profile_patterns = actual_profiles + [
            "Default",
            "Profile 1",
            "Profile 2",
            "Profile 3",
            "Profile 4",
            "Profile 5",
        ]
        # Remove duplicates while preserving order
        profile_patterns = list(dict.fromkeys(profile_patterns))

        self.logger.log_debug(f"Checking Chrome profiles: {profile_patterns}")

        # Check if Chrome is currently running
        chrome_running = self._is_chrome_running()
        if chrome_running:
            self.logger.log_info("Detected: Chrome is currently running")

        for pattern in profile_patterns:
            profile_dir = user_data_dir / pattern
            self.logger.log_debug(
                f"Checking profile directory: {profile_dir} (exists: {profile_dir.exists()})"
            )
            if not profile_dir.exists():
                self.logger.log_debug(
                    f"Profile directory does not exist: {profile_dir}"
                )
                continue

            # NEW: Check for Cookies file in Network subdirectory (newer Chrome versions)
            # Also check in the old location (older Chrome versions) as fallback
            cookie_paths_to_check = [
                profile_dir / "Network" / "Cookies",  # New location
                profile_dir / "Cookies",  # Old location
            ]

            cookie_path = None
            for path in cookie_paths_to_check:
                if path.exists():
                    cookie_path = path
                    self.logger.log_debug(f"Found Cookies file at: {path}")
                    break

            # If no Cookies file found in either location
            if cookie_path is None:
                self.logger.log_debug(
                    f"Profile {pattern} exists but no cookies file found in either location"
                )
                # Add to fallback profiles for Chrome installations that haven't been used for browsing
                fallback_profiles.append(
                    {
                        "name": pattern,
                        "cookie_path": str(
                            profile_dir / "Network" / "Cookies"
                        ),  # Use new location as default
                        "cookie_count": 0,
                        "last_modified": 0,
                        "file_size": 0,
                        "fallback": True,
                        "reason": "no_cookies_file",
                    }
                )
                continue

            try:
                # Check cookie file size and modification time
                stat = cookie_path.stat()
                self.logger.log_debug(
                    f"Cookie file stats - size: {stat.st_size}, modified: {stat.st_mtime}"
                )
                if stat.st_size == 0:
                    self.logger.log_debug(f"Empty cookies file in profile: {pattern}")
                    fallback_profiles.append(
                        {
                            "name": pattern,
                            "cookie_path": str(cookie_path),
                            "cookie_count": 0,
                            "last_modified": stat.st_mtime,
                            "file_size": 0,
                            "fallback": True,
                            "reason": "empty_cookies_file",
                        }
                    )
                    continue

                # Count YouTube cookies in this profile
                youtube_cookie_count = self._count_youtube_cookies(str(cookie_path))

                profiles.append(
                    {
                        "name": pattern,
                        "cookie_path": str(
                            cookie_path
                        ),  # Use the actual path where Cookies file was found
                        "cookie_count": youtube_cookie_count,
                        "last_modified": stat.st_mtime,
                        "file_size": stat.st_size,
                    }
                )

                self.logger.log_debug(
                    f"Profile {pattern}: {youtube_cookie_count} YouTube cookies, modified {datetime.fromtimestamp(stat.st_mtime)}"
                )

            except Exception as e:
                self.logger.log_warning(f"Error checking profile {pattern}: {e}")
                continue

        # If we found profiles with actual cookies, use the best one
        if profiles:
            # Sort by YouTube cookie count (descending), then by last modified (descending)
            profiles.sort(
                key=lambda p: (p["cookie_count"], p["last_modified"]), reverse=True
            )
            best_profile = profiles[0]
            self.logger.log_info(
                f"Selected Chrome profile: {best_profile['name']} with {best_profile['cookie_count']} YouTube cookies"
            )
            return best_profile

        # If no profiles with cookies found, use fallback profiles
        if fallback_profiles:
            # Prefer Default profile, then Profile 1, etc.
            fallback_profiles.sort(key=lambda p: (p["name"] != "Default", p["name"]))
            best_fallback = fallback_profiles[0]
            self.logger.log_info(
                f"Using fallback Chrome profile: {best_fallback['name']} (reason: {best_fallback['reason']})"
            )
            return best_fallback

        self.logger.log_error("No Chrome profiles found at all")
        return None

    def _count_youtube_cookies(self, cookie_path: str) -> int:
        """Count YouTube cookies in a Chrome cookie database."""
        try:
            # Check if cookie file is empty
            if os.path.getsize(cookie_path) == 0:
                self.logger.log_warning(f"Chrome cookie file is empty: {cookie_path}")
                return 0

            # Create temporary copy to avoid locking issues
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
            temp_db_path = temp_db.name
            temp_db.close()

            try:
                try:
                    shutil.copy2(cookie_path, temp_db_path)
                except PermissionError:
                    # This typically happens when Chrome is running and has locked the file
                    self.logger.log_warning(
                        f"Permission denied copying Chrome cookies file: {cookie_path}"
                    )
                    self.logger.log_info(
                        "Chrome appears to be running. Please close Chrome completely and try again."
                    )
                    return 0
                except Exception as e:
                    self.logger.log_error(f"Failed to copy Chrome cookies file: {e}")
                    return 0

                conn = None
                try:
                    conn = sqlite3.connect(temp_db_path)
                    cursor = conn.cursor()

                    # Count YouTube cookies
                    query = """
                        SELECT COUNT(*)
                        FROM cookies
                        WHERE host_key LIKE '%youtube.com' OR host_key LIKE '%.youtube.com'
                    """

                    cursor.execute(query)
                    count = cursor.fetchone()[0]
                    return count

                finally:
                    if conn:
                        conn.close()

            finally:
                # Always cleanup temporary file, even on exceptions
                self._cleanup_temp_file(temp_db_path)

        except Exception as e:
            self.logger.log_error(f"Failed to count YouTube cookies: {e}")
            return 0

    def extract_cookies_auto(self, domain: str = "youtube.com") -> str | None:
        """Extract cookies automatically from Chrome with proper cleanup."""
        try:
            # Check cache first (thread-safe)
            cache_key = f"{domain}_auto"
            with self.lock:
                if cache_key in self.cookie_cache:
                    cache_time = self.last_extraction_time.get(cache_key, 0)
                    if time.time() - cache_time < 300:  # 5 minute cache
                        self.logger.log_debug(f"Using cached cookies for {domain}")
                        return self.cookie_cache[cache_key]

            if not self.chrome_info:
                self.logger.log_warning("Chrome not detected for cookie extraction")
                return None

            cookie_path = self.chrome_info["cookie_path"]
            if not os.path.exists(cookie_path):
                self.logger.log_warning(f"Chrome cookie file not found: {cookie_path}")
                return None

            # Check if cookie file is empty
            if os.path.getsize(cookie_path) == 0:
                self.logger.log_warning(f"Chrome cookie file is empty: {cookie_path}")
                self.logger.log_info(
                    "Chrome cookie database exists but is empty - visit some websites in Chrome first"
                )
                return None

            # Create temporary copy of cookie database with proper cleanup
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
            temp_db_path = temp_db.name
            temp_db.close()

            # Track temporary file for cleanup
            with self.lock:
                self._temp_files.add(temp_db_path)

            try:
                try:
                    shutil.copy2(cookie_path, temp_db_path)
                except PermissionError:
                    # This typically happens when Chrome is running and has locked the file
                    self.logger.log_warning(
                        f"Permission denied copying Chrome cookies file: {cookie_path}"
                    )
                    self.logger.log_info(
                        "Chrome appears to be running. Please close Chrome completely and try again."
                    )
                    self.logger.log_info(
                        "Note: Chrome must be fully closed, not just the window minimized."
                    )
                    # Check if Chrome processes are running
                    if self._is_chrome_running():
                        self.logger.log_info(
                            "🔍 DETECTED: Chrome processes are still running!"
                        )
                        self.logger.log_info(
                            "🔧 SOLUTION: Close ALL Chrome windows and check Task Manager to ensure no chrome.exe processes remain"
                        )
                        self.logger.log_info(
                            "⏳ After closing Chrome, wait 10-15 seconds for it to fully terminate"
                        )
                    return None
                except Exception as e:
                    self.logger.log_error(f"Failed to copy Chrome cookies file: {e}")
                    return None

                conn = None
                try:
                    conn = sqlite3.connect(temp_db_path)
                    cursor = conn.cursor()

                    # Query cookies for the domain
                    query = """
                        SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly, encrypted_value
                        FROM cookies
                        WHERE host_key LIKE ? OR host_key LIKE ?
                        ORDER BY creation_utc DESC
                    """

                    cursor.execute(query, (f"%{domain}", f"%.{domain}"))
                    cookies = cursor.fetchall()

                finally:
                    if conn:
                        conn.close()

            finally:
                # Always cleanup temporary file, even on exceptions
                try:
                    if os.path.exists(temp_db_path):
                        os.unlink(temp_db_path)
                        self.logger.log_debug(
                            f"Cleaned up temporary cookie database: {temp_db_path}"
                        )
                except Exception as cleanup_error:
                    self.logger.log_warning(
                        f"Failed to cleanup temporary cookie file {temp_db_path}: {cleanup_error}"
                    )

            if not cookies:
                self.logger.log_warning(f"No cookies found for domain {domain}")
                return None

            self.logger.log_info(f"Found {len(cookies)} cookies for domain {domain}")

            # Format cookies for yt-dlp
            cookie_lines = []
            cookie_lines.append("# Netscape HTTP Cookie File")
            cookie_lines.append("# This is a generated file! Do not edit.")
            cookie_lines.append("")

            valid_cookies = 0
            for cookie in cookies:
                (
                    name,
                    value,
                    host_key,
                    path,
                    expires_utc,
                    is_secure,
                    is_httponly,
                    encrypted_value,
                ) = cookie

                # Decrypt value if encrypted
                if encrypted_value and not value:
                    try:
                        value = self._decrypt_chrome_cookie(encrypted_value)
                    except Exception as e:
                        self.logger.log_warning(f"Failed to decrypt cookie {name}: {e}")
                        continue

                if not value:
                    continue

                # Convert expires_utc to Unix timestamp
                if expires_utc:
                    # Chrome stores time as microseconds since Windows epoch (1601-01-01)
                    # Convert to Unix timestamp
                    expires = (expires_utc / 1000000) - 11644473600
                else:
                    expires = 0

                # Format: domain, domain_specified, path, secure, expires, name, value
                domain_specified = "TRUE" if host_key.startswith(".") else "FALSE"
                secure = "TRUE" if is_secure else "FALSE"

                # Sanitize all fields to prevent format corruption
                host_key_clean = self._sanitize_netscape_field(host_key)
                path_clean = self._sanitize_netscape_field(path)
                name_clean = self._sanitize_netscape_field(name)
                value_clean = self._sanitize_netscape_field(value)

                # Skip if critical fields are empty after sanitization
                if not host_key_clean or not name_clean:
                    continue

                cookie_line = f"{host_key_clean}\t{domain_specified}\t{path_clean}\t{secure}\t{int(expires)}\t{name_clean}\t{value_clean}"
                cookie_lines.append(cookie_line)
                valid_cookies += 1

            if valid_cookies == 0:
                self.logger.log_warning("No valid cookies after decryption")
                return None

            self.logger.log_info(f"Successfully formatted {valid_cookies} cookies")

            # Cache the result (thread-safe)
            result = "\n".join(cookie_lines)
            with self.lock:
                self.cookie_cache[cache_key] = result
                self.last_extraction_time[cache_key] = time.time()

            return result

        except Exception as e:
            raise CookieExtractionError(f"Failed to extract Chrome cookies: {e}") from e

    def _sanitize_netscape_field(self, field_value):
        """
        Enhanced sanitization for Netscape cookie fields with improved Unicode handling
        """
        if field_value is None:
            return ""

        # Convert to string and handle Unicode encoding issues
        field_str = str(field_value)

        # Enhanced Unicode handling - preserve valid UTF-8 characters when possible
        try:
            # First try to normalize Unicode characters
            import unicodedata

            field_str = unicodedata.normalize("NFKC", field_str)
        except Exception:
            pass

        # Handle problematic Unicode characters more gracefully
        try:
            # Try latin-1 encoding first (what yt-dlp expects)
            field_str.encode("latin-1")
        except UnicodeEncodeError:
            try:
                # Remove problematic Unicode characters that can't be encoded in latin-1
                field_str = "".join(char for char in field_str if ord(char) < 256)
            except Exception:
                try:
                    # Fallback to ASCII with replacement
                    field_str = field_str.encode("ascii", errors="replace").decode(
                        "ascii"
                    )
                except Exception:
                    # Last resort - remove non-ASCII
                    field_str = field_str.encode("ascii", errors="ignore").decode(
                        "ascii"
                    )

        # Remove control characters and format-breaking characters
        field_str = field_str.replace("\t", " ")  # Replace tabs with spaces
        field_str = field_str.replace("\n", " ")  # Replace newlines with spaces
        field_str = field_str.replace("\r", " ")  # Replace carriage returns with spaces
        field_str = field_str.replace("\x00", "")  # Remove null bytes
        field_str = field_str.replace("\x0b", " ")  # Replace vertical tabs
        field_str = field_str.replace("\x0c", " ")  # Replace form feeds

        # Remove other control characters (ASCII 0-31 except space)
        field_str = "".join(
            char for char in field_str if ord(char) >= 32 or char == " "
        )

        # Additional validation for cookie-specific requirements
        if len(field_str) > 4096:  # Prevent extremely long cookie values
            field_str = field_str[:4096]
            self.logger.log_warning("Cookie field truncated due to excessive length")

        return field_str.strip()

    def _decrypt_chrome_cookie(self, encrypted_value: bytes) -> str:
        """Decrypt Chrome cookie value using Windows DPAPI with enhanced error handling."""
        if not WIN32CRYPT_AVAILABLE:
            if self.dpapi_failure_count == 0:  # Only log once
                self.logger.log_warning(
                    "Windows DPAPI not available for cookie decryption"
                )
                self.dpapi_failure_count += 1
            return ""

        try:
            if not encrypted_value or len(encrypted_value) < 3:
                return ""

            # Create a hash of the encrypted value to track failed cookies
            cookie_hash = hash(encrypted_value)
            if cookie_hash in self.failed_cookies_cache:
                return ""  # Skip cookies that consistently fail

            # Check if it starts with the encryption prefix
            if encrypted_value[:3] == b"v10":
                # Remove the prefix and decrypt
                encrypted_data = encrypted_value[3:]
                try:
                    decrypted_data = win32crypt.CryptUnprotectData(
                        encrypted_data, None, None, None, 0
                    )
                    return decrypted_data[1].decode("utf-8", errors="ignore")
                except Exception as e:
                    self.dpapi_failure_count += 1
                    self.failed_cookies_cache.add(cookie_hash)

                    # Enhanced logging with better error categorization
                    if self.dpapi_failure_count % self.dpapi_failure_threshold == 0:
                        error_type = (
                            "Invalid data"
                            if "Datos no válidos" in str(e) or "Invalid data" in str(e)
                            else "Unknown error"
                        )
                        self.logger.log_debug(
                            f"DPAPI decryption failed for {self.dpapi_failure_count} cookies (showing every {self.dpapi_failure_threshold}): {error_type} - This is normal for some cookie types"
                        )
                    return ""
            else:
                # Use Windows DPAPI to decrypt (fallback for older format)
                decrypted_data = win32crypt.CryptUnprotectData(
                    encrypted_value, None, None, None, 0
                )
                return decrypted_data[1].decode("utf-8", errors="ignore")
        except Exception as e:
            self.dpapi_failure_count += 1
            cookie_hash = hash(encrypted_value) if encrypted_value else 0
            self.failed_cookies_cache.add(cookie_hash)

            # Enhanced error handling with better categorization
            if (
                self.dpapi_failure_count % (self.dpapi_failure_threshold * 2) == 0
            ):  # Log less frequently
                error_type = (
                    "Invalid data"
                    if "Datos no válidos" in str(e) or "Invalid data" in str(e)
                    else "Decryption error"
                )
                self.logger.log_debug(
                    f"Cookie decryption: {self.dpapi_failure_count} cookies could not be decrypted ({error_type}) - This is expected for some cookie types"
                )

            # Try to decode as plain text (fallback)
            try:
                return encrypted_value.decode("utf-8", errors="ignore")
            except Exception:
                return ""

    def _is_cache_valid(self, cache_key: str, max_age: int = 1800) -> bool:
        """Check if cached cookies are still valid."""
        if cache_key not in self.cookie_cache:
            return False

        if cache_key not in self.last_extraction_time:
            return False

        age = time.time() - self.last_extraction_time[cache_key]
        return age < max_age

    def _validate_cookie_content(self, cookies: str, domain: str) -> bool:
        """Validate cookie content."""
        if not cookies or len(cookies.strip()) < 50:
            return False

        # Check if it contains domain-specific cookies
        if domain not in cookies:
            return False

        # Check if it has proper Netscape format
        if "# Netscape HTTP Cookie File" not in cookies:
            return False

        return True

    def get_cookies_for_ytdlp(self, domain: str = "youtube.com") -> str | None:
        """Get cookies formatted for yt-dlp."""
        return self.extract_cookies_auto(domain)

    def get_cookies_for_ytdlp_enhanced(
        self, preferred_browser=None, use_cookies_from_browser=True
    ):
        """
        Enhanced cookie API that returns structured authentication data
        Returns dict with: source, cookie_file, browser_spec, visitor_data, po_token
        """
        try:
            # 1) Prefer manually imported cookies if available (explicit user choice)
            manual_key = "youtube.com_manual"
            with self.lock:
                manual_cookies = self.cookie_cache.get(manual_key)
            if manual_cookies:
                # Always honor manually imported cookies over any automatic source
                with self.lock:
                    manual_path = self._manual_cookie_file_path
                if manual_path and os.path.exists(manual_path):
                    return {
                        "source": "manual_import",
                        "browser_spec": None,
                        "cookie_file": manual_path,
                        "visitor_data": None,
                        "po_token": None,
                        "user_agent": self._get_default_chrome_user_agent(),
                    }
                else:
                    import tempfile

                    temp_file = tempfile.NamedTemporaryFile(
                        mode="w",
                        suffix=".cookies.txt",
                        delete=False,
                        encoding="utf-8",
                        newline="\n",
                    )
                    # Ensure Netscape header exists
                    stripped = manual_cookies.strip()
                    if not stripped.startswith("# Netscape HTTP Cookie File"):
                        temp_file.write("# Netscape HTTP Cookie File\n")
                        temp_file.write("# This is a generated file! Do not edit.\n\n")
                    temp_file.write(manual_cookies)
                    temp_file.close()
                    with self.lock:
                        self._temp_files.add(temp_file.name)
                    return {
                        "source": "manual_import",
                        "browser_spec": None,
                        "cookie_file": temp_file.name,
                        "visitor_data": None,
                        "po_token": None,
                        "user_agent": self._get_default_chrome_user_agent(),
                    }

            # 2) Use cookies from browser if allowed and available
            if (
                use_cookies_from_browser
                and self.chrome_info
                and self.chrome_info.get("available")
            ):
                profile_path = self.chrome_info.get("profile_path", "")
                if profile_path:
                    # Extract profile name from path
                    profile_name = (
                        os.path.basename(profile_path)
                        if profile_path != self.chrome_info.get("user_data_dir")
                        else None
                    )
                    browser_spec = (
                        f"chrome:{profile_name}" if profile_name else "chrome"
                    )

                    return {
                        "source": "cookies_from_browser",
                        "browser_spec": browser_spec,
                        "cookie_file": None,
                        "visitor_data": None,
                        "po_token": None,
                        "user_agent": self._get_default_chrome_user_agent(),
                    }

            # 3) Fallback to auto-extracted cookies
            cookie_content = self.extract_cookies_auto()
            if cookie_content:
                # Validate it's not JSON
                content_stripped = cookie_content.strip()
                if (
                    content_stripped.startswith("{")
                    or content_stripped.startswith("[")
                    or '"cookies"' in content_stripped
                ):
                    self.logger.log_warning(
                        "Cookie content appears to be JSON format - refusing to use"
                    )
                    return None

                # Create temporary validated Netscape file
                import tempfile

                temp_file = tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".cookies.txt",
                    delete=False,
                    encoding="utf-8",
                    newline="\n",
                )

                # Ensure proper Netscape header
                if not content_stripped.startswith("# Netscape HTTP Cookie File"):
                    temp_file.write("# Netscape HTTP Cookie File\n")
                    temp_file.write("# This is a generated file! Do not edit.\n\n")

                temp_file.write(cookie_content)
                temp_file.close()
                # Track for cleanup
                with self.lock:
                    self._temp_files.add(temp_file.name)

                return {
                    "source": "auto_extracted",
                    "browser_spec": None,
                    "cookie_file": temp_file.name,
                    "visitor_data": None,
                    "po_token": None,
                    "user_agent": self._get_default_chrome_user_agent(),
                }

            return None

        except Exception as e:
            self.logger.log_error(f"Enhanced cookie API failed: {e}")
            return None

    def import_cookie_file(self, file_path: str, domain: str = "youtube.com") -> bool:
        """Import cookies from a file."""
        try:
            if not os.path.exists(file_path):
                self.logger.log_error(f"Cookie file does not exist: {file_path}")
                return False

            with open(file_path, encoding="utf-8") as f:
                cookies = f.read()

            if not cookies or len(cookies.strip()) < 50:
                self.logger.log_error(f"Cookie file is empty or too small: {file_path}")
                return False

            # Validate cookie content
            if not self._validate_cookie_content(cookies, domain):
                self.logger.log_error(f"Cookie file validation failed: {file_path}")
                return False

            # Cache the imported cookies
            cache_key = f"{domain}_manual"
            self.cookie_cache[cache_key] = cookies
            self.last_extraction_time[cache_key] = time.time()

            with self.lock:
                self._manual_cookie_file_path = file_path
            self.logger.log_info(f"Successfully imported cookies from {file_path}")
            return True

        except Exception as e:
            self.logger.log_error(f"Failed to import cookie file {file_path}: {e}")
            return False

    def refresh_browser_detection(self):
        """Refresh Chrome detection."""
        self.logger.log_info("Refreshing Chrome detection...")
        self.chrome_info = self._detect_chrome()

    def _is_domain_problematic(self, domain: str) -> bool:
        """Check if a domain has consistently failed and is in cooldown period."""
        with self.lock:  # Thread-safe access to failed_domains_cache
            if domain not in self.failed_domains_cache:
                return False

            failure_data = self.failed_domains_cache[domain]
            current_time = time.time()

            # Check if cooldown period has expired
            if (
                current_time - failure_data["last_failure"]
                > self.domain_cooldown_period
            ):
                # Reset failure count after cooldown
                del self.failed_domains_cache[domain]
                return False

            # Check if failure threshold exceeded
            return failure_data["count"] >= self.domain_failure_threshold

    def _record_domain_failure(self, domain: str):
        """Record a domain failure for tracking."""
        current_time = time.time()

        with self.lock:  # Thread-safe access to failed_domains_cache
            if domain in self.failed_domains_cache:
                self.failed_domains_cache[domain]["count"] += 1
                self.failed_domains_cache[domain]["last_failure"] = current_time
            else:
                self.failed_domains_cache[domain] = {
                    "count": 1,
                    "last_failure": current_time,
                }

            if (
                self.failed_domains_cache[domain]["count"]
                >= self.domain_failure_threshold
            ):
                self.logger.log_warning(
                    f"Domain {domain} marked as problematic after {self.domain_failure_threshold} failures"
                )

    def should_skip_cookies_for_domain(self, domain: str) -> bool:
        """Public method to check if cookies should be skipped for a domain."""
        return self._is_domain_problematic(domain)

    def record_authentication_failure(self, domain: str):
        """Public method to record authentication failure for a domain."""
        self._record_domain_failure(domain)
        if self.chrome_info:
            self.logger.log_info(f"Chrome re-detected: {self.chrome_info['name']}")
        else:
            self.logger.log_warning("Chrome not found during refresh")

    def clear_cache(self):
        """Clear cookie cache."""
        with self.lock:
            self.cookie_cache.clear()
            self.last_extraction_time.clear()
            self.logger.log_info("Cookie cache cleared")

    def refresh_cookies(self):
        """Refresh cookies from browser - critical method for GUI integration."""
        try:
            self.logger.log_info("Refreshing cookies from browser...")

            # Clear existing cache to force fresh extraction
            self.clear_cache()

            # Refresh Chrome detection
            self.refresh_browser_detection()

            # Test cookie extraction
            if self.chrome_info:
                cookies = self.extract_cookies_auto()
                if cookies:
                    self.logger.log_info("Cookie refresh successful")
                    return True
                else:
                    self.logger.log_warning(
                        "Cookie refresh failed - no cookies extracted"
                    )
                    return False
            else:
                self.logger.log_warning("Cookie refresh failed - Chrome not detected")
                return False

        except Exception as e:
            self.logger.log_error(f"Cookie refresh failed: {e}")
            return False

    def get_cookie_status(self) -> str:
        """Get current cookie status - critical method for GUI integration."""
        try:
            if not self.chrome_info:
                return "Chrome not detected"

            # Check if Chrome is running
            if self.is_chrome_running():
                status = "Chrome running - cookies may be locked"
            else:
                status = "Chrome not running - cookies accessible"

            # Check cookie availability
            cookies = self.extract_cookies_auto()
            if cookies:
                # Count cookies for status
                cookie_lines = [
                    line
                    for line in cookies.split("\n")
                    if line.strip() and not line.startswith("#")
                ]
                cookie_count = len(cookie_lines)
                status += f" - {cookie_count} cookies available"
            else:
                status += " - no cookies available"

            return status

        except Exception as e:
            self.logger.log_error(f"Failed to get cookie status: {e}")
            return f"Error: {str(e)}"

    def get_available_browsers(self) -> list[str]:
        """Get list of available browsers - for GUI browser selection."""
        browsers = []

        if self.chrome_info:
            browsers.append("Chrome")

        # Could add other browsers here in the future
        # For now, only Chrome is supported

        return browsers

    def import_cookies_from_file(self, file_path: str) -> bool:
        """Import cookies from file - wrapper for GUI compatibility."""
        return self.import_cookie_file(file_path)

    def is_chrome_running(self) -> bool:
        """Public method to check if Chrome is currently running."""
        return self._is_chrome_running()

    def _cleanup_temp_file(self, file_path: str):
        """Clean up a single temporary file safely."""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                self.logger.log_debug(f"Cleaned up temporary file: {file_path}")

            # Remove from tracking set
            with self.lock:
                self._temp_files.discard(file_path)

        except Exception as cleanup_error:
            self.logger.log_warning(
                f"Failed to cleanup temporary file {file_path}: {cleanup_error}"
            )

    def cleanup_all_temp_files(self):
        """Clean up all tracked temporary files."""
        with self.lock:
            temp_files_copy = self._temp_files.copy()

        for temp_file in temp_files_copy:
            self._cleanup_temp_file(temp_file)

        self.logger.log_info(f"Cleaned up {len(temp_files_copy)} temporary files")

    def shutdown(self):
        """Shutdown the cookie manager and clean up resources."""
        if self._is_shutdown:
            return

        self.logger.log_info("Shutting down cookie manager...")
        self._is_shutdown = True

        # Clean up all temporary files
        self.cleanup_all_temp_files()

        # Clear caches
        with self.lock:
            self.cookie_cache.clear()
            self.last_extraction_time.clear()
            self.failed_cookies_cache.clear()
            self.failed_domains_cache.clear()

        self.logger.log_info("Cookie manager shutdown complete")

    def __del__(self):
        """Destructor to ensure cleanup on garbage collection."""
        try:
            if not self._is_shutdown:
                self.shutdown()
        except Exception:
            pass  # Ignore errors during destruction

    def _is_chrome_running(self) -> bool:
        """Check if Chrome processes are currently running with timeout protection."""
        try:
            # Use psutil to check for Chrome processes with timeout
            import psutil

            def timeout_handler(signum, frame):
                raise TimeoutError("Chrome detection timed out")

            # Set up timeout for Windows (use threading approach since signal doesn't work well on Windows)
            import threading

            result = [False]  # Use list to allow modification in nested function
            exception_occurred = [False]

            def check_processes():
                try:
                    for process in psutil.process_iter(["name"]):
                        try:
                            if (
                                process.info["name"]
                                and "chrome.exe" in process.info["name"].lower()
                            ):
                                result[0] = True
                                return
                        except (
                            psutil.NoSuchProcess,
                            psutil.AccessDenied,
                            psutil.ZombieProcess,
                        ):
                            pass
                except Exception:
                    exception_occurred[0] = True

            # Run process check with 3-second timeout
            thread = threading.Thread(target=check_processes, daemon=True)
            thread.start()
            thread.join(timeout=3.0)

            if thread.is_alive():
                self.logger.log_warning(
                    "Chrome process detection timed out after 3 seconds"
                )
                return False

            if exception_occurred[0]:
                raise Exception("Process enumeration failed")

            return result[0]

        except ImportError:
            # Fallback method using tasklist with timeout
            try:
                result = subprocess.run(
                    ["tasklist"], capture_output=True, text=True, check=True, timeout=5
                )
                return "chrome.exe" in result.stdout.lower()
            except subprocess.TimeoutExpired:
                self.logger.log_warning("Tasklist command timed out after 5 seconds")
                return False
            except Exception:
                return False
        except Exception as e:
            self.logger.log_warning(f"Chrome detection failed: {e}")
            return False


# Global instance
_cookie_manager_instance = None


def get_cookie_manager() -> CookieManager:
    """Get global cookie manager instance."""
    global _cookie_manager_instance
    if _cookie_manager_instance is None:
        _cookie_manager_instance = CookieManager()
    return _cookie_manager_instance
