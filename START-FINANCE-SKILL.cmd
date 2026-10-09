@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 tools\finance_skill_api.py --open-browser
  goto :eof
)
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  python tools\finance_skill_api.py --open-browser
  goto :eof
)
echo Python 3.11 or newer is required to start the Finance SKILL workspace.
echo Install Python from python.org, then start this file again.
pause
