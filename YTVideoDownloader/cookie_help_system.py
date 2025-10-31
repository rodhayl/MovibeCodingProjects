#!/usr/bin/env python3
"""
Intelligent Cookie Help System for YouTube Video Downloader

Provides contextual help, tooltips, and user guidance for cookie management.
Replaces vague error messages with specific, actionable instructions.
"""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk


class HelpTooltip(ctk.CTkButton):
    """Enhanced tooltip widget with rich content support."""

    def __init__(self, text, detailed_help=None, parent=None):
        super().__init__(
            parent,
            text="?",
            width=20,
            height=20,
            fg_color="#3498db",
            hover_color="#2980b9",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.help_text = text
        self.detailed_help = detailed_help

        # Configure tooltip behavior
        self.configure(command=self.show_detailed_help)

        # Create tooltip on hover
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.tooltip_window = None

    def on_enter(self, event):
        """Show tooltip on hover."""
        if self.help_text:
            self.show_tooltip()

    def on_leave(self, event):
        """Hide tooltip when leaving."""
        self.hide_tooltip()

    def show_tooltip(self):
        """Display tooltip window."""
        if self.tooltip_window:
            return

        x = self.winfo_rootx() + 25
        y = self.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip_window,
            text=self.help_text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            wraplength=300,
            justify="left",
        )
        label.pack()

    def hide_tooltip(self):
        """Hide tooltip window."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def show_detailed_help(self):
        """Show detailed help when clicked."""
        if self.detailed_help:
            dialog = DetailedHelpDialog(self.detailed_help, self)
            dialog.show()


class DetailedHelpDialog:
    """Dialog for showing detailed help content."""

    def __init__(self, content, parent=None):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Help & Instructions")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()

        # Configure grid
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        # Content area
        self.text_area = ctk.CTkTextbox(self.window, wrap="word")
        self.text_area.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Convert HTML content to plain text (simplified)
        plain_content = self._html_to_text(content)
        self.text_area.insert("0.0", plain_content)
        self.text_area.configure(state="disabled")

        # Close button
        close_btn = ctk.CTkButton(self.window, text="Close", command=self.close)
        close_btn.grid(row=1, column=0, pady=10)

    def _html_to_text(self, html_content):
        """Convert HTML content to plain text."""
        from utils import html_to_text

        return html_to_text(html_content)

    def show(self):
        """Show the dialog."""
        self.window.focus()

    def close(self):
        """Close the dialog."""
        self.window.destroy()


class CookieHelpSystem:
    """Centralized help system for cookie management."""

    @staticmethod
    def _load_html_template(filename):
        """Load HTML content from resources folder."""
        import os

        resources_dir = os.path.join(os.path.dirname(__file__), "resources")
        filepath = os.path.join(resources_dir, filename)
        try:
            with open(filepath, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"<p>Help content not found: {filename}</p>"

    @staticmethod
    def get_cookie_export_help():
        """Get detailed help for cookie export process."""
        return CookieHelpSystem._load_html_template("cookie_export_help.html")

    @staticmethod
    def get_browser_detection_help():
        """Get help for browser detection issues."""
        return CookieHelpSystem._load_html_template("browser_detection_help.html")

    @staticmethod
    def get_authentication_error_help():
        """Get help for authentication errors."""
        return CookieHelpSystem._load_html_template("authentication_error_help.html")

    @staticmethod
    def get_quick_fix_suggestions(error_type):
        """Get quick fix suggestions based on error type."""
        suggestions = {
            "authentication": [
                "Click 'Refresh Cookies' button",
                "Try selecting a different browser",
                "Import fresh cookies manually",
                "Wait 10 minutes and try again",
            ],
            "browser_detection": [
                "Close all browser windows",
                "Run application as administrator",
                "Check if browsers are installed",
                "Use manual cookie import instead",
            ],
            "cookie_import": [
                "Check file format (should be .txt)",
                "Ensure cookies are from youtube.com",
                "Try exporting cookies again",
                "Use 'Get cookies.txt LOCALLY' extension",
            ],
            "network": [
                "Check internet connection",
                "Try using VPN",
                "Wait and retry later",
                "Use different network",
            ],
        }
        return suggestions.get(error_type, ["Contact support for assistance"])

    @staticmethod
    def create_help_tooltip(text, detailed_help=None):
        """Create a help tooltip widget."""
        return HelpTooltip(text, detailed_help)

    @staticmethod
    def show_guided_setup():
        """Show guided setup wizard for first-time users."""
        wizard = CookieSetupWizard()
        return wizard.exec_()

    @staticmethod
    def show_detailed_help(parent=None):
        """Show detailed cookie management help."""
        help_content = CookieHelpSystem.get_cookie_export_help()
        dialog = DetailedHelpDialog(help_content, parent)
        dialog.show()
        return dialog

    @staticmethod
    def show_cookie_export_help(parent=None):
        """Show cookie export help dialog."""
        help_text = """
