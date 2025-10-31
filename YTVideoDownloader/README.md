# YTVideoDownloader

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey)

A cross-platform GUI application for downloading videos from YouTube, Vimeo, and many other platforms.

## Documentation

This README now includes the essential user guide. For contributor guidance, see `CONTRIBUTING.md`.

### Quick User Guide

1) Run from source
   - Create venv: `python -m venv venv`
   - Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux)
   - Install deps: `pip install -r requirements.txt`
   - Launch: `python main.py`

2) Single video download
   - Paste a video URL, click "Get Video Info"
   - Pick a format (or enable manual selection for separate video/audio)
   - Choose output folder, then "Download"

3) Playlist download
   - Paste a playlist URL, click "Get Playlist Info"
   - (Optional) Select specific videos, choose format strategy
   - Choose output folder, then "Download Playlist"

4) FFmpeg
   - Bundled `bin/ffmpeg` is used when available; otherwise PATH is used

For development setup, testing, and project conventions, read `CONTRIBUTING.md`.

## Features

- Download videos from multiple platforms (YouTube, Vimeo, etc.)
- Download entire YouTube playlists
- Select specific videos from playlists
- Real-time video info fetching and format selection
- Automatic merging of best video and audio streams
- Manual audio-video format mixing (select specific video and audio formats to merge)
- **Automated cookie management for YouTube authentication**
- **Automatic handling of "Sign in to confirm you're not a bot" errors**
- **Browser cookie extraction and import support**
- Progress tracking with visual feedback
- Custom output directory selection
- Cross-platform compatibility (Windows, macOS, Linux)

## Bundled FFmpeg

This application now includes FFmpeg binaries to ensure all video formats can be downloaded without requiring a separate FFmpeg installation.

### How it works

1. The application first checks for bundled FFmpeg in the `bin` directory
2. If found, it uses the bundled version automatically
3. If not found, it falls back to checking for FFmpeg in the system PATH
4. If FFmpeg is not available at all, only single formats (video-only or audio-only) can be downloaded

### Benefits

- No need to install FFmpeg separately
- Works out-of-the-box on all supported platforms
- All video formats can be downloaded without additional setup
- Reduced support issues related to missing dependencies

## Quick Start

### Running from Source

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd YTVideoDownloader
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

### Using Pre-built Executable

1. Download the latest release (see Releases section)
2. Extract the archive
3. Run VideoDownloader.exe (Windows) or VideoDownloader (macOS/Linux)

## Building from Source

To create a standalone executable with bundled FFmpeg:

1. Place the appropriate FFmpeg binary in the `bin` directory:
   - Windows: `bin/ffmpeg.exe`
   - macOS/Linux: `bin/ffmpeg`

2. Run the packaging script:
   ```bash
   python build_package.py
   ```

3. Find the executable in the `dist` directory

## Cookie Management & YouTube Authentication

### Automatic Cookie Management

YTVideoDownloader includes an advanced cookie management system that automatically handles YouTube's "Sign in to confirm you're not a bot" errors:

- **Automatic browser detection**: Extracts cookies from Chrome, Firefox, Edge, and Safari
- **Smart retry logic**: Automatically retries downloads with fresh cookies when authentication fails
- **Rate limiting**: Prevents triggering additional bot detection
- **Fallback mechanisms**: Uses visitor data when cookies aren't available

### Manual Cookie Import

If you encounter persistent authentication issues, you can manually import cookies:

#### Using Browser Extensions

1. **Install a cookie export extension**:
   - **Chrome/Edge**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - **Firefox**: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
   - **Alternative**: [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)

2. **Export YouTube cookies**:
   - Navigate to `youtube.com` in your browser
   - Make sure you're logged in to your YouTube account
   - Click the extension icon
   - Export cookies for `youtube.com` (save as `.txt` file)

3. **Import cookies in YTVideoDownloader**:
   - Open the application
   - Click "Cookie Settings" or "Import Cookie File"
   - Select your exported cookie file
   - The application will automatically use these cookies for downloads

#### Best Practices for Cookie Export

- **Use incognito/private browsing**: For better cookie stability
  1. Open incognito/private window
  2. Log into YouTube
  3. Navigate to `https://www.youtube.com/robots.txt`
  4. Export cookies from this tab
  5. Close the incognito window immediately

- **Export fresh cookies**: YouTube rotates cookies frequently, so export new ones if downloads fail

### Troubleshooting Authentication Issues

#### "Sign in to confirm you're not a bot" Error

1. **Automatic handling**: The application should automatically retry with fresh cookies
2. **Manual refresh**: Click "Refresh Cookies" button in the application
3. **Import fresh cookies**: Export new cookies from your browser and import them
4. **Rate limiting**: Wait 5-10 minutes between download attempts to avoid triggering more blocks

#### Cookie Import Issues

- **Supported formats**: Netscape format (.txt), JSON format, tab-separated format
- **File encoding**: Ensure cookie files are saved as UTF-8
- **Domain matching**: Make sure cookies are for `youtube.com` or `.youtube.com`
- **Fresh cookies**: Use recently exported cookies (within 24 hours)

#### Browser Detection Issues

- **Windows**: Cookies are extracted from `%LOCALAPPDATA%` directories
- **macOS**: Cookies are extracted from `~/Library/Application Support`
- **Linux**: Cookies are extracted from `~/.config` directories
- **Permissions**: Ensure the application has read access to browser directories

### Cookie Security & Privacy

- **Local processing**: All cookie extraction and processing happens locally
- **Temporary files**: Cookie files are automatically cleaned up after use
- **No data transmission**: Cookies are never sent to external servers
- **Account safety**: Use throwaway accounts if concerned about potential bans

## Usage

See the Quick User Guide in this README.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## License

This project is open source and available under the MIT License. See [LICENSE](LICENSE) file for details.

Third-party attributions can be found in [NOTICE](NOTICE).

## Disclaimer

This tool is intended for downloading videos you have rights to or that are in the public domain. Please respect copyright laws and the terms of service of the platforms you download from.
