@echo off
setlocal
chcp 65001 >nul
title P004 Independent Director Studio
cd /d "%~dp0"
set "PYTHONUTF8=1"
echo ============================================
echo   NUVEXA P004 - Director / Writer Studio
echo   Local only - fictional education rehearsal
echo ============================================
echo.
where py >nul 2>nul
if not errorlevel 1 (
  echo Starting Python 3 (py launcher)...
  py -3 scripts\director_studio.py
  goto :finish
)
where python >nul 2>nul
if not errorlevel 1 (
  echo Starting Python (PATH)...
  python scripts\director_studio.py
  goto :finish
)
echo [ERROR] Python 3.11+ is required but was not found.
echo Install Python 3.11+ and enable the Windows Python launcher.
goto :finish
:finish
echo.
echo Director Studio stopped or could not start.
echo The window remains open for error inspection.
pause
endlocal