🍪 How to Export Cookies with "Get cookies.txt"

📋 Step-by-Step Guide:
1. Install Extension:
   • Chrome: Get cookies.txt from Chrome Web Store
   • Firefox: cookies.txt from Firefox Add-ons

2. Login to YouTube:
   • Go to youtube.com
   • Sign in to your account

3. Export Cookies:
   • Click the extension icon
   • Select "Export cookies for this site"
   • Save the .txt file

4. Import to App:
   • Click "Import Cookie File" button
   • Select your saved .txt file

💡 Tip: Export fresh cookies regularly for best results!
        """

        dialog = DetailedHelpDialog(help_text, parent)
        dialog.show()

    @staticmethod
    def show_browser_detection_help(parent=None):
        """Show browser detection help dialog."""
        help_text = """
🔍 Browser Detection & Auto-Cookie Extraction

📋 How It Works:
• Automatic Detection: Scans for Chrome, Edge, Firefox, Brave, Opera
• Cookie Extraction: Safely reads browser cookie databases
• Smart Selection: Prioritizes browsers with YouTube cookies

🔧 Troubleshooting:
• No Browsers Found: Ensure browsers are installed in standard locations
• Access Denied: Close all browser windows and try again
• No Cookies: Visit YouTube in your browser first

✅ Best Practices:
• Close browser before extraction
• Use Chrome or Edge for best compatibility
• Stay logged in to YouTube
        """

        dialog = DetailedHelpDialog(help_text, parent)
        dialog.show()


class CookieSetupWizard:
    """Guided setup wizard for cookie management."""

    def __init__(self, parent=None):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Cookie Management Setup Wizard")
        self.window.geometry("700x600")
        self.window.transient(parent)
        self.window.grab_set()

        self.current_step = 0
        self.total_steps = 4

        self.init_ui()

    def init_ui(self):
        """Initialize the wizard UI."""
        # Configure grid
        self.window.grid_rowconfigure(2, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            self.window,
            text="🍪 Cookie Management Setup Wizard",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        header.grid(row=0, column=0, pady=20, padx=20, sticky="ew")

        # Progress indicator
        self.progress_label = ctk.CTkLabel(
            self.window, text=f"Step {self.current_step + 1} of {self.total_steps}"
        )
        self.progress_label.grid(row=1, column=0, pady=5)

        # Content area
        self.content_area = ctk.CTkTextbox(self.window, wrap="word")
        self.content_area.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

        # Navigation buttons frame
        nav_frame = ctk.CTkFrame(self.window)
        nav_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        nav_frame.grid_columnconfigure(1, weight=1)

        self.prev_btn = ctk.CTkButton(
            nav_frame, text="← Previous", command=self.prev_step, state="disabled"
        )
        self.prev_btn.grid(row=0, column=0, padx=5)

        self.next_btn = ctk.CTkButton(nav_frame, text="Next →", command=self.next_step)
        self.next_btn.grid(row=0, column=2, padx=5)

        self.finish_btn = ctk.CTkButton(nav_frame, text="Finish", command=self.finish)
        self.finish_btn.grid(row=0, column=2, padx=5)
        self.finish_btn.grid_remove()  # Hide initially

        # Load first step
        self.load_step()

    def load_step(self):
        """Load content for current step."""
        steps = [
            self.get_welcome_content(),
            self.get_browser_setup_content(),
            self.get_manual_import_content(),
            self.get_completion_content(),
        ]

        # Clear and set content
        self.content_area.delete("0.0", "end")
        plain_content = self._html_to_text(steps[self.current_step])
        self.content_area.insert("0.0", plain_content)
        self.content_area.configure(state="disabled")

        self.progress_label.configure(
            text=f"Step {self.current_step + 1} of {self.total_steps}"
        )

        # Update button states
        if self.current_step > 0:
            self.prev_btn.configure(state="normal")
        else:
            self.prev_btn.configure(state="disabled")

        if self.current_step < self.total_steps - 1:
            self.next_btn.grid()
            self.finish_btn.grid_remove()
        else:
            self.next_btn.grid_remove()
            self.finish_btn.grid()

    def _html_to_text(self, html_content):
        """Convert HTML content to plain text."""
        from utils import html_to_text

        return html_to_text(html_content)

    def finish(self):
        """Finish the wizard."""
        self.window.destroy()

    def next_step(self):
        """Go to next step."""
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
            self.load_step()

    def prev_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self.load_step()

    def get_welcome_content(self):
        """Get welcome step content."""
        return CookieHelpSystem._load_html_template("wizard_welcome.html")

    def get_browser_setup_content(self):
        """Get browser setup step content."""
        return CookieHelpSystem._load_html_template("wizard_browser_setup.html")

    def get_manual_import_content(self):
        """Get manual import step content."""
        return CookieHelpSystem._load_html_template("wizard_manual_import.html")

    def get_completion_content(self):
        """Get completion step content."""
        return CookieHelpSystem._load_html_template("wizard_completion.html")


class SmartErrorHandler:
    """Intelligent error handler that provides contextual solutions."""

    @staticmethod
    def show_cookie_manager_error(parent=None):
        """Show cookie manager initialization error."""
        messagebox.showerror(
            "Cookie Manager Error",
            "Cookie manager is not available.\n\n"
            "The cookie management system failed to initialize. "
            "This may be due to missing dependencies or system permissions.\n\n"
            "Please try restarting the application or check the logs for more details.",
        )

    @staticmethod
    def show_browser_detection_error(parent=None, error_details=None):
        """Show browser detection error."""
        info_text = (
            "No browsers were detected or cookie extraction failed.\n\n"
            "Possible solutions:\n"
            "• Close all browser windows and try again\n"
            "• Ensure you have Chrome, Edge, or Firefox installed\n"
            "• Visit YouTube in your browser first to create cookies\n"
            "• Try importing cookies manually using browser extensions\n\n"
            "Special note for Chrome users:\n"
            "• If Chrome is running, close it completely and try again\n"
            "• Chrome keeps cookies in memory while running and only saves them when properly closed"
        )

        if error_details:
            info_text += f"\n\nError details: {error_details}"

        messagebox.showwarning("Browser Detection Failed", info_text)

    @staticmethod
    def show_cookie_import_error(parent=None, file_path=None, error_details=None):
        """Show enhanced cookie import error with JSON format guidance."""
        # Detect if this is a JSON format error
        is_json_error = False
        if file_path:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read().strip()
                    if (
                        content.startswith("{")
                        or content.startswith("[")
                        or '"cookies"' in content
                    ):
                        is_json_error = True
            except Exception:
                pass

        if is_json_error:
            title = "Cookie Import Failed - JSON Format Detected"
            info_text = (
                "❌ The selected file appears to be in JSON format.\n"
                "This application only accepts Netscape format cookies.\n\n"
                "✅ Required format: Netscape HTTP Cookie File\n"
                "• Must start with: # Netscape HTTP Cookie File\n"
                "• Tab-separated values (not JSON objects)\n"
                "• Plain text format (not JSON)\n\n"
                "📋 How to get correct format:\n"
                "• Use browser extensions that export Netscape format\n"
                "• Avoid extensions that export JSON format\n"
                "• Look for 'cookies.txt' or 'Netscape' in export options"
            )

            # Show error and ask if user wants export guide
            result = messagebox.askyesno(
                title, info_text + "\n\nWould you like to see the export guide?"
            )
            if result:
                SmartErrorHandler._show_export_guide(parent)
        else:
            title = "Cookie Import Failed"
            info_text = (
                "Failed to import cookie file.\n\n"
                "Please check:\n"
                "• File format is correct (Netscape format)\n"
                "• File contains YouTube cookies\n"
                "• File is not corrupted or empty\n"
                "• You have read permissions for the file"
            )

            if file_path:
                info_text += f"\n\nFile: {file_path}"

            if error_details:
                info_text += f"\nError: {error_details}"

            messagebox.showerror(title, info_text)

    @staticmethod
    def show_cookie_refresh_error(parent=None, error_details=None):
        """Show cookie refresh error."""
        info_text = (
            "Failed to refresh cookies automatically.\n\n"
            "Try these solutions:\n"
            "• Close all browser windows\n"
            "• Select a specific browser instead of auto-detect\n"
            "• Import cookies manually using browser extensions\n"
            "• Check that you're logged in to YouTube in your browser"
        )

        if error_details:
            info_text += f"\n\nError details: {error_details}"

        messagebox.showwarning("Cookie Refresh Failed", info_text)

    @staticmethod
    def show_no_cookies_file_error(parent=None):
        """Show specific error for when Chrome is installed but no cookie files exist."""
        info_text = (
            "🔍 Chrome is installed but no cookie files were found.\n\n"
            "This is normal in these situations:\n"
            "• Chrome has never been used to visit websites\n"
            "• Chrome is currently running (cookies not saved yet)\n"
            "• Chrome was recently installed but not used\n\n"
            "IMPORTANT: Chrome keeps cookies in memory while running and only writes them to disk when properly closed.\n\n"
            "Solution:\n"
            "1. Close ALL Chrome windows completely\n"
            "2. Check Task Manager to ensure NO chrome.exe processes remain\n"
            "3. Wait 10-15 seconds for Chrome to fully terminate\n"
            "4. Visit YouTube.com in Chrome and log in to your account\n"
            "5. Close Chrome again completely\n"
            "6. Click 'Refresh Cookies' in this application"
        )

        messagebox.showinfo("Chrome Detected But No Cookies Found", info_text)

    @staticmethod
    def handle_authentication_error(error_message, parent_widget=None):
        """Handle authentication errors with smart suggestions."""
        # Create a custom dialog for multiple options
        dialog = ctk.CTkToplevel(parent_widget)
        dialog.title("YouTube Authentication Required")
        dialog.geometry("600x500")
        dialog.transient(parent_widget)
        dialog.grab_set()

        result = {"action": "close"}

        # Configure grid
        dialog.grid_rowconfigure(1, weight=1)
        dialog.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            dialog,
            text="🚫 YouTube Authentication Required",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        header.grid(row=0, column=0, pady=20, padx=20, sticky="ew")

        # Content
        content_text = """
