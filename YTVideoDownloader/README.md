# YTVideoDownloader: Desktop Media Download and Playlist Workflows

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/language-Python-blue)](https://www.python.org/downloads/)

**Status:** Experimental desktop utility with source, unit/integration test code and a Windows executable. Website compatibility changes with upstream yt-dlp and platform behavior.

YTVideoDownloader adds a desktop interface to yt-dlp workflows for selecting formats, processing playlists and merging media with FFmpeg. The project focuses on background jobs, progress feedback, error handling and configurable authentication inputs. Use it only for media you are authorized to download; authenticated requests may send selected cookies to the relevant media service.

## What this project demonstrates

- Background download/playlist jobs with queues, progress and format selection.
- Integration of yt-dlp and optional FFmpeg with desktop error feedback.
- Cookie-source precedence and tests for download, playlist and UI scenarios.

A stored Windows artifact does not establish current compatibility with every platform, browser or media site. Review third-party terms and keep session cookies private.

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
- Authentication-error feedback and configurable cookie/retry handling
- **Browser cookie extraction and import support**
- Progress tracking with visual feedback
- Custom output directory selection
- Source routes for Windows, macOS and Linux; validate dependencies and site behavior on the target system

## FFmpeg

The application checks for a bundled FFmpeg binary under `bin` and otherwise looks on `PATH`. The current source tree does not include a `bin` directory; supply FFmpeg for source installations that need merging or conversion. The contents of a prebuilt executable must be checked separately.

When FFmpeg is unavailable, merging separate video/audio streams is limited. Codec and format availability depend on the installed build and media source; no universal format support is guaranteed. See [Building from Source](#building-from-source) to include an appropriate FFmpeg binary in your own package.

## Quick Start

### Running from Source

Use a Python version supported by the dependencies resolved in your environment. The current requirements include `pywin32` for Windows cookie handling, so the unmodified requirements file is Windows-specific. The shell examples below describe environment activation on other systems, not a validated macOS/Linux install; review platform-specific dependencies before attempting those ports.

1. Clone the repository:
   ```bash
   git clone https://github.com/rodhayl/MovibeCodingProjects.git
   cd MovibeCodingProjects/YTVideoDownloader
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

### Using the Windows executable

The repository contains [dist/VideoDownloader.exe](dist/VideoDownloader.exe). This is a versioned repository artifact, not a separate GitHub Release. Review its source/version and evaluate it with authorized sample media before regular use. No macOS or Linux binary is provided in this tree.

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

YTVideoDownloader includes cookie-source selection and retry/error handling for authenticated downloads. These mechanisms do not guarantee access or permission to bypass a service restriction:

- **Browser cookie helpers**: Support depends on the browser, operating system, permissions and upstream libraries
- **Smart retry logic**: Automatically retries downloads with fresh cookies when authentication fails
- **Retry pacing**: Spaces attempts; this does not guarantee that a service will allow them
- **Fallback mechanisms**: Uses visitor data when cookies aren't available

### Manual Cookie Import

If you encounter persistent authentication issues, you can manually import cookies:

#### Manual export and import

Only use cookies from an account you control and are authorized to use for the requested media. Review the permissions and provenance of any export tool before installing it. Export only the required service cookies, store the file privately and select it using Cookie Settings / Import Cookie File in the application.

Cookie files can provide access to an authenticated session. Do not upload them to issues, chat, shared folders or source control. Remove unneeded exports and review the application's temporary-file handling; automatic cleanup is not a guarantee that every copy is gone.

If a service rejects a request, follow its supported access process and restrictions. Repeated retries or fresh cookies do not establish authorization.

### Troubleshooting Authentication Issues

#### "Sign in to confirm you're not a bot" Error

1. **Review the error**: Confirm that the media and account access are authorized; retries may still be rejected
2. **Manual refresh**: Click "Refresh Cookies" button in the application
3. **Import fresh cookies**: Export new cookies from your browser and import them
4. **Respect restrictions**: Stop repeated attempts when the service refuses access and follow its supported guidance

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

### Cookie security and privacy

- Cookie extraction and preparation happen on the machine, but yt-dlp can transmit selected cookies to the media service for authenticated requests.
- Keep the browser profile and exported cookie files private. They can contain sensitive session information.
- Temporary files may be created; inspect cleanup behavior and remove unneeded exports without assuming all copies disappear automatically.
- Download requests communicate with the selected site and its media infrastructure. Local processing is not a “no data transmission” guarantee.
- Account restrictions and platform changes can prevent a download. No account-safety or authentication-success rate is claimed.

## Usage

See the Quick User Guide in this README.

## Development and validation

See [CONTRIBUTING.md](CONTRIBUTING.md) for environment setup and conventions. The test tree contains unit, integration and real-download scenarios. Inspect a test before running it: mocked checks do not establish live-site compatibility, and real-download scenarios require authorized media and network access.

Record the commit, yt-dlp/FFmpeg versions, test scope and skips when reporting results. No authentication-success or universal platform-support metric is asserted here.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## License

This project is open source and available under the MIT License. See [LICENSE](LICENSE) file for details.

Third-party attributions can be found in [NOTICE](NOTICE).

## Disclaimer

This tool is intended for downloading videos you have rights to or that are in the public domain. Please respect copyright laws and the terms of service of the platforms you download from.
