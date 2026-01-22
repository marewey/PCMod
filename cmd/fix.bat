@echo off
:: Check for Admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.Please run as Administrator
    pause
    exit
)

echo Unblocking PCMod Launcher files...
powershell -Command "dir '%~dp0\..' -Recurse | Unblock-File"
echo Done! You can now run PCMod.hta
pause