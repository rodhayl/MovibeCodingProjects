# Contributing to YTVideoDownloader

Thank you for your interest in contributing to YTVideoDownloader! This document provides guidelines for contributing, development setup, project conventions, and policies.

## How to Contribute

### Reporting Issues

Before reporting an issue, please check the existing issues to avoid duplicates. When reporting a new issue, please include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Screenshots if applicable
- Your operating system and Python version (if running from source)
- Any relevant error messages or logs

### Suggesting Enhancements

Feature requests are welcome! Please provide:

- A clear description of the proposed feature
- Use cases for the feature
- Any implementation ideas you might have

### Code Contributions

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes with clear, concise commits
4. Add or update tests as necessary
5. Ensure all tests pass
6. Update documentation as needed
7. Submit a pull request with a clear description of your changes

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests: `python -m unittest discover tests`

## Code Style

- Follow [PEP 8](https://pep8.org/) guidelines for Python code
- Use meaningful variable and function names
- Include docstrings for all public classes and functions
- Add comments for complex logic
- Keep lines under 100 characters

## Testing

- Write unit tests for new functionality
- Ensure all existing tests pass before submitting a pull request
- Run tests with: `python -m unittest discover tests`

## Pull Request Process

1. Ensure your code follows the project's coding standards
2. Include tests for any new functionality
3. Update documentation as needed
4. Describe your changes in the pull request
5. Reference any related issues

## License

By contributing to YTVideoDownloader, you agree that your contributions will be licensed under the MIT License with additional terms.

---

## Development Guide

Architecture
- GUI: CustomTkinter
- Download engine: `yt_dlp`
- Media processing: FFmpeg
- Threading: Background threads for downloads; UI remains responsive

Key Components
- `main.py` / `gui/main_window.py`: UI setup, event wiring
- `download_threads.py`: Single video downloads
- `playlist_downloader.py`: Playlist processing
- `utils.py`: FFmpeg detection, path helpers, URL helpers

Features
- Manual video/audio format mixing (e.g., `137+140`)
- Playlist URL normalization and selection
- Cross‑platform Downloads folder detection

Running tests
- Unit: `python -m pytest -q tests\unit`
- Single file: `python -m pytest -q tests\unit\test_cookie_precedence.py`

Dependencies
- See `requirements.txt`

Building
1) Place FFmpeg in `bin/` (Windows: `bin/ffmpeg.exe`, macOS/Linux: `bin/ffmpeg`)
2) Package: `python build_package.py`
3) Output in `dist/`

---

## Project Agent Guide (For Automation/Contributors)

Quick Facts
- Runtime: Python 3, Windows‑first (paths, PowerShell, cmd)
- Core libs: `yt_dlp`, `customtkinter`, `sqlite3` (Chrome cookies), `psutil` (optional)
- Entry points: `gui/main_window.py`, `download_threads.py`, `single_video_downloader.py`
- Cookies: `cookie_manager.py` with `get_cookie_manager()`

Cookie Handling
- Precedence: manual import > `cookiesfrombrowser` > auto‑extracted temp file
- `get_cookies_for_ytdlp_enhanced()` returns:
  - `source`: `manual_import` | `cookies_from_browser` | `auto_extracted`
  - `cookie_file`: temp Netscape file path (when applicable)
  - `browser_spec`: e.g., `chrome:Profile 1` → split to `(browser, profile)` for yt‑dlp
- Mapping at call sites:
  - `cookiefile` ← `cookie_data["cookie_file"]`
  - `cookiesfrombrowser` ← tuple from `cookie_data["browser_spec"]`

Test‑First Fixes
1) Write failing, minimal test
2) Implement smallest fix to pass
3) Re‑run that test; then impacted subset
4) Keep scope tight; avoid drive‑by refactors

Conventions
- Logging: `AppLogger.get_instance()`; no print
- Threading: guard shared state; queue UI updates
- Windows paths: normalize for external tools; use LF for Netscape cookie files
- yt‑dlp: quiet loggers; set `ffmpeg_location` when bundled FFmpeg exists

Review Checklist
- Cookie behavior changes covered by precedence tests
- Temp files tracked/cleaned via cookie manager
- No network in tests (use mocks)
- GUI updates through the queue; avoid blocking

---

## Code of Conduct

We are committed to a welcoming, inclusive community.

Standards
- Use inclusive language; be respectful and empathetic
- Accept constructive criticism gracefully
- No harassment, trolling, or publishing private info

Maintainer Responsibilities
- Clarify acceptable behavior; act on violations
- Edit/remove contributions that violate standards; enforce consistently

Scope
- Applies in project spaces and when representing the project publicly

Reporting
- Report incidents to the maintainers (private channel/email). Reports are confidential.
- Consequences determined by project leadership depending on severity

Attribution: Adapted from Contributor Covenant v1.4

---

## Security Policy

Supported Versions
- Latest release is supported with security updates

Reporting Vulnerabilities
- Email the maintainers or open a private GitHub security advisory
- Include description, steps to reproduce/PoC, impact, and fix suggestions

Security Considerations
- Input validation; safe subprocess handling for FFmpeg
- Path sanitization; trusted libraries for network calls (`yt_dlp`)

Best Practices for Users
- Download only content you’re authorized to access
- Keep dependencies and the app up‑to‑date
