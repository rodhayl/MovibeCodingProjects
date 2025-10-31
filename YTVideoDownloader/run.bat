@echo off
REM Video Downloader Launcher for Windows
REM Enhanced version with colored output, progress indicators, and better error messages

setlocal EnableDelayedExpansion

REM ANSI color codes for Windows 10+
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "CYAN=[96m"
set "RESET=[0m"
set "BOLD=[1m"
set "DIM=[2m"

REM Header with banner
echo.
echo %CYAN%%BOLD%========================================%RESET%
echo %CYAN%%BOLD%   YouTube Video Downloader Launcher   %RESET%
echo %CYAN%%BOLD%========================================%RESET%
echo.

REM Ensure we run from the script directory
pushd "%~dp0" >nul

REM Step 1: Check for Python
echo %BLUE%[1/4]%RESET% Checking for Python installation...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
	echo %RED%✗ Error:%RESET% Python not found
	echo.
	echo %YELLOW%Please install Python 3.10 or later from:%RESET%
	echo   https://www.python.org/downloads/
	echo.
	echo %YELLOW%Make sure to check "Add Python to PATH" during installation!%RESET%
	echo.
	REM pause removed to allow non-interactive exit
	popd >nul
	exit /b 1
)

REM Get Python version for display
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN%✓%RESET% Python %PYTHON_VERSION% found

REM Step 2: Check for pip
echo.
echo %BLUE%[2/4]%RESET% Checking for pip package manager...
python -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
	echo %YELLOW%⚠ Warning:%RESET% pip not found
	echo.
	echo %YELLOW%Attempting to bootstrap pip...%RESET%
	python -m ensurepip --upgrade 2>&1 | findstr /V "Requirement already satisfied"
	if %ERRORLEVEL% neq 0 (
		echo %RED%✗ Error:%RESET% Failed to install pip automatically
		echo.
		echo %YELLOW%Please install pip manually:%RESET%
		echo   1. Download get-pip.py from https://bootstrap.pypa.io/get-pip.py
		echo   2. Run: python get-pip.py
		echo.
			REM pause removed to allow non-interactive exit
		popd >nul
		exit /b 1
	)
	echo %GREEN%✓%RESET% pip installed successfully
) else (
	for /f "tokens=2" %%i in ('python -m pip --version 2^>^&1') do set PIP_VERSION=%%i
	echo %GREEN%✓%RESET% pip !PIP_VERSION! found
)

REM Step 3: Install dependencies
echo.
echo %BLUE%[3/4]%RESET% Checking and installing dependencies...

if exist "%~dp0requirements.txt" (
	REM Detect virtual environment
	set "PIP_OPTS="
	if defined VIRTUAL_ENV (
		echo %CYAN%ℹ Info:%RESET% Virtual environment detected
		echo   Installing to: !VIRTUAL_ENV!
	) else (
		echo %CYAN%ℹ Info:%RESET% No virtual environment detected
		echo   Using --user flag to avoid admin requirements
		set "PIP_OPTS=--user"
	)
	
	echo.
	echo %DIM%Installing packages from requirements.txt...%RESET%
	echo %DIM%─────────────────────────────────────────%RESET%
	
	REM Install with better output
	python -m pip install !PIP_OPTS! -q -r "%~dp0requirements.txt" 2>&1 | findstr /V "Requirement already satisfied" | findstr /V "^$"
	
	if !ERRORLEVEL! neq 0 (
		echo.
		echo %RED%✗ Error:%RESET% Failed to install dependencies
		echo.
		echo %YELLOW%Troubleshooting steps:%RESET%
		echo   1. Check your internet connection
		echo   2. Try running as Administrator
		echo   3. Manually run: python -m pip install -r requirements.txt
		echo   4. Check the error messages above for specific issues
		echo.
			REM pause removed to allow non-interactive exit
		popd >nul
		exit /b 1
	)
	
	echo %DIM%─────────────────────────────────────────%RESET%
	echo %GREEN%✓%RESET% All dependencies installed successfully
) else (
	echo %YELLOW%⚠ Warning:%RESET% No requirements.txt found
	echo   Skipping dependency installation
)

REM Step 4: Launch application
echo.
echo %BLUE%[4/4]%RESET% Launching Video Downloader application...
echo.
echo %DIM%─────────────────────────────────────────%RESET%
echo.

REM Run the application
python "%~dp0main.py"
set APP_EXIT_CODE=!ERRORLEVEL!

echo.
echo %DIM%─────────────────────────────────────────%RESET%

if !APP_EXIT_CODE! equ 0 (
	echo.
	echo %GREEN%✓%RESET% Application closed successfully
) else (
	echo.
	echo %YELLOW%⚠%RESET% Application exited with code: !APP_EXIT_CODE!
)

echo.
echo %CYAN%Thank you for using YouTube Video Downloader!%RESET%
echo.

popd >nul
endlocal

REM No interactive pause — script will exit automatically
