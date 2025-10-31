#!/usr/bin/env python3
"""
CustomTkinter GUI Implementation for Video Downloader

This module contains the main application window and all GUI components
using CustomTkinter instead of PyQt5.
"""

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk


# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import business logic
from app_logger import AppLogger
from cookie_manager import get_cookie_manager
from download_threads import DownloadThread
from playlist_downloader import PlaylistDownloader

# Import utility functions from utils module
from utils import (
    check_ffmpeg,
    clean_url_for_video_info,
    get_downloads_folder,
    normalize_playlist_url,
)


# DownloadWorker class removed - now using real DownloadThread from download_threads.py


class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize logger
        self.logger = AppLogger.get_instance()
        self.logger.log_info("Initializing CustomTkinter Video Downloader application")

        # Initialize widget state tracking
        self._destroyed = False

        # Initialize data structures
        self.formats = []
        self.video_formats = []
        self.audio_formats = []
        # Store format mappings: display_string -> format_id
        self.format_id_map = {}
        self.video_format_id_map = {}
        self.audio_format_id_map = {}
        self.playlist_info = None
        self.current_video_url = None
        self.current_video_info = None

        # Separate downloaders for complete isolation
        self.single_video_downloader = None
        self.playlist_downloader = None

        # Initialize cookie management
        try:
            self.cookie_manager = get_cookie_manager()
            self.logger.log_info("Cookie management system initialized")
        except Exception as e:
            self.logger.log_error("Failed to initialize cookie management", exception=e)
            self.cookie_manager = None

        # Initialize GUI update queue for thread communication
        self.update_queue = queue.Queue()

        # Setup GUI
        self.setup_window()
        self.setup_variables()
        self.setup_ui()

        # Start queue processing
        self.process_queue()

        # Check FFmpeg on startup (delayed to avoid conflicts)
        self.after(100, self.check_ffmpeg_on_startup)

        # Initialize cookie status and browser detection (delayed to avoid conflicts)
        self.after(200, self.initialize_cookie_system)

        # Initialize format combos after GUI is fully set up (delayed to ensure components exist)
        self.after(50, self.initialize_format_combos)

    def setup_window(self):
        """Configure main window properties"""
        self.title("Video Downloader")
        self.geometry(
            "1400x1000"
        )  # Increased size to ensure all UI elements are visible

        # Configure grid weights for responsive layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Set appearance mode and color theme
        ctk.set_appearance_mode("system")  # Modes: system, light, dark
        ctk.set_default_color_theme("blue")  # Themes: blue, green, dark-blue

    def setup_ui(self):
        """Create and arrange all GUI components"""
        # Create main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Create tabview
        self.tabview = ctk.CTkTabview(self.main_container, command=self.on_tab_change)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Add tabs
        self.single_video_tab = self.tabview.add("Single Video")
        self.playlist_tab = self.tabview.add("Playlist")

        # Track current tab for URL transfer
        self.current_tab = "Single Video"

        # Setup tab contents
        self.setup_single_video_tab()
        self.setup_playlist_tab()

    def setup_variables(self):
        """Initialize tkinter variables"""
        # Single video variables
        self.url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=get_downloads_folder())
        self.format_mode_var = tk.StringVar(value="Automatic")

        # Playlist variables
        self.playlist_url_var = tk.StringVar()
        self.playlist_output_dir_var = tk.StringVar(value=get_downloads_folder())
        self.playlist_format_mode_var = tk.StringVar(value="Automatic")

        # Status variables
        self.status_var = tk.StringVar()
        self.playlist_status_var = tk.StringVar()
        self.cookie_status_var = (
            tk.StringVar()
        )  # Dynamic status - initialized by initialize_cookie_system

        # Cookie operation state tracking
        self.cookie_operation_in_progress = False

    def initialize_format_combos(self):
        """Initialize format combo boxes with default values for Automatic mode"""
        # Set default values for format combos in Automatic mode
        self.format_combo.configure(values=["Best Video and Best Audio"])
        self.format_combo.set("Best Video and Best Audio")

        self.playlist_format_combo.configure(values=["Best Video and Best Audio"])
        self.playlist_format_combo.set("Best Video and Best Audio")

    def setup_single_video_tab(self):
        """Setup single video tab layout and components"""
        # Configure grid weights
        self.single_video_tab.grid_columnconfigure(0, weight=1)

        row = 0

        # URL Input Section
        url_frame = ctk.CTkFrame(self.single_video_tab)
        url_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        url_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(url_frame, text="URL:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.url_entry = ctk.CTkEntry(
            url_frame,
            textvariable=self.url_var,
            placeholder_text="Enter YouTube, Vimeo, or other supported video URL",
        )
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        row += 1

        # Control Buttons
        button_frame = ctk.CTkFrame(self.single_video_tab)
        button_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)

        self.get_info_btn = ctk.CTkButton(
            button_frame, text="Get Video Info", command=self.get_video_info
        )
        self.get_info_btn.grid(row=0, column=0, padx=5, pady=5)

        row += 1

        # Format Selection Mode
        format_mode_frame = ctk.CTkFrame(self.single_video_tab)
        format_mode_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        format_mode_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(format_mode_frame, text="Format Selection Mode:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )

        self.format_mode_combo = ctk.CTkComboBox(
            format_mode_frame,
            values=["Automatic", "Manual"],
            variable=self.format_mode_var,
            command=self.toggle_format_mode,
            state="readonly",
        )
        self.format_mode_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        row += 1

        # Automatic Format Selection
        self.auto_format_frame = ctk.CTkFrame(self.single_video_tab)
        self.auto_format_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        self.auto_format_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.auto_format_frame, text="Format:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.format_combo = ctk.CTkComboBox(
            self.auto_format_frame, values=["Best Video and Best Audio"]
        )
        self.format_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        # Set default value and then disable
        self.format_combo.set("Best Video and Best Audio")
        self.format_combo.configure(state="disabled")

        row += 1

        # Manual Format Selection
        self.manual_format_frame = ctk.CTkFrame(self.single_video_tab)
        self.manual_format_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        self.manual_format_frame.grid_columnconfigure(1, weight=1)
        self.manual_format_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(self.manual_format_frame, text="Video Format:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.video_format_combo = ctk.CTkComboBox(
            self.manual_format_frame, state="readonly"
        )
        self.video_format_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(self.manual_format_frame, text="Audio Format:").grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.audio_format_combo = ctk.CTkComboBox(
            self.manual_format_frame, state="readonly"
        )
        self.audio_format_combo.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Initially hide manual format selection
        self.manual_format_frame.grid_remove()

        row += 1

        # Cookie Management Section
        self.setup_cookie_management_section(self.single_video_tab, row)
        row += 1

        # Output Directory
        output_frame = ctk.CTkFrame(self.single_video_tab)
        output_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        output_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(output_frame, text="Output Directory:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.output_entry = ctk.CTkEntry(output_frame, textvariable=self.output_dir_var)
        self.output_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.browse_btn = ctk.CTkButton(
            output_frame, text="Browse", command=self.browse_directory
        )
        self.browse_btn.grid(row=0, column=2, padx=5, pady=5)

        row += 1

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self.single_video_tab)
        self.progress_bar.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        self.progress_bar.set(0)

        row += 1

        # Download Button
        self.download_btn = ctk.CTkButton(
            self.single_video_tab,
            text="Download",
            command=self.start_download,
            state="disabled",
        )
        self.download_btn.grid(row=row, column=0, padx=10, pady=5)

        row += 1

        # Status Label
        self.status_label = ctk.CTkLabel(
            self.single_video_tab, textvariable=self.status_var
        )
        self.status_label.grid(row=row, column=0, padx=10, pady=5)

    def setup_cookie_management_section(self, parent, row):
        """Setup cookie management UI section"""
        cookie_frame = ctk.CTkFrame(parent)
        cookie_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        cookie_frame.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(cookie_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(
            header_frame,
            text="Authentication & Cookie Management:",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.cookie_help_btn = ctk.CTkButton(
            header_frame, text="?", width=30, height=30, command=self.show_cookie_help
        )
        self.cookie_help_btn.grid(row=0, column=1, padx=5, pady=5)

        # Status
        status_frame = ctk.CTkFrame(cookie_frame)
        status_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        self.cookie_status_label = ctk.CTkLabel(
            status_frame, textvariable=self.cookie_status_var, text_color="orange"
        )
        self.cookie_status_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Controls
        controls_frame = ctk.CTkFrame(cookie_frame)
        controls_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.refresh_cookies_btn = ctk.CTkButton(
            controls_frame,
            text="Auto-Refresh Cookies",
            command=self.refresh_cookies_enhanced,
        )
        self.refresh_cookies_btn.grid(row=0, column=0, padx=5, pady=5)

        self.import_cookies_btn = ctk.CTkButton(
            controls_frame,
            text="Import Cookie File",
            command=self.import_cookie_file_enhanced,
        )
        self.import_cookies_btn.grid(row=0, column=1, padx=5, pady=5)

        self.cookie_export_help_btn = ctk.CTkButton(
            controls_frame,
            text="Get cookies.txt ?",
            command=self.show_cookie_export_help,
        )
        self.cookie_export_help_btn.grid(row=0, column=2, padx=5, pady=5)

        # Browser Selection
        browser_frame = ctk.CTkFrame(cookie_frame)
        browser_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        browser_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(browser_frame, text="Browser:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )

        self.browser_combo = ctk.CTkComboBox(
            browser_frame, values=["Auto-detect (Recommended)"], state="readonly"
        )
        self.browser_combo.set("Auto-detect (Recommended)")  # Set default value
        self.browser_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.browser_refresh_btn = ctk.CTkButton(
            browser_frame, text="🔄", width=30, command=self.refresh_browser_detection
        )
        self.browser_refresh_btn.grid(row=0, column=2, padx=5, pady=5)

        # Add tooltip for browser refresh button
        self._create_tooltip(
            self.browser_refresh_btn,
            "Refresh browser detection and update cookie status",
        )

    def setup_playlist_tab(self):
        """Setup playlist tab layout and components"""
        self.playlist_tab.grid_columnconfigure(0, weight=1)

        row = 0

        # URL Input
        url_frame = ctk.CTkFrame(self.playlist_tab)
        url_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        url_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(url_frame, text="URL:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.playlist_url_entry = ctk.CTkEntry(
            url_frame,
            textvariable=self.playlist_url_var,
            placeholder_text="Enter YouTube playlist URL",
        )
        self.playlist_url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        row += 1

        # Get Playlist Info Button
        self.get_playlist_btn = ctk.CTkButton(
            self.playlist_tab, text="Get Playlist Info", command=self.get_playlist_info
        )
        self.get_playlist_btn.grid(row=row, column=0, padx=10, pady=5)

        row += 1

        # Playlist Info Display
        self.playlist_info_label = ctk.CTkLabel(self.playlist_tab, text="")
        self.playlist_info_label.grid(row=row, column=0, padx=10, pady=5)

        row += 1

        # Video Selection Table
        table_frame = ctk.CTkFrame(self.playlist_tab)
        table_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        table_frame.grid_columnconfigure(0, weight=1)

        # Create Treeview for video selection with dark theme styling
        style = ttk.Style()
        
        # Configure dark theme colors for Treeview
        style.theme_use('default')
        style.configure(
            "Playlist.Treeview",
            background="#2b2b2b",  # Dark background
            foreground="white",  # White text
            fieldbackground="#2b2b2b",  # Dark field background
            font=("TkDefaultFont", 21),
            rowheight=50
        )
        style.configure(
            "Playlist.Treeview.Heading",
            background="#1f538d",  # CustomTkinter blue for headers
            foreground="white",
            font=("TkDefaultFont", 21, "bold")
        )
        
        # Configure selection colors
        style.map(
            "Playlist.Treeview",
            background=[("selected", "#1f538d")],  # Blue when selected
            foreground=[("selected", "white")]
        )

        self.video_tree = ttk.Treeview(
            table_frame,
            columns=("Select", "Title", "Duration", "Status"),
            show="headings",
            height=10,
            style="Playlist.Treeview",
        )

        # Configure columns with adjusted widths for larger font
        self.video_tree.heading("Select", text="Select")
        self.video_tree.heading("Title", text="Title")
        self.video_tree.heading("Duration", text="Duration")
        self.video_tree.heading("Status", text="Status")

        self.video_tree.column("Select", width=120, minwidth=120, anchor="center")
        self.video_tree.column("Title", width=600, minwidth=400, anchor="center")
        self.video_tree.column("Duration", width=150, minwidth=150, anchor="center")
        self.video_tree.column("Status", width=180, minwidth=180, anchor="center")

        # Initialize video selection state tracking
        self.video_selection_state = {}
        # Map tree item_id -> {url,title,duration}
        self.playlist_item_data = {}

        # Bind click events for checkbox functionality
        self.video_tree.bind("<Button-1>", self._on_video_tree_click)
        self.video_tree.bind("<space>", self._on_video_tree_space)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.video_tree.yview
        )
        self.video_tree.configure(yscrollcommand=scrollbar.set)

        self.video_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=5)

        table_frame.grid_rowconfigure(0, weight=1)

        # Add selection control buttons
        selection_frame = ctk.CTkFrame(self.playlist_tab)
        selection_frame.grid(row=row + 1, column=0, sticky="ew", padx=10, pady=5)

        self.select_all_btn = ctk.CTkButton(
            selection_frame,
            text="Select All",
            command=self._select_all_videos,
            width=100,
        )
        self.select_all_btn.grid(row=0, column=0, padx=5, pady=5)

        self.deselect_all_btn = ctk.CTkButton(
            selection_frame,
            text="Deselect All",
            command=self._deselect_all_videos,
            width=100,
        )
        self.deselect_all_btn.grid(row=0, column=1, padx=5, pady=5)

        row += 2  # Account for selection buttons

        # Format Selection (similar to single video)
        self.setup_playlist_format_selection(row)
        row += 2  # Format selection takes 2 rows

        # Output Directory
        output_frame = ctk.CTkFrame(self.playlist_tab)
        output_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        output_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(output_frame, text="Output Directory:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.playlist_output_entry = ctk.CTkEntry(
            output_frame, textvariable=self.playlist_output_dir_var
        )
        self.playlist_output_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.playlist_browse_btn = ctk.CTkButton(
            output_frame, text="Browse", command=self.browse_playlist_directory
        )
        self.playlist_browse_btn.grid(row=0, column=2, padx=5, pady=5)

        row += 1

        # Progress Bars
        self.playlist_progress_bar = ctk.CTkProgressBar(self.playlist_tab)
        self.playlist_progress_bar.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        self.playlist_progress_bar.set(0)

        row += 1

        self.current_video_progress_bar = ctk.CTkProgressBar(self.playlist_tab)
        self.current_video_progress_bar.grid(
            row=row, column=0, sticky="ew", padx=10, pady=5
        )
        self.current_video_progress_bar.set(0)

        row += 1

        # Download/Cancel Buttons
        button_frame = ctk.CTkFrame(self.playlist_tab)
        button_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)

        self.playlist_download_btn = ctk.CTkButton(
            button_frame,
            text="Download Playlist",
            command=self.start_playlist_download,
            state="disabled",
        )
        self.playlist_download_btn.grid(row=0, column=0, padx=5, pady=5)

        self.playlist_cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel_playlist_download,
            state="disabled",
        )
        self.playlist_cancel_btn.grid(row=0, column=1, padx=5, pady=5)

        row += 1

        # Status Label
        self.playlist_status_label = ctk.CTkLabel(
            self.playlist_tab, textvariable=self.playlist_status_var
        )
        self.playlist_status_label.grid(row=row, column=0, padx=10, pady=5)

    def setup_playlist_format_selection(self, row):
        """Setup playlist format selection components"""
        # Format Selection Mode
        format_mode_frame = ctk.CTkFrame(self.playlist_tab)
        format_mode_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        format_mode_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(format_mode_frame, text="Format Selection Mode:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )

        self.playlist_format_mode_combo = ctk.CTkComboBox(
            format_mode_frame,
            values=["Automatic", "Manual"],
            variable=self.playlist_format_mode_var,
            command=self.toggle_playlist_format_mode,
            state="readonly",
        )
        self.playlist_format_mode_combo.grid(
            row=0, column=1, padx=5, pady=5, sticky="ew"
        )

        row += 1

        # Automatic Format Selection
        self.playlist_auto_format_frame = ctk.CTkFrame(self.playlist_tab)
        self.playlist_auto_format_frame.grid(
            row=row, column=0, sticky="ew", padx=10, pady=5
        )
        self.playlist_auto_format_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.playlist_auto_format_frame, text="Format:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.playlist_format_combo = ctk.CTkComboBox(
            self.playlist_auto_format_frame, values=["Best Video and Best Audio"]
        )
        self.playlist_format_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        # Set default value and then disable
        self.playlist_format_combo.set("Best Video and Best Audio")
        self.playlist_format_combo.configure(state="disabled")

        # Manual Format Selection
        self.playlist_manual_format_frame = ctk.CTkFrame(self.playlist_tab)
        self.playlist_manual_format_frame.grid(
            row=row, column=0, sticky="ew", padx=10, pady=5
        )
        self.playlist_manual_format_frame.grid_columnconfigure(1, weight=1)
        self.playlist_manual_format_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(self.playlist_manual_format_frame, text="Video Format:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.playlist_video_format_combo = ctk.CTkComboBox(
            self.playlist_manual_format_frame, state="readonly"
        )
        self.playlist_video_format_combo.grid(
            row=0, column=1, padx=5, pady=5, sticky="ew"
        )

        ctk.CTkLabel(self.playlist_manual_format_frame, text="Audio Format:").grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.playlist_audio_format_combo = ctk.CTkComboBox(
            self.playlist_manual_format_frame, state="readonly"
        )
        self.playlist_audio_format_combo.grid(
            row=0, column=3, padx=5, pady=5, sticky="ew"
        )

        # Initially hide manual format selection
        self.playlist_manual_format_frame.grid_remove()

    def _populate_playlist_manual_formats(self):
        """Populate playlist manual format combos with descriptive display strings.

        Uses the first playlist entry to extract real format IDs and presents
        them as human-friendly options (e.g., "1080p mp4" or "128k m4a").
        Falls back to generic selectors when extraction is not available.
        """
        # Collect a sample URL from the first playlist item
        sample_url = None
        try:
            for item_id in self.video_tree.get_children():
                data = getattr(self, "playlist_item_data", {}).get(item_id)
                if data and data.get("url"):
                    sample_url = data["url"]
                    break
        except Exception:
            pass

        # Reset mapping dicts
        self.playlist_video_format_id_map = {}
        self.playlist_audio_format_id_map = {}

        video_values = []  # display strings
        audio_values = []  # display strings

        if sample_url:
            try:
                import yt_dlp

                with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                    info = ydl.extract_info(sample_url, download=False)
                if info and "formats" in info:
                    for fmt in info["formats"]:
                        fid = fmt.get("format_id", "")
                        ext = fmt.get("ext", "")
                        vcodec = fmt.get("vcodec", "none")
                        acodec = fmt.get("acodec", "none")
                        height = fmt.get("height")
                        abr = fmt.get("abr")

                        # Build descriptive display strings mirroring single video UX
                        if vcodec != "none" and acodec == "none":
                            quality = f"{int(height)}p" if height else "unknown"
                            display = f"{quality} {ext}".strip()
                            video_values.append(display)
                            self.playlist_video_format_id_map[display] = fid
                        elif vcodec == "none" and acodec != "none":
                            bitrate = f"{int(abr)}k" if abr else "unknown"
                            display = f"{bitrate} {ext}".strip()
                            audio_values.append(display)
                            self.playlist_audio_format_id_map[display] = fid
            except Exception:
                # Ignore extraction errors and use generic selectors below
                pass

        # If extraction failed or lists are empty, use generic values
        if not video_values:
            # Generic selectors as display and id mapping to themselves
            generic_video = [
                "bestvideo",
                "bestvideo[height<=1080]",
                "bestvideo[height<=720]",
                "bestvideo[height<=480]",
            ]
            video_values = generic_video
            for g in generic_video:
                self.playlist_video_format_id_map[g] = g
        if not audio_values:
            generic_audio = [
                "bestaudio",
                "bestaudio[abr<=160]",
                "bestaudio[abr<=128]",
            ]
            audio_values = generic_audio
            for g in generic_audio:
                self.playlist_audio_format_id_map[g] = g

        try:
            self.playlist_video_format_combo.configure(values=video_values)
            self.playlist_audio_format_combo.configure(values=audio_values)
            # Keep previous selection if possible; otherwise pick first
            prev_v = None
            prev_a = None
            try:
                prev_v = self.playlist_video_format_combo.get()
                prev_a = self.playlist_audio_format_combo.get()
            except Exception:
                pass
            self.playlist_video_format_combo.set(
                prev_v if prev_v in video_values else video_values[0]
            )
            self.playlist_audio_format_combo.set(
                prev_a if prev_a in audio_values else audio_values[0]
            )
        except Exception:
            pass

    def destroy(self):
        """Override destroy to prevent callback errors and clean up resources"""
        self._destroyed = True

        # Clean up resources
        try:
            # Cancel any running download threads
            if hasattr(self, "download_worker") and self.download_worker:
                self.download_worker.cancel()

            # Clean up cookie manager resources
            if hasattr(self, "cookie_manager") and self.cookie_manager:
                self.cookie_manager.cleanup_all_temp_files()

            # Clear queue to prevent memory leaks
            if hasattr(self, "update_queue"):
                try:
                    while True:
                        self.update_queue.get_nowait()
                except queue.Empty:
                    pass

        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.log_warning(f"Error during cleanup: {e}")

        try:
            super().destroy()
        except tk.TclError:
            pass

    def process_queue(self):
        """Process GUI update queue for thread communication"""
        if self._destroyed:
            return

        try:
            while True:
                message = self.update_queue.get_nowait()
                self.handle_queue_message(message)
        except queue.Empty:
            pass

        # Schedule next check
        self.after(100, self.process_queue)

    def handle_queue_message(self, message):
        """Handle messages from background threads"""
        msg_type = message.get("type")

        if msg_type == "progress":
            self.update_progress(message["value"])
        elif msg_type == "status":
            self.update_status(message["text"])
        elif msg_type == "error":
            error_record = message.get("error_record")
            self.show_error(message["text"], error_record)
        elif msg_type == "finished":
            self.download_finished(message["text"])
        elif msg_type == "video_info_success":
            self.handle_video_info_success(message)
        elif msg_type == "enable_button":
            self.enable_button(message["button"])
        # Playlist-specific message types
        elif msg_type == "playlist_progress":
            self.update_playlist_progress(message["value"])
        elif msg_type == "playlist_video_progress":
            self.update_current_video_progress(message["value"])
        elif msg_type == "video_progress":
            self.update_video_progress(message["video_id"], message["progress"])
        elif msg_type == "video_status":
            self.update_video_status(message["video_id"], message["status"])
        elif msg_type == "playlist_status":
            self.update_playlist_status(message["text"])
        elif msg_type == "playlist_finished":
            self.playlist_download_finished(message["text"])
        elif msg_type == "playlist_error":
            self.playlist_download_error(message["text"])
        elif msg_type == "playlist_video_finished":
            self.handle_playlist_video_finished(message["text"])
        elif msg_type == "playlist_video_error":
            self.handle_playlist_video_error(message["text"])

    def update_progress(self, value):
        """Update progress bar for single video downloads"""
        # Update main progress bar for single video downloads
        self.progress_bar.set(value / 100.0)

    def update_status(self, text):
        """Update status label"""
        self.status_var.set(text)

    def update_playlist_progress(self, value):
        """Update playlist overall progress bar"""
        self.playlist_progress_bar.set(value / 100.0)

    def update_current_video_progress(self, value):
        """Update current video progress bar for playlist downloads"""
        self.current_video_progress_bar.set(value / 100.0)

    def update_video_progress(self, video_id, progress):
        """Update current video progress bar"""
        self.current_video_progress_bar.set(progress / 100.0)

    def update_video_status(self, video_id, status):
        """Update individual video status in the tree"""
        # Find the tree item for this video
        for item_id in self.video_tree.get_children():
            if video_id in item_id:
                values = list(self.video_tree.item(item_id, "values"))
                if len(values) >= 4:
                    if status == "downloading":
                        values[3] = "Downloading..."
                    elif status == "completed":
                        values[3] = "Completed"
                    elif status == "error":
                        values[3] = "Failed"
                    elif status == "pending":
                        values[3] = "Pending"
                    self.video_tree.item(item_id, values=values)
                break

    def update_playlist_status(self, text):
        """Update playlist status label"""
        self.playlist_status_var.set(text)

    def playlist_download_finished(self, text):
        """Handle playlist download completion"""
        # Show detailed completion dialog
        messagebox.showinfo("Playlist Download Complete", text)

        # Update status with completion message
        self.playlist_status_var.set(text)

        # Re-enable UI elements
        self.playlist_download_btn.configure(state="normal")
        self.playlist_cancel_btn.configure(state="disabled")
        self.get_playlist_btn.configure(state="normal")

        # Keep progress bars at 100% for a moment to show completion
        self.playlist_progress_bar.set(1.0)
        self.current_video_progress_bar.set(1.0)

        # Reset progress bars after a delay
        self.after(
            3000,
            lambda: (
                self.playlist_progress_bar.set(0),
                self.current_video_progress_bar.set(0),
            ),
        )

    def playlist_download_error(self, text):
        """Handle playlist download error"""
        # Show detailed error dialog with suggestions
        error_message = f"Playlist download encountered an error:\n\n{text}\n\n"
        error_message += "Suggestions:\n"
        error_message += "• Check your internet connection\n"
        error_message += "• Verify the playlist URL is accessible\n"
        error_message += "• Try refreshing cookies if authentication is required\n"
        error_message += "• Check if FFmpeg is available for format conversion"

        messagebox.showerror("Playlist Download Error", error_message)
        self.playlist_status_var.set(
            f"Error: {text[:100]}..." if len(text) > 100 else f"Error: {text}"
        )

        # Re-enable UI elements
        self.playlist_download_btn.configure(state="normal")
        self.playlist_cancel_btn.configure(state="disabled")
        self.get_playlist_btn.configure(state="normal")

        # Reset progress bars
        self.playlist_progress_bar.set(0)
        self.current_video_progress_bar.set(0)

    def handle_playlist_video_finished(self, text):
        """Handle individual playlist video completion"""
        self.logger.log_info(f"Playlist video finished: {text}")
        # Individual video completion is handled internally by PlaylistDownloader
        # No specific UI action needed here

    def handle_playlist_video_error(self, text):
        """Handle individual playlist video error"""
        self.logger.log_warning(f"Playlist video error: {text}")
        # Individual video errors are handled internally by PlaylistDownloader
        # The overall playlist status will be updated accordingly

    def show_error(self, text, error_record=None):
        """Show error message"""
        # This is a single video download error
        messagebox.showerror("Error", text)
        self.status_var.set(f"Error: {text}")
        # Re-enable download button for single video downloads
        self.download_btn.configure(state="normal")

    def download_finished(self, text):
        """Handle single video download completion"""
        # This is a single video download
        messagebox.showinfo("Download Complete", text)
        self.status_var.set(text)
        self.download_btn.configure(state="normal")
        self.progress_bar.set(0)

    def handle_video_info_success(self, message):
        """Handle successful video info retrieval"""
        info = message["info"]
        self.formats = message["formats"]
        self.video_formats = message["video_formats"]
        self.audio_formats = message["audio_formats"]

        # Store format ID mappings
        self.format_id_map = message.get("format_id_map", {})
        self.video_format_id_map = message.get("video_format_id_map", {})
        self.audio_format_id_map = message.get("audio_format_id_map", {})

        # Update format combos
        # For automatic mode, always show "Best Video and Best Audio"
        self.format_combo.configure(values=["Best Video and Best Audio"])
        self.format_combo.set("Best Video and Best Audio")
        self.format_combo.configure(state="disabled")

        if self.video_formats:
            self.video_format_combo.configure(values=self.video_formats)
            self.video_format_combo.set(self.video_formats[0])
            self.video_format_combo.configure(state="readonly")

        if self.audio_formats:
            self.audio_format_combo.configure(values=self.audio_formats)
            self.audio_format_combo.set(self.audio_formats[0])
            self.audio_format_combo.configure(state="readonly")

        # Enable download button
        self.download_btn.configure(state="normal")

        self.status_var.set(f"Video info loaded: {info.get('title', 'Unknown')}")

    def enable_button(self, button_name):
        """Enable specific button"""
        if button_name == "get_info":
            self.get_info_btn.configure(state="normal")

    def on_tab_change(self):
        """Handle tab change events for URL transfer"""
        new_tab = self.tabview.get()

        # Transfer URL when switching from Single Video to Playlist
        if self.current_tab == "Single Video" and new_tab == "Playlist":
            single_video_url = self.url_var.get().strip()
            if single_video_url:
                self.playlist_url_var.set(single_video_url)

        # Transfer URL when switching from Playlist to Single Video
        elif self.current_tab == "Playlist" and new_tab == "Single Video":
            playlist_url = self.playlist_url_var.get().strip()
            if playlist_url:
                self.url_var.set(playlist_url)

        # Update current tab tracking
        self.current_tab = new_tab

    def toggle_format_mode(self, selected_value=None):
        """Toggle between automatic and manual format selection"""
        # Get the current selection from the combo box
        current_mode = self.format_mode_var.get()

        if current_mode == "Automatic":
            self.auto_format_frame.grid()
            self.manual_format_frame.grid_remove()
            # Ensure format combo shows the correct value for automatic mode
            self.format_combo.configure(
                state="normal", values=["Best Video and Best Audio"]
            )
            self.format_combo.set("Best Video and Best Audio")
            self.format_combo.configure(state="disabled")
        else:  # Manual
            self.auto_format_frame.grid_remove()
            self.manual_format_frame.grid()

        self.update_format_controls()

    def toggle_playlist_format_mode(self, selected_value=None):
        """Toggle between automatic and manual format selection for playlist"""
        # Get the current selection from the combo box
        current_mode = self.playlist_format_mode_var.get()

        if current_mode == "Automatic":
            self.playlist_auto_format_frame.grid()
            self.playlist_manual_format_frame.grid_remove()
            # Ensure playlist format combo shows the correct value for automatic mode
            self.playlist_format_combo.configure(
                state="normal", values=["Best Video and Best Audio"]
            )
            self.playlist_format_combo.set("Best Video and Best Audio")
            self.playlist_format_combo.configure(state="disabled")
        else:  # Manual
            self.playlist_auto_format_frame.grid_remove()
            self.playlist_manual_format_frame.grid()
            # Ensure manual combos have values populated
            try:
                self._populate_playlist_manual_formats()
            except Exception:
                pass

    def update_format_controls(self):
        """Update format control states based on available data"""
        formats_available = len(self.formats) > 0

        if self.format_mode_var.get() == "Automatic":
            self.format_combo.configure(
                state="disabled" if not formats_available else "disabled"
            )
        else:  # Manual
            video_formats_available = len(self.video_formats) > 0
            audio_formats_available = len(self.audio_formats) > 0

            self.video_format_combo.configure(
                state="readonly" if video_formats_available else "disabled"
            )
            self.audio_format_combo.configure(
                state="readonly" if audio_formats_available else "disabled"
            )

    def _validate_url(self, url):
        """Simple URL validation - only check for empty URLs"""
        if not url or not url.strip():
            return False, "Please enter a video URL"

        return True, url.strip()

    def get_video_info(self):
        """Get video information in background thread"""
        raw_url = self.url_var.get()

        # Simple URL validation - only check for empty URLs
        is_valid, result = self._validate_url(raw_url)

        if not is_valid:
            messagebox.showwarning("Error", result)
            return

        url = result

        # Disable button during processing
        self.get_info_btn.configure(state="disabled")
        self.status_var.set("Fetching video information...")

        # Start background thread
        thread = threading.Thread(
            target=self._get_video_info_thread, args=(url,), daemon=True
        )
        thread.start()

    def _get_video_info_thread(self, url):
        """Background thread for getting video info using real yt-dlp"""
        try:
            import yt_dlp

            # Clean URL and extract info
            cleaned_url = clean_url_for_video_info(url)

            # Setup yt-dlp options
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
                "socket_timeout": 30,
            }

            # Add cookie support
            try:
                from utils import setup_ytdlp_cookies

                setup_ytdlp_cookies(
                    ydl_opts=ydl_opts,
                    cookie_manager=self.cookie_manager,
                    url=url,
                    logger=self.logger,
                    context="info",
                )
            except Exception as e:
                self.logger.log_warning(f"Cookie setup failed: {str(e)}")

            # Extract video info using yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(cleaned_url, download=False)

            # Parse formats
            formats = []
            video_formats = []
            audio_formats = []
            format_id_map = {}
            video_format_id_map = {}
            audio_format_id_map = {}

            # Add only the best quality option for automatic mode
            formats = ["Best Video and Best Audio"]
            format_id_map["Best Video and Best Audio"] = "bestvideo+bestaudio"

            # Parse available formats
            if "formats" in info:
                for fmt in info["formats"]:
                    format_id = fmt.get("format_id", "")
                    ext = fmt.get("ext", "")
                    vcodec = fmt.get("vcodec", "none")
                    acodec = fmt.get("acodec", "none")
                    height = fmt.get("height")
                    abr = fmt.get("abr")

                    if vcodec != "none" and acodec != "none":
                        # Combined format
                        quality = f"{height}p" if height else "unknown"
                        display_string = f"{quality} {ext}"
                        formats.append(display_string)
                        format_id_map[display_string] = format_id
                    elif vcodec != "none":
                        # Video only
                        quality = f"{height}p" if height else "unknown"
                        display_string = f"{quality} {ext}"
                        video_formats.append(display_string)
                        video_format_id_map[display_string] = format_id
                    elif acodec != "none":
                        # Audio only
                        bitrate = f"{abr}k" if abr else "unknown"
                        display_string = f"{bitrate} {ext}"
                        audio_formats.append(display_string)
                        audio_format_id_map[display_string] = format_id

            # Limit to reasonable number of formats
            formats = formats[:15]
            video_formats = video_formats[:15]
            audio_formats = audio_formats[:10]

            self.current_video_info = info
            self.current_video_url = cleaned_url

            # Update GUI via queue
            self.update_queue.put(
                {
                    "type": "video_info_success",
                    "info": info,
                    "formats": formats,
                    "video_formats": video_formats,
                    "audio_formats": audio_formats,
                    "format_id_map": format_id_map,
                    "video_format_id_map": video_format_id_map,
                    "audio_format_id_map": audio_format_id_map,
                }
            )

        except Exception as e:
            err = str(e)
            if "sign in to confirm" in err.lower():
                self.logger.log_warning(
                    "Video info request hit YouTube auth despite cookies. Ensure manual cookies are fresh and UA matches."
                )
            self.update_queue.put(
                {"type": "error", "text": f"Error getting video info: {err}"}
            )
        finally:
            self.update_queue.put({"type": "enable_button", "button": "get_info"})

    def start_download(self):
        """Start video download using real DownloadThread"""
        output_path = self.output_dir_var.get().strip()

        if not output_path:
            messagebox.showwarning("Error", "Please enter output directory")
            return

        # Check if video info has been retrieved (ensures URL is processed)
        if not hasattr(self, "current_video_url") or not self.current_video_url:
            messagebox.showwarning(
                "Error", "Please click 'Get Video Info' first to process the URL"
            )
            return

        # Use the cleaned/processed URL instead of raw input
        url = self.current_video_url

        # Get selected format
        if self.format_mode_var.get() == "Automatic":
            format_selection = self.format_combo.get()
            # Use format ID mapping for automatic mode
            format_id = self.format_id_map.get(format_selection, "bestvideo+bestaudio")
            video_format_id = None
            audio_format_id = None
        else:  # Manual
            format_id = None
            # Map display strings back to actual format IDs
            video_display = self.video_format_combo.get()
            audio_display = self.audio_format_combo.get()
            video_format_id = self.video_format_id_map.get(video_display, video_display)
            audio_format_id = self.audio_format_id_map.get(audio_display, audio_display)

        # Disable download button
        self.download_btn.configure(state="disabled")

        # Start download using DownloadThread (single source of truth)
        downloader = DownloadThread(
            url,
            format_id,
            output_path,
            self.update_queue,
            video_format_id,
            audio_format_id,
        )
        # Store reference for lifecycle management
        self.single_video_downloader = downloader
        downloader.start()

    def get_playlist_info(self):
        """Get playlist information using real yt-dlp"""
        url = self.playlist_url_var.get().strip()
        if not url:
            messagebox.showwarning("Error", "Please enter a playlist URL")
            return

        # Disable button and show loading
        self.get_playlist_btn.configure(state="disabled")
        self.playlist_info_label.configure(text="Loading playlist information...")

        # Start background thread for playlist extraction
        thread = threading.Thread(
            target=self._get_playlist_info_thread, args=(url,), daemon=True
        )
        thread.start()

    def _get_playlist_info_thread(self, url):
        """Background thread for getting playlist info using real yt-dlp"""
        try:
            import yt_dlp

            # Normalize playlist URL
            normalized_url = normalize_playlist_url(url)

            # Setup yt-dlp options for playlist
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,  # Only get playlist info, not individual videos
                "socket_timeout": 30,
            }

            # Add cookie support
            try:
                from utils import setup_ytdlp_cookies

                setup_ytdlp_cookies(
                    ydl_opts=ydl_opts,
                    cookie_manager=self.cookie_manager,
                    url=url,
                    logger=self.logger,
                    context="playlist",
                )
            except Exception as e:
                self.logger.log_warning(f"Cookie setup failed: {str(e)}")

            # Extract playlist info
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                playlist_info = ydl.extract_info(normalized_url, download=False)

            # Process playlist data
            playlist_title = playlist_info.get("title", "Unknown Playlist")
            entries = playlist_info.get("entries", [])
            video_count = len(entries)

            # Update GUI in main thread
            self.after(
                0,
                lambda: self._update_playlist_gui(playlist_title, video_count, entries),
            )

        except Exception as e:
            # Update GUI with error in main thread
            error_msg = str(e)
            self.after(0, lambda: self._handle_playlist_error(error_msg))
        finally:
            # Re-enable button
            self.after(0, lambda: self.get_playlist_btn.configure(state="normal"))

    def _update_playlist_gui(self, playlist_title, video_count, entries):
        """Update playlist GUI with real data"""
        # Update playlist info label
        self.playlist_info_label.configure(
            text=f"{playlist_title} - {video_count} videos"
        )

        # Clear existing items and selection state
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
        self.video_selection_state.clear()

        # Add real videos (limit to first 50 for performance)
        for i, entry in enumerate(entries[:50]):
            if entry:
                title = entry.get("title", f"Video {i + 1}")
                duration = entry.get("duration", 0)
                # Compute URL from entry
                video_url = entry.get("webpage_url") or entry.get("url")
                vid = entry.get("id")
                if not video_url and vid:
                    video_url = f"https://www.youtube.com/watch?v={vid}"

                # Format duration
                if duration:
                    minutes = duration // 60
                    seconds = duration % 60
                    duration_str = f"{minutes}:{seconds:02d}"
                else:
                    duration_str = "Unknown"

                # Add to tree with checkbox (initially selected)
                item_id = self.video_tree.insert(
                    "", "end", values=("☑", title, duration_str, "Ready")
                )
                self.video_selection_state[item_id] = True
                # Store per-item URL to avoid constructing from item_id
                self.playlist_item_data[item_id] = {
                    "url": video_url,
                    "title": title,
                    "duration": duration_str,
                }

        # Enable playlist download if we have videos
        if video_count > 0:
            self.playlist_download_btn.configure(state="normal")
            # Pre-populate manual format combos for better UX
            try:
                self._populate_playlist_manual_formats()
            except Exception:
                pass

    def _on_video_tree_click(self, event):
        """Handle click events on video tree for checkbox functionality"""
        region = self.video_tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.video_tree.identify_row(event.y)
            column = self.video_tree.identify_column(event.x)

            # Only handle clicks on the Select column (#1)
            if column == "#1" and item:
                self._toggle_video_selection(item)
                return "break"  # Prevent default selection behavior

    def _on_video_tree_space(self, event):
        """Handle space key press for checkbox toggle"""
        selection = self.video_tree.selection()
        if selection:
            item = selection[0]
            self._toggle_video_selection(item)
            return "break"

    def _toggle_video_selection(self, item_id):
        """Toggle selection state of a video item"""
        if item_id not in self.video_selection_state:
            return

        # Toggle state
        current_state = self.video_selection_state[item_id]
        new_state = not current_state
        self.video_selection_state[item_id] = new_state

        # Update visual representation
        values = list(self.video_tree.item(item_id, "values"))
        values[0] = "☑" if new_state else "☐"
        self.video_tree.item(item_id, values=values)

        # Update download button state based on selection
        self._update_download_button_state()

    def _select_all_videos(self):
        """Select all videos in the playlist"""
        for item_id in self.video_selection_state:
            self.video_selection_state[item_id] = True
            values = list(self.video_tree.item(item_id, "values"))
            values[0] = "☑"
            self.video_tree.item(item_id, values=values)
        self._update_download_button_state()

    def _deselect_all_videos(self):
        """Deselect all videos in the playlist"""
        for item_id in self.video_selection_state:
            self.video_selection_state[item_id] = False
            values = list(self.video_tree.item(item_id, "values"))
            values[0] = "☐"
            self.video_tree.item(item_id, values=values)
        self._update_download_button_state()

    def _update_download_button_state(self):
        """Update download button state based on video selection"""
        has_selection = any(self.video_selection_state.values())
        if has_selection and len(self.video_selection_state) > 0:
            self.playlist_download_btn.configure(state="normal")
        else:
            self.playlist_download_btn.configure(state="disabled")

    def get_selected_videos(self):
        """Get list of selected video item IDs for download operations"""
        return [
            item_id
            for item_id, selected in self.video_selection_state.items()
            if selected
        ]

    def _handle_playlist_error(self, error_msg):
        """Handle playlist extraction error"""
        self.playlist_info_label.configure(text="Error loading playlist")
        messagebox.showerror("Playlist Error", f"Failed to load playlist: {error_msg}")

    def start_playlist_download(self):
        """Start playlist download using dedicated PlaylistDownloader"""
        selected_videos = self.get_selected_videos()
        selected_count = len(selected_videos)

        if selected_count == 0:
            messagebox.showwarning(
                "No Selection", "Please select at least one video to download."
            )
            return

        # Validate output directory
        output_path = self.playlist_output_dir_var.get().strip()
        if not output_path:
            messagebox.showwarning("Error", "Please select an output directory")
            return

        # Get format selection
        if self.playlist_format_mode_var.get() == "Automatic":
            format_id = "bestvideo+bestaudio"
            video_format_id = None
            audio_format_id = None
        else:
            # Manual format selection
            video_format = self.playlist_video_format_combo.get()
            audio_format = self.playlist_audio_format_combo.get()

            if not video_format or not audio_format:
                messagebox.showwarning(
                    "Error", "Please select both video and audio formats"
                )
                return

            format_id = None
            video_format_id = video_format
            audio_format_id = audio_format

        # Disable UI elements during download
        self.playlist_download_btn.configure(state="disabled")
        self.playlist_cancel_btn.configure(state="normal")
        self.get_playlist_btn.configure(state="disabled")

        # Reset progress bars
        self.playlist_progress_bar.set(0)
        self.current_video_progress_bar.set(0)

        # Update status
        self.playlist_status_var.set(
            f"Starting playlist download of {selected_count} videos..."
        )

        # Prepare selected video data for PlaylistDownloader from stored mapping
        selected_video_data = []
        for video_item_id in selected_videos:
            data = self.playlist_item_data.get(video_item_id)
            if data and data.get("url"):
                selected_video_data.append(
                    {
                        "url": data["url"],
                        "title": data.get("title", ""),
                        "duration": data.get("duration", "Unknown"),
                    }
                )

        # Resolve manual format IDs when in Manual mode
        if self.playlist_format_mode_var.get() == "Manual":
            v_display = self.playlist_video_format_combo.get()
            a_display = self.playlist_audio_format_combo.get()
            video_format_id = getattr(self, "playlist_video_format_id_map", {}).get(
                v_display, v_display
            )
            audio_format_id = getattr(self, "playlist_audio_format_id_map", {}).get(
                a_display, a_display
            )

        # Start playlist download using dedicated PlaylistDownloader
        self.playlist_downloader = PlaylistDownloader(
            selected_videos=selected_video_data,
            format_id=format_id,
            output_path=output_path,
            update_queue=self.update_queue,
            video_format_id=video_format_id,
            audio_format_id=audio_format_id,
        )
        self.playlist_downloader.start()

    def cancel_playlist_download(self):
        """Cancel playlist download using PlaylistDownloader"""
        # Ask for confirmation
        result = messagebox.askyesno(
            "Cancel Download",
            "Are you sure you want to cancel the playlist download?\n\n"
            "Any videos currently being downloaded will be stopped.",
        )

        if result:
            # Cancel playlist download if running
            if hasattr(self, "playlist_downloader") and self.playlist_downloader:
                self.playlist_downloader.cancel()

            self.playlist_status_var.set("Cancelling playlist download...")

            # Show cancellation notification
            messagebox.showinfo(
                "Download Cancelled", "Playlist download has been cancelled."
            )

            # Re-enable UI elements
            self.playlist_download_btn.configure(state="normal")
            self.playlist_cancel_btn.configure(state="disabled")
            self.get_playlist_btn.configure(state="normal")

            # Reset progress bars
            self.playlist_progress_bar.set(0)
            self.current_video_progress_bar.set(0)

            self.playlist_status_var.set("Playlist download cancelled")

    def browse_directory(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)

    def browse_playlist_directory(self):
        """Browse for playlist output directory"""
        directory = filedialog.askdirectory(
            initialdir=self.playlist_output_dir_var.get()
        )
        if directory:
            self.playlist_output_dir_var.set(directory)

    def show_cookie_help(self):
        """Show cookie help dialog using real cookie help system"""
        try:
            from cookie_help_system import show_cookie_help_dialog

            show_cookie_help_dialog()
        except ImportError:
            # Fallback if cookie help system not available
            help_text = (
                "Cookie Management Help:\n\n"
                "1. Auto-Refresh Cookies: Automatically extracts cookies from your browser\n"
                "2. Import Cookie File: Import cookies from a Netscape format file\n"
                "3. Browser Selection: Choose which browser to extract cookies from\n\n"
                "For age-restricted or private videos, you need to be logged in to YouTube in your browser."
            )
            messagebox.showinfo("Cookie Help", help_text)

    def show_cookie_export_help(self):
        """Show cookie export help using real cookie help system"""
        try:
            from cookie_help_system import CookieHelpSystem

            CookieHelpSystem.show_cookie_export_help(self)
        except (ImportError, AttributeError):
            # Fallback if cookie help system not available
            help_text = (
                "Cookie Export Help:\n\n"
                "To export cookies manually:\n"
                "1. Install a browser extension like 'Get cookies.txt'\n"
                "2. Visit YouTube and make sure you're logged in\n"
                "3. Use the extension to export cookies as 'cookies.txt'\n"
                "4. Import the file using the 'Import Cookie File' button\n\n"
                "The auto-refresh feature does this automatically for supported browsers."
            )
            messagebox.showinfo("Cookie Export Help", help_text)

    def refresh_cookies_enhanced(self):
        """Refresh cookies from browser using real cookie manager with enhanced feedback"""
        if self.cookie_operation_in_progress:
            self._update_cookie_status(
                "Operation already in progress, please wait", "orange"
            )
            return

        self.cookie_operation_in_progress = True
        self._update_cookie_status("Refreshing cookies from browser...", "orange")

        # Disable buttons during operation
        self.refresh_cookies_btn.configure(state="disabled")
        self.import_cookies_btn.configure(state="disabled")
        self.browser_refresh_btn.configure(state="disabled")

        def refresh_thread():
            try:
                if not self.cookie_manager:
                    self.after(
                        0,
                        lambda: self._handle_refresh_complete(
                            False, "Cookie manager not available"
                        ),
                    )
                    return

                # Step 1: Check Chrome status
                self.after(
                    0,
                    lambda: self._update_cookie_status(
                        "Checking Chrome browser...", "orange"
                    ),
                )

                # Step 2: Refresh browser detection
                self.after(
                    0,
                    lambda: self._update_cookie_status(
                        "Detecting browser installation...", "orange"
                    ),
                )
                self.cookie_manager.refresh_browser_detection()

                # Step 3: Extract cookies
                self.after(
                    0,
                    lambda: self._update_cookie_status(
                        "Extracting cookies from browser...", "orange"
                    ),
                )
                refresh_result = self.cookie_manager.refresh_cookies()

                if refresh_result:
                    # Step 4: Validate cookies
                    self.after(
                        0,
                        lambda: self._update_cookie_status(
                            "Validating extracted cookies...", "orange"
                        ),
                    )
                    status = self.cookie_manager.get_cookie_status()
                    self.after(0, lambda: self._handle_refresh_complete(True, status))
                else:
                    self.after(
                        0,
                        lambda: self._handle_refresh_complete(
                            False, "Failed to extract cookies from browser"
                        ),
                    )

            except Exception as e:
                error_msg = f"Refresh error: {str(e)}"
                self.logger.log_error(f"Cookie refresh failed: {e}")
                self.after(0, lambda: self._handle_refresh_complete(False, error_msg))

        thread = threading.Thread(target=refresh_thread, daemon=True)
        thread.start()

    def import_cookie_file_enhanced(self):
        """Import cookie file using real cookie manager with enhanced feedback"""
        if self.cookie_operation_in_progress:
            self._update_cookie_status(
                "Operation already in progress, please wait", "orange"
            )
            return

        file_path = filedialog.askopenfilename(
            title="Select Cookie File (cookies.txt format)",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~/Downloads"),
        )

        if not file_path:
            return  # User cancelled

        self.cookie_operation_in_progress = True
        filename = os.path.basename(file_path)

        # Disable buttons during operation
        self.refresh_cookies_btn.configure(state="disabled")
        self.import_cookies_btn.configure(state="disabled")
        self.browser_refresh_btn.configure(state="disabled")

        def import_thread():
            try:
                if not self.cookie_manager:
                    self.after(
                        0,
                        lambda: self._handle_import_complete(
                            False, "Cookie manager not available", filename
                        ),
                    )
                    return

                # Step 1: Validate file exists and is readable
                self.after(
                    0,
                    lambda: self._update_cookie_status(
                        f"Validating file: {filename}...", "orange"
                    ),
                )

                if not os.path.exists(file_path):
                    self.after(
                        0,
                        lambda: self._handle_import_complete(
                            False, "File not found", filename
                        ),
                    )
                    return

                if not os.access(file_path, os.R_OK):
                    self.after(
                        0,
                        lambda: self._handle_import_complete(
                            False, "File not readable", filename
                        ),
                    )
                    return

                # Step 2: Check file size
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    self.after(
                        0,
                        lambda: self._handle_import_complete(
                            False, "File is empty", filename
                        ),
                    )
                    return
                elif file_size > 10 * 1024 * 1024:  # 10MB limit
                    self.after(
                        0,
                        lambda: self._handle_import_complete(
                            False, "File too large (>10MB)", filename
                        ),
                    )
                    return

                # Step 3: Import cookies
                self.after(
                    0,
                    lambda: self._update_cookie_status(
                        f"Importing cookies from {filename}...", "orange"
                    ),
                )
                success = self.cookie_manager.import_cookies_from_file(file_path)

                if success:
                    # Step 4: Validate imported cookies
                    self.after(
                        0,
                        lambda: self._update_cookie_status(
                            "Validating imported cookies...", "orange"
                        ),
                    )
                    status = self.cookie_manager.get_cookie_status()
                    self.after(
                        0, lambda: self._handle_import_complete(True, status, filename)
                    )
                else:
                    self.after(
                        0,
                        lambda: self._handle_import_complete(
                            False, "Invalid cookie file format", filename
                        ),
                    )

            except Exception as e:
                error_msg = f"Import error: {str(e)}"
                self.logger.log_error(f"Cookie import failed: {e}")
                self.after(
                    0, lambda: self._handle_import_complete(False, error_msg, filename)
                )

        thread = threading.Thread(target=import_thread, daemon=True)
        thread.start()

    def refresh_browser_detection(self):
        """Refresh browser detection using real cookie manager with enhanced feedback"""
        if self.cookie_operation_in_progress:
            self._update_cookie_status(
                "Operation already in progress, please wait", "orange"
            )
            return

        self.cookie_operation_in_progress = True
        self._update_cookie_status("Refreshing browser detection...", "orange")

        # Disable button during operation
        self.browser_refresh_btn.configure(state="disabled")

        def detection_thread():
            try:
                if self.cookie_manager:
                    # Get available browsers from cookie manager
                    available_browsers = self.cookie_manager.get_available_browsers()
                    browsers = ["Auto-detect (Recommended)"]
                    browsers.extend(available_browsers)

                    # Update browser combo on main thread
                    self.after(0, lambda: self.browser_combo.configure(values=browsers))

                    # Update cookie status
                    status = self.cookie_manager.get_cookie_status()
                    self.after(0, lambda: self._handle_detection_complete(True, status))
                else:
                    # Fallback if cookie manager not available
                    browsers = [
                        "Auto-detect (Recommended)",
                        "Chrome",
                        "Firefox",
                        "Edge",
                    ]
                    self.after(0, lambda: self.browser_combo.configure(values=browsers))
                    self.after(
                        0,
                        lambda: self._handle_detection_complete(
                            False, "Cookie manager not available"
                        ),
                    )
            except Exception as e:
                # Fallback on error
                browsers = ["Auto-detect (Recommended)", "Chrome", "Firefox", "Edge"]
                self.after(0, lambda: self.browser_combo.configure(values=browsers))
                error_msg = f"Detection error: {str(e)}"
                self.logger.log_error(f"Browser detection failed: {e}")
                self.after(0, lambda: self._handle_detection_complete(False, error_msg))

        thread = threading.Thread(target=detection_thread, daemon=True)
        thread.start()

    def check_ffmpeg_on_startup(self):
        """Check FFmpeg availability on application startup"""
        if not check_ffmpeg():
            self.show_ffmpeg_dialog()

    def initialize_cookie_system(self):
        """Initialize cookie system and browser detection on startup"""
        try:
            self._update_cookie_status("Initializing cookie system...", "orange")

            # Initialize browser detection without triggering the threaded version
            if self.cookie_manager:
                # Get available browsers from cookie manager
                available_browsers = self.cookie_manager.get_available_browsers()
                browsers = ["Auto-detect (Recommended)"]
                browsers.extend(available_browsers)
                self.browser_combo.configure(values=browsers)

                # Set initial cookie status
                status = self.cookie_manager.get_cookie_status()
                self._update_cookie_status(status, "green")
            else:
                # Fallback if cookie manager not available
                browsers = ["Auto-detect (Recommended)", "Chrome", "Firefox", "Edge"]
                self.browser_combo.configure(values=browsers)
                self._update_cookie_status("Manager not available", "red")
        except Exception as e:
            self._update_cookie_status("Initialization error", "red")
            self.logger.log_warning(f"Cookie system initialization failed: {str(e)}")

    def show_ffmpeg_dialog(self):
        """Show dialog asking user if they want to download FFmpeg"""
        result = messagebox.askyesno(
            "FFmpeg Not Found",
            "FFmpeg is not available on your system.\n\n"
            "FFmpeg is required for merging video and audio streams to get the best quality downloads.\n\n"
            "Without FFmpeg, only default video quality will be available (single format downloads).\n\n"
            "Would you like to download and install FFmpeg automatically?",
        )
        if result:
            self.download_ffmpeg()

    def download_ffmpeg(self):
        """Start FFmpeg download process using consolidated utility function"""
        from utils import download_ffmpeg

        # Use the consolidated function to check FFmpeg availability
        if download_ffmpeg():
            messagebox.showinfo(
                "FFmpeg Status", "FFmpeg is already available in the bin directory!"
            )
        else:
            messagebox.showinfo(
                "FFmpeg Download", "FFmpeg download functionality will be implemented"
            )

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""

        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            label = tk.Label(
                tooltip,
                text=text,
                background="#ffffe0",
                relief="solid",
                borderwidth=1,
                font=("Arial", 9),
            )
            label.pack()
            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, "tooltip"):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _update_cookie_status(self, message: str, color: str = "white"):
        """Update cookie status with color coding"""
        self.cookie_status_var.set(f"Cookie Status: {message}")
        self.cookie_status_label.configure(text_color=color)

    def _handle_refresh_complete(self, success: bool, message: str):
        """Handle completion of cookie refresh operation"""
        self.cookie_operation_in_progress = False

        # Re-enable buttons
        self.refresh_cookies_btn.configure(state="normal")
        self.import_cookies_btn.configure(state="normal")
        self.browser_refresh_btn.configure(state="normal")

        if success:
            self._update_cookie_status(f"Refresh successful - {message}", "green")
        else:
            self._update_cookie_status(f"Refresh failed - {message}", "red")

    def _handle_import_complete(self, success: bool, message: str, filename: str):
        """Handle completion of cookie import operation"""
        self.cookie_operation_in_progress = False

        # Re-enable buttons
        self.refresh_cookies_btn.configure(state="normal")
        self.import_cookies_btn.configure(state="normal")
        self.browser_refresh_btn.configure(state="normal")

        if success:
            self._update_cookie_status(f"Import successful - {filename}", "green")
        else:
            self._update_cookie_status(f"Import failed - {message}", "red")

    def _handle_detection_complete(self, success: bool, message: str):
        """Handle completion of browser detection operation"""
        self.cookie_operation_in_progress = False

        # Re-enable button
        self.browser_refresh_btn.configure(state="normal")

        if success:
            self._update_cookie_status(f"Detection complete - {message}", "green")
        else:
            self._update_cookie_status(f"Detection failed - {message}", "red")


def main():
    """Main application entry point"""
    logger = AppLogger.get_instance()

    try:
        logger.log_info("Starting Video Downloader application (CustomTkinter version)")

        # Create and run application
        app = VideoDownloaderApp()

        logger.log_info("CustomTkinter Application created successfully")

        # Start the application
        logger.log_info("Starting CustomTkinter main loop")
        app.mainloop()

        logger.log_info("Application shutdown completed")

    except KeyboardInterrupt:
        logger.log_info("Application interrupted by user")
    except Exception as e:
        logger.log_error("Fatal error in main application", exception=e)
        print(f"Fatal error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