🔧 AUTOMATIC SOLUTIONS (Try these first):

1. Click "Refresh Cookies" button
   → Automatically extracts fresh cookies from your browser

2. Select different browser from dropdown
   → Tries cookies from Chrome, Edge, or Firefox

3. Wait and retry
   → System will automatically retry with fresh authentication

🛠️ MANUAL SOLUTIONS (If automatic fails):

1. Export fresh cookies:
   • Go to youtube.com in your browser and log in
   • Use "Get cookies.txt LOCALLY" browser extension
   • Click "Import Cookie File" in this application

2. Try incognito mode:
   • Open private/incognito browser window
   • Log into YouTube
   • Export cookies from that session

💡 PREVENTION TIPS:
   • Refresh cookies every 2-3 days
   • Avoid downloading too many videos rapidly
   • Use a dedicated YouTube account for downloads
        """

        content_area = ctk.CTkTextbox(dialog, wrap="word")
        content_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_area.insert("0.0", content_text)
        content_area.configure(state="disabled")

        # Buttons frame
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        btn_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def set_result(action):
            result["action"] = action
            dialog.destroy()

        refresh_btn = ctk.CTkButton(
            btn_frame, text="Refresh Cookies Now", command=lambda: set_result("refresh")
        )
        refresh_btn.grid(row=0, column=0, padx=5, pady=5)

        import_btn = ctk.CTkButton(
            btn_frame, text="Import Cookie File", command=lambda: set_result("import")
        )
        import_btn.grid(row=0, column=1, padx=5, pady=5)

        help_btn = ctk.CTkButton(
            btn_frame, text="Show Help Guide", command=lambda: set_result("help")
        )
        help_btn.grid(row=0, column=2, padx=5, pady=5)

        close_btn = ctk.CTkButton(
            btn_frame, text="Close", command=lambda: set_result("close")
        )
        close_btn.grid(row=0, column=3, padx=5, pady=5)

        # Wait for dialog to close
        dialog.wait_window()
        return result["action"]

    @staticmethod
    def handle_browser_detection_error(parent_widget=None):
        """Handle browser detection errors."""
        # Create a custom dialog for multiple options
        dialog = ctk.CTkToplevel(parent_widget)
        dialog.title("Browser Detection Issue")
        dialog.geometry("600x500")
        dialog.transient(parent_widget)
        dialog.grab_set()

        result = {"action": "close"}

        # Configure grid
        dialog.grid_rowconfigure(1, weight=1)
        dialog.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            dialog,
            text="🔍 No browsers detected or cookie extraction failed.",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        header.grid(row=0, column=0, pady=20, padx=20, sticky="ew")

        # Content
        content_text = """
