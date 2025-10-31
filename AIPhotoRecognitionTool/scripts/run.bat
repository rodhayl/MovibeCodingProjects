@echo off
echo Starting Photo Recognition App...
cd /d "%~dp0\.."

REM Optional CLI arg: cuda|amd|cpu|auto
set "PHOTOFILTER_TORCH_ACCELERATOR=%~1"
if /I "%PHOTOFILTER_TORCH_ACCELERATOR%"=="" (
    REM Load persisted choice if available
    if exist ".accelerator_choice" (
        for /f "usebackq delims=" %%A in (".accelerator_choice") do set "PHOTOFILTER_TORCH_ACCELERATOR=%%A"
    )
)

echo Checking accelerator-specific (CUDA/AMD/CPU) dependencies...
python scripts\install_gpu_deps.py
if errorlevel 1 (
    echo ERROR: Failed to install GPU/accelerator dependencies
    exit /b 1
)

if exist ".accelerator_choice" (
    for /f "usebackq delims=" %%A in (".accelerator_choice") do set "PHOTOFILTER_TORCH_ACCELERATOR=%%A"
)
if not "%PHOTOFILTER_TORCH_ACCELERATOR%"=="" (
    echo Using accelerator: %PHOTOFILTER_TORCH_ACCELERATOR%
)

python photo_recognition_gui_production.py
if errorlevel 1 (
    exit /b 1
)
