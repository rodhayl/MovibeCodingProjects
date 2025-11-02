@echo off
echo ========================================
echo   Building PhotoFilter Executable
echo ========================================
echo.

REM Change to the directory where this script is located
cd /d "%~dp0"

echo.
echo Cleaning previous build...
if exist "build" rmdir /S /Q "build"
if exist "dist" rmdir /S /Q "dist"
if exist "PhotoFilter.spec" del /Q "PhotoFilter.spec"

echo.
echo Building executable with PyInstaller...
echo This may take several minutes...
python -m PyInstaller build_minimal.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Please check the error messages above.
    echo.
    echo Common fixes:
    echo   1. Install PyInstaller: python -m pip install pyinstaller
    echo   2. Check Python is in PATH: python --version
    echo   3. Try: python -m PyInstaller --clean build_exe.spec
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build Completed Successfully!
echo ========================================
echo.
if exist "dist\PhotoFilter.exe" (
    for %%I in (dist\PhotoFilter.exe) do (
        set size=%%~zI
        set /a sizeMB=!size!/1048576
        echo Executable: dist\PhotoFilter.exe
        echo Size: !sizeMB! MB
    )
) else (
    echo ERROR: dist\PhotoFilter.exe not found!
)
echo.
echo You can now:
echo  1. Test the executable: dist\PhotoFilter.exe
echo  2. Distribute it to users (no Python required!)
echo.

pause