🔧 QUICK FIXES:

1. Close all browser windows completely
   → Browser databases are locked when browsers are running
   → Chrome must be fully closed, not just minimized

2. Run application as administrator
   → Provides better access to browser data directories

3. Check browser installations
   → Ensure Chrome, Edge, or Firefox are installed

4. Use manual cookie import instead
   → Export cookies using browser extension

🛠️ DETAILED TROUBLESHOOTING:

• Windows: Check %LOCALAPPDATA% for browser directories
• Antivirus: Temporarily disable real-time protection
• Permissions: Ensure application has read access to browser data
• Browser versions: Very old browsers may not be supported

💡 ALTERNATIVE SOLUTION:
Use manual cookie import with "Get cookies.txt LOCALLY" extension.
This method works regardless of browser detection issues.

⚠️ SPECIAL NOTE FOR CHROME USERS:
If Chrome is currently running, the cookie database files may not exist yet.
Close Chrome completely, wait 10 seconds, then try again.
        """

        content_area = ctk.CTkTextbox(dialog, wrap="word")
        content_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_area.insert("0.0", content_text)
        content_area.configure(state="disabled")

        # Buttons frame
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        btn_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def set_result(action):
            result["action"] = action
            dialog.destroy()

        retry_btn = ctk.CTkButton(
            btn_frame, text="Retry Detection", command=lambda: set_result("retry")
        )
        retry_btn.grid(row=0, column=0, padx=5, pady=5)

        manual_btn = ctk.CTkButton(
            btn_frame, text="Use Manual Import", command=lambda: set_result("manual")
        )
        manual_btn.grid(row=0, column=1, padx=5, pady=5)

        help_btn = ctk.CTkButton(
            btn_frame, text="Show Setup Guide", command=lambda: set_result("help")
        )
        help_btn.grid(row=0, column=2, padx=5, pady=5)

        close_btn = ctk.CTkButton(
            btn_frame, text="Close", command=lambda: set_result("close")
        )
        close_btn.grid(row=0, column=3, padx=5, pady=5)

        # Wait for dialog to close
        dialog.wait_window()
        return result["action"]

    @staticmethod
    def _show_export_guide(parent=None):
        """Show detailed cookie export guide."""
        guide_text = (
            "How to Export Cookies in Netscape Format\n\n"
            "📋 Step-by-step guide:\n\n"
            "1️⃣ Install a browser extension:\n"
            "   • Chrome: 'Get cookies.txt' or 'cookies.txt'\n"
            "   • Firefox: 'cookies.txt' extension\n\n"
            "2️⃣ Visit YouTube.com and log in\n\n"
            "3️⃣ Click the extension icon\n\n"
            "4️⃣ Select export options:\n"
            "   ✅ Choose 'Netscape format' or 'cookies.txt'\n"
            "   ❌ Avoid 'JSON format'\n\n"
            "5️⃣ Save the file and import it here\n\n"
            "⚠️ Important:\n"
            "• File should start with '# Netscape HTTP Cookie File'\n"
            "• Should contain tab-separated values\n"
            "• Should NOT contain JSON brackets { } or [ ]"
        )

        messagebox.showinfo("Cookie Export Guide", guide_text)

    @staticmethod
    def handle_cookie_import_error(error_details, parent_widget=None):
        """Handle cookie import errors."""
        # Create a custom dialog for multiple options
        dialog = ctk.CTkToplevel(parent_widget)
        dialog.title("Cookie Import Failed")
        dialog.geometry("600x500")
        dialog.transient(parent_widget)
        dialog.grab_set()

        result = {"action": "close"}

        # Configure grid
        dialog.grid_rowconfigure(1, weight=1)
        dialog.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            dialog,
            text="📁 Failed to import cookie file.",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        header.grid(row=0, column=0, pady=20, padx=20, sticky="ew")

        # Content
        content_text = f"""
