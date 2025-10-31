@echo off
echo ========================================
echo   PhotoFilter - AI Photo Recognition
echo ========================================
echo.

REM Change to the directory where this script is located
cd /d "%~dp0"

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    exit /b 1
)

REM Optional CLI arg: cuda|amd|cpu|auto
set "PHOTOFILTER_TORCH_ACCELERATOR=%~1"
if /I "%PHOTOFILTER_TORCH_ACCELERATOR%"=="" (
    REM Load persisted choice if available
    if exist ".accelerator_choice" (
        for /f "usebackq delims=" %%A in (".accelerator_choice") do set "PHOTOFILTER_TORCH_ACCELERATOR=%%A"
    )
)

echo.
echo Installing/updating dependencies...
call scripts\install.bat
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

echo.
echo Checking accelerator-specific (CUDA/AMD/CPU) dependencies...
python scripts\install_gpu_deps.py
if errorlevel 1 (
    echo ERROR: Failed to install GPU/accelerator dependencies
    exit /b 1
)

REM After installer (which may have prompted), re-load persisted choice
if exist ".accelerator_choice" (
    for /f "usebackq delims=" %%A in (".accelerator_choice") do set "PHOTOFILTER_TORCH_ACCELERATOR=%%A"
)
if not "%PHOTOFILTER_TORCH_ACCELERATOR%"=="" (
    echo Using accelerator: %PHOTOFILTER_TORCH_ACCELERATOR%
)

echo.
echo Starting PhotoFilter Application...
echo.

REM Try to run the application using the package structure first
python -m photofilter.gui.main_window 2>nul
if errorlevel 1 (
    echo Package structure not available, trying production GUI...
    python photo_recognition_gui_production.py
    if errorlevel 1 (
        echo ERROR: Failed to start application
        echo Please check the installation and try again
        exit /b 1
    )
)

echo.
echo Application closed.
