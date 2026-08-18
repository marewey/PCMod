@echo off
@setlocal EnableDelayedExpansion Enableextensions
title PCMod Python Bootstrap

echo ==========================================
echo       PCMod Launcher Python Bootstrap
echo ==========================================
echo.

:: Check if Python is installed
set PYTHON_CMD=
py --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :check_deps
)

python --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :check_deps
)

:: Python is not found, install the bundled Python
echo Python is not installed.
if not exist "bin\python-3.8.10-amd64.exe" (
    echo [ERROR] Bundled Python installer "bin\python-3.8.10-amd64.exe" not found!
    echo Please install Python manually from python.org
    pause
    exit /b 1
)

echo.
echo Installing Python 3.8.10...
echo This may take a minute. Please wait...
start /wait "" "bin\python-3.8.10-amd64.exe" /passive InstallAllUsers=0 Include_pip=1 PrependPath=1 SimpleInstall=1

if %errorlevel% neq 0 (
    echo [ERROR] Python installation failed with exit code %errorlevel%
    pause
    exit /b 1
)
echo Python installation [DONE]

:: Refresh system path variables
if exist "bin\refreshenv.cmd" (
    echo Refreshing environment variables...
    call "bin\refreshenv.cmd" >nul
)

:: Recheck Python
py --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :check_deps
)

python --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :check_deps
)

:: If still not found, try common local AppData Python paths
set "LOCAL_PY=%USERPROFILE%\AppData\Local\Programs\Python\Python38\python.exe"
if exist "%LOCAL_PY%" (
    set "PYTHON_CMD="%LOCAL_PY%""
    goto :check_deps
)

echo [ERROR] Python was installed but is still not found in the PATH.
echo Please restart your computer or command prompt and try again.
pause
exit /b 1

:check_deps
echo Python is installed. Using:
!PYTHON_CMD! --version

:: Ensure pip is installed and upgraded
echo.
echo Checking and installing required dependencies...

echo - Upgrading pip...
!PYTHON_CMD! -m pip install --upgrade pip >nul 2>nul

echo - Checking and installing portablemc...
!PYTHON_CMD! -m pip show portablemc >nul 2>nul
if %errorlevel% neq 0 (
    echo   Installing portablemc...
    !PYTHON_CMD! -m pip install portablemc
) else (
    echo   portablemc is already installed.
)

echo - Checking and installing pywebview...
!PYTHON_CMD! -m pip show pywebview >nul 2>nul
if %errorlevel% neq 0 (
    echo   Installing pywebview...
    !PYTHON_CMD! -m pip install pywebview
) else (
    echo   pywebview is already installed.
)

echo.
echo All dependencies verified successfully!
echo Launching PCMod Launcher...
start "" !PYTHON_CMD! PCMod.py
exit /b 0