❌ ERROR DETAILS:
{error_details}

🔧 SOLUTIONS:

1. Check file format:
   • File should be .txt format
   • Should contain Netscape-style cookies
   • File should not be empty

2. Re-export cookies:
   • Go to youtube.com and log in fresh
   • Use "Get cookies.txt LOCALLY" extension
   • Select "Export for current site"
   • Choose "Netscape format" if asked

3. Try different browser:
   • Export from Chrome, Edge, or Firefox
   • Each browser may have different cookie formats

4. Check cookie content:
   • Open .txt file in notepad
   • Should contain lines starting with .youtube.com
   • Should have multiple cookie entries

💡 COMMON ISSUES:
• Empty file: Make sure you're logged into YouTube
• Wrong format: Ensure Netscape format is selected
• Expired cookies: Export fresh cookies (within 24 hours)
• Incomplete export: Make sure all YouTube cookies are included
        """

        content_area = ctk.CTkTextbox(dialog, wrap="word")
        content_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_area.insert("0.0", content_text)
        content_area.configure(state="disabled")

        # Buttons frame
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        btn_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def set_result(action):
            result["action"] = action
            dialog.destroy()

        retry_btn = ctk.CTkButton(
            btn_frame, text="Try Different File", command=lambda: set_result("retry")
        )
        retry_btn.grid(row=0, column=0, padx=5, pady=5)

        guide_btn = ctk.CTkButton(
            btn_frame, text="Show Export Guide", command=lambda: set_result("guide")
        )
        guide_btn.grid(row=0, column=1, padx=5, pady=5)

        auto_btn = ctk.CTkButton(
            btn_frame, text="Try Auto-Detection", command=lambda: set_result("auto")
        )
        auto_btn.grid(row=0, column=2, padx=5, pady=5)

        close_btn = ctk.CTkButton(
            btn_frame, text="Close", command=lambda: set_result("close")
        )
        close_btn.grid(row=0, column=3, padx=5, pady=5)

        # Wait for dialog to close
        dialog.wait_window()
        return result["action"]


# Utility functions for easy integration
# Note: create_help_tooltip() function consolidated - use CookieHelpSystem.create_help_tooltip() directly


# Removed redundant wrapper - use GUI-integrated version in main_window.py


# Removed redundant wrapper - use CookieHelpSystem.show_browser_detection_help() directly


def show_authentication_error_help(parent=None):
    """Show authentication error help dialog."""
    help_content = CookieHelpSystem.get_authentication_error_help()
    dialog = DetailedHelpDialog(help_content, parent)
    dialog.exec_()


def show_setup_wizard(parent=None):
    """Show the cookie setup wizard."""
    wizard = CookieSetupWizard(parent)
    wizard.window.wait_window()  # Wait for wizard to close
