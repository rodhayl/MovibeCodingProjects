#!/usr/bin/env python3
"""
YouTube Video Downloader - CustomTkinter Version

A modern video downloader application with CustomTkinter GUI.
This version replaces PyQt5 with CustomTkinter while preserving all functionality.
"""

import platform
import sys
import traceback

from app_logger import AppLogger, log_function_calls
from gui.main_window import VideoDownloaderApp


@log_function_calls(timeout=60.0)
def main():
    """Main application entry point"""
    logger = AppLogger.get_instance()

    try:
        logger.log_info(
            "Starting Video Downloader application (CustomTkinter version)",
            extra_data={"python_version": sys.version, "platform": platform.platform()},
        )

        # Create and run CustomTkinter application
        app = VideoDownloaderApp()

        logger.log_info("CustomTkinter Application created successfully")

        # Set up exception handling
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            logger.log_critical(
                f"Uncaught exception: {exc_type.__name__}: {exc_value}",
                extra_data={
                    "exception_type": exc_type.__name__,
                    "exception_value": str(exc_value),
                    "traceback": "".join(traceback.format_tb(exc_traceback)),
                },
            )

        sys.excepthook = handle_exception

        try:
            logger.log_info("Application window created, entering main event loop")

            # Start the CustomTkinter main loop
            app.mainloop()

            logger.log_info("Application exited normally")
            return 0

        except Exception as e:
            logger.log_critical("Failed to run CustomTkinter application", exception=e)
            return 1

    except Exception as e:
        # Fallback logging if logger fails
        print(f"Critical error in main: {e}")
        traceback.print_exc()
        return 1
    finally:
        # Shutdown logger
        try:
            logger.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
