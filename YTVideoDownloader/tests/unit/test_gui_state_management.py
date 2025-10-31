#!/usr/bin/env python3
"""
Pytest-style tests for GUI state management functionality

Tests GUI component state transitions, data binding, and event handling logic
without requiring a real GUI window.
"""

from unittest.mock import Mock, patch


def test_format_mode_toggle_to_manual(video_downloader_app):
    """Test toggling from automatic to manual format selection"""
    app = video_downloader_app

    app.format_mode_var.set("Automatic")
    app.format_mode_var.set("Manual")
    app.toggle_format_mode()

    assert app.format_mode_var.get() == "Manual"
    app.auto_format_frame.grid_remove.assert_called()
    app.manual_format_frame.grid.assert_called()


def test_format_mode_toggle_to_automatic(video_downloader_app):
    """Test toggling from manual to automatic format selection"""
    app = video_downloader_app

    app.format_mode_var.set("Manual")
    app.format_mode_var.set("Automatic")
    app.toggle_format_mode()

    assert app.format_mode_var.get() == "Automatic"
    app.auto_format_frame.grid.assert_called()
    app.manual_format_frame.grid_remove.assert_called()


def test_format_controls_update_with_formats_available(video_downloader_app):
    """Test format controls update when formats are available"""
    app = video_downloader_app

    app.formats = ["Best Video and Best Audio"]
    app.video_formats = ["1080p mp4", "720p mp4"]
    app.audio_formats = ["128k m4a", "48k m4a"]

    app.format_mode_var.set("Automatic")
    app.update_format_controls()

    app.format_combo.configure.assert_called_with(state="disabled")

    app.format_mode_var.set("Manual")
    app.update_format_controls()

    app.video_format_combo.configure.assert_called_with(state="readonly")
    app.audio_format_combo.configure.assert_called_with(state="readonly")


def test_format_controls_update_no_formats_available(video_downloader_app):
    """Test format controls update when no formats are available"""
    app = video_downloader_app

    app.formats = []
    app.video_formats = []
    app.audio_formats = []

    app.format_mode_var.set("Automatic")
    app.update_format_controls()

    app.format_combo.configure.assert_called_with(state="disabled")

    app.format_mode_var.set("Manual")
    app.update_format_controls()

    app.video_format_combo.configure.assert_called_with(state="disabled")
    app.audio_format_combo.configure.assert_called_with(state="disabled")


def test_queue_message_handling_progress(video_downloader_app):
    """Test handling of progress messages from queue"""
    app = video_downloader_app

    progress_message = {"type": "progress", "value": 50}
    app.handle_queue_message(progress_message)

    app.progress_bar.set.assert_called_with(0.5)


def test_queue_message_handling_status(video_downloader_app):
    """Test handling of status messages from queue"""
    app = video_downloader_app

    status_message = {"type": "status", "text": "Downloading..."}
    app.handle_queue_message(status_message)

    assert app.status_var.get() == "Downloading..."


def test_queue_message_handling_error(video_downloader_app):
    """Test handling of error messages from queue"""
    app = video_downloader_app

    with patch("gui.main_window.messagebox.showerror") as mock_error:
        error_message = {"type": "error", "text": "Download failed"}
        app.handle_queue_message(error_message)

        mock_error.assert_called_once_with("Error", "Download failed")
        assert app.status_var.get() == "Error: Download failed"


def test_queue_message_handling_finished(video_downloader_app):
    """Test handling of finished messages from queue"""
    app = video_downloader_app

    with patch("gui.main_window.messagebox.showinfo") as mock_info:
        finished_message = {"type": "finished", "text": "Download completed"}
        app.handle_queue_message(finished_message)

        mock_info.assert_called_once_with("Download Complete", "Download completed")
        assert app.status_var.get() == "Download completed"
        app.download_btn.configure.assert_called_with(state="normal")
        app.progress_bar.set.assert_called_with(0)


def test_queue_message_handling_video_info_success(video_downloader_app):
    """Test handling of video info success messages from queue"""
    app = video_downloader_app

    video_info_message = {
        "type": "video_info_success",
        "info": {"title": "Test Video", "duration": 300},
        "formats": ["Best Video and Best Audio"],
        "video_formats": ["1080p mp4", "720p mp4"],
        "audio_formats": ["128k m4a", "48k m4a"],
    }

    app.handle_queue_message(video_info_message)

    assert app.formats == ["Best Video and Best Audio"]
    assert app.video_formats == ["1080p mp4", "720p mp4"]
    assert app.audio_formats == ["128k m4a", "48k m4a"]

    app.format_combo.configure.assert_any_call(values=["Best Video and Best Audio"])
    app.format_combo.set.assert_called_with("Best Video and Best Audio")
    app.download_btn.configure.assert_called_with(state="normal")


