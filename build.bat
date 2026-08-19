@echo off
title PCMod Standalone EXE Builder
echo ==========================================
echo       PCMod Standalone EXE Builder
echo ==========================================
echo.

echo Checking Python installation...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    py --version >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python was not found in PATH!
        echo Please install Python 3.8+ and add it to PATH.
        pause
        exit /b 1
    )
    set PY_CMD=py
) else (
    set PY_CMD=python
)

echo Installing build dependencies (pyinstaller, pywebview, portablemc)...
%PY_CMD% -m pip install pyinstaller pywebview portablemc --quiet

echo.
echo Building PCMod.exe with PyInstaller...
%PY_CMD% -m PyInstaller --clean PCMod.spec

if %errorlevel% equ 0 (
    echo.
    if exist "dist\PCMod.exe" (
        copy /y "dist\PCMod.exe" "PCMod.exe" >nul
        echo [SUCCESS] Standalone PCMod.exe created successfully in the root folder!
    ) else (
        echo [WARNING] Dist folder produced output but dist\PCMod.exe was not found.
    )
) else (
    echo.
    echo [ERROR] PyInstaller build failed with exit code %errorlevel%.
)

echo.
pause
