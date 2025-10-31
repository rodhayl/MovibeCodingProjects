#!/usr/bin/env python3
"""
Simplified Logging System for Video Downloader
Uses standard Python logging with basic functionality.
"""

import logging
import os
import sys
from collections.abc import Callable
from contextlib import contextmanager


class AppLogger:
    """Simplified logger using standard Python logging"""

    _instance = None
    _lock = None

    def __init__(self):
        if AppLogger._instance is not None:
            raise Exception("This class is a singleton!")

        # Set up basic logging
        self.logger = logging.getLogger("VideoDownloader")
        self.logger.setLevel(logging.DEBUG)

        # Create console handler if not exists
        if not self.logger.handlers:
            # Set up console handler with UTF-8 encoding support
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)

            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)8s] %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console_handler.setFormatter(formatter)

            self.logger.addHandler(console_handler)

            # Add file handler for errors with UTF-8 encoding
            try:
                log_dir = os.path.join(os.path.dirname(__file__), "logs")
                os.makedirs(log_dir, exist_ok=True)

                file_handler = logging.FileHandler(
                    os.path.join(log_dir, "video_downloader.log"), encoding="utf-8"
                )
                file_handler.setLevel(logging.WARNING)
                file_handler.setFormatter(formatter)

                self.logger.addHandler(file_handler)
            except Exception:
                # If file logging fails, continue with console only
                pass

    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            if cls._lock is None:
                import threading

                cls._lock = threading.Lock()

            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _sanitize_message(self, message: str) -> str:
        """Sanitize message to prevent Unicode encoding errors"""
        try:
            # Replace problematic Unicode characters with safe alternatives
            message = message.replace("⚠️", "[WARNING]")
            message = message.replace("✅", "[OK]")
            message = message.replace("❌", "[ERROR]")
            message = message.replace("🎉", "[SUCCESS]")
            message = message.replace("🔍", "[SEARCH]")
            message = message.replace("📋", "[INFO]")
            message = message.replace("🍪", "[COOKIE]")
            # Encode to ASCII with error handling, then decode back
            return message.encode("ascii", errors="replace").decode("ascii")
        except Exception:
            # Fallback: remove all non-ASCII characters
            return "".join(char for char in message if ord(char) < 128)

    def log_debug(self, message: str, extra_data: dict | None = None) -> None:
        """Log debug message"""
        message = self._sanitize_message(message)
        if extra_data:
            message = f"{message} - {extra_data}"
        self.logger.debug(message)

    def log_info(self, message: str, extra_data: dict | None = None) -> None:
        """Log info message"""
        message = self._sanitize_message(message)
        if extra_data:
            message = f"{message} - {extra_data}"
        self.logger.info(message)

    def log_warning(self, message: str, extra_data: dict | None = None) -> None:
        """Log warning message"""
        message = self._sanitize_message(message)
        if extra_data:
            message = f"{message} - {extra_data}"
        self.logger.warning(message)

    def log_error(
        self,
        message: str,
        extra_data: dict | None = None,
        exception: Exception = None,
    ) -> None:
        """Log error message"""
        message = self._sanitize_message(message)
        if extra_data:
            message = f"{message} - {extra_data}"
        if exception:
            message = f"{message} - Exception: {str(exception)}"
        self.logger.error(message)
        if exception:
            self.logger.debug("Exception details:", exc_info=True)

    def log_critical(
        self,
        message: str,
        extra_data: dict | None = None,
        exception: Exception = None,
    ) -> None:
        """Log critical message"""
        if extra_data:
            message = f"{message} - {extra_data}"
        if exception:
            message = f"{message} - Exception: {str(exception)}"
        self.logger.critical(message)
        if exception:
            self.logger.debug("Exception details:", exc_info=True)

    def log_performance(
        self, message: str, execution_time: float, extra_data: dict | None = None
    ) -> None:
        """Log performance metrics"""
        perf_message = f"PERFORMANCE: {message} (took {execution_time:.3f}s)"
        if extra_data:
            perf_message = f"{perf_message} - {extra_data}"
        self.logger.info(perf_message)

    def shutdown(self) -> None:
        """Shutdown the logger"""
        self.logger.info("Logger shutting down")
        # Close all handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

    def new_correlation_id(self) -> str:
        """Generate a simple correlation ID for backward compatibility"""
        import uuid

        return str(uuid.uuid4())[:8]

    def start_operation_monitoring(
        self, operation_id: str, timeout: float = None
    ) -> None:
        """Simplified operation monitoring - does nothing"""
        pass

    def end_operation_monitoring(self, operation_id: str) -> None:
        """Simplified operation monitoring - does nothing"""
        pass


def log_function_calls(timeout: float | None = None, monitor_performance: bool = True):
    """Simplified decorator - just returns the function unchanged"""

    def decorator(func: Callable) -> Callable:
        # Simply return the function without any logging overhead
        return func

    return decorator


@contextmanager
def log_operation(
    operation_name: str,
    timeout: float | None = None,
    extra_data: dict | None = None,
):
    """Simplified context manager - just yields operation name"""
    try:
        yield operation_name
    except Exception:
        # Re-raise without logging overhead
        raise


# Initialize logger on import
logger = AppLogger.get_instance()