def test_queue_message_handling_enable_button(video_downloader_app):
    """Test handling of enable button messages from queue"""
    app = video_downloader_app

    enable_message = {"type": "enable_button", "button": "get_info"}
    app.handle_queue_message(enable_message)

    app.get_info_btn.configure.assert_called_with(state="normal")


def test_url_validation_logic(video_downloader_app):
    """Test URL validation logic in get_video_info"""
    app = video_downloader_app

    with patch("gui.main_window.messagebox.showwarning") as mock_warning:
        app.url_var.set("")

        with patch("gui.main_window.threading.Thread"):
            app.get_video_info()

        mock_warning.assert_called_once_with("Error", "Please enter a video URL")


def test_download_validation_logic(video_downloader_app):
    """Test download validation logic in start_download"""
    app = video_downloader_app

    with patch("gui.main_window.messagebox.showwarning") as mock_warning:
        app.output_dir_var = Mock()
        app.output_dir_var.get.return_value = ""

        app.start_download()

        mock_warning.assert_called_once_with("Error", "Please enter output directory")


def test_format_selection_logic_automatic(video_downloader_app):
    """Test format selection logic for automatic mode"""
    app = video_downloader_app

    app.format_mode_var.set("Automatic")
    app.url_var.set("https://www.youtube.com/watch?v=test")
    app.output_dir_var = Mock()
    app.output_dir_var.get.return_value = "/tmp"
    app.current_video_url = "https://www.youtube.com/watch?v=test"
    app.format_combo.get = Mock(return_value="Best Video and Best Audio")

    with patch("gui.main_window.DownloadThread") as mock_download:
        app.start_download()

        mock_download.assert_called_once()
        args = mock_download.call_args[0]
        assert args[0] == "https://www.youtube.com/watch?v=test"
        assert args[1] == "bestvideo+bestaudio"
        assert args[2] == "/tmp"
        assert args[4] is None
        assert args[5] is None


def test_format_selection_logic_manual(video_downloader_app):
    """Test format selection logic for manual mode"""
    app = video_downloader_app

    app.format_mode_var.set("Manual")
    app.url_var.set("https://www.youtube.com/watch?v=test")
    app.output_dir_var = Mock()
    app.output_dir_var.get.return_value = "/tmp"
    app.current_video_url = "https://www.youtube.com/watch?v=test"
    app.video_format_combo.get = Mock(return_value="1080p mp4")
    app.audio_format_combo.get = Mock(return_value="128k m4a")

    with patch("gui.main_window.DownloadThread") as mock_thread:
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        app.start_download()

        mock_thread.assert_called_once()
        call_args = mock_thread.call_args[0]

        assert call_args[1] is None
        assert call_args[4] == "1080p mp4"
        assert call_args[5] == "128k m4a"


def test_url_transfer_single_to_playlist(video_downloader_app):
    """Test URL transfer from Single Video to Playlist tab"""
    app = video_downloader_app

    test_url = "https://www.youtube.com/watch?v=test123"
    app.url_var.set(test_url)
    app.current_tab = "Single Video"
    app.tabview.get = Mock(return_value="Playlist")

    app.on_tab_change()

    assert app.playlist_url_var.get() == test_url
    assert app.current_tab == "Playlist"


def test_url_transfer_playlist_to_single(video_downloader_app):
    """Test URL transfer from Playlist to Single Video tab"""
    app = video_downloader_app

    test_url = "https://www.youtube.com/playlist?list=test123"
    app.playlist_url_var.set(test_url)
    app.current_tab = "Playlist"
    app.tabview.get = Mock(return_value="Single Video")

    app.on_tab_change()

    assert app.url_var.get() == test_url
    assert app.current_tab == "Single Video"


def test_url_transfer_no_url(video_downloader_app):
    """Test tab change when no URL is present"""
    app = video_downloader_app

    app.url_var.set("")
    app.playlist_url_var.set("")
    app.current_tab = "Single Video"
    app.tabview.get = Mock(return_value="Playlist")

    app.on_tab_change()

    assert app.current_tab == "Playlist"
    assert app.playlist_url_var.get() == ""
