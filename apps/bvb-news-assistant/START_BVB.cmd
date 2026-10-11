@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title BVB News Desk v5.0 - Windows Launcher

echo ====================================================
echo BVB News Desk v5.0 - Windows Launcher
echo ====================================================

echo Starting local service...
if not exist "%~dp0BVB_Server.ps1" (
    echo [ERROR] Missing BVB_Server.ps1.
    echo Please extract ALL files from the ZIP into one folder.
    pause
    exit /b 2
)
where powershell.exe >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Windows PowerShell was not found.
    echo Try Windows 10 or Windows 11 with PowerShell 5.1 installed.
    pause
    exit /b 3
)
echo.
echo Starting PowerShell server. Keep this window open.
echo A browser tab should open automatically.
echo If browser does not open, check the URL shown below.
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0BVB_Server.ps1"
set "BVB_EXIT=%ERRORLEVEL%"
echo.
echo [INFO] Server process finished. Exit code: %BVB_EXIT%
if not "%BVB_EXIT%"=="0" (
    echo [ERROR] Startup did not complete successfully.
    echo Please copy the LAST 10 lines shown above for troubleshooting.
)
pause
exit /b %BVB_EXIT%
