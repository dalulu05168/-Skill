@echo off
setlocal EnableExtensions
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 goto use_py
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 goto use_python
echo [Finance SKILL] Python 3.11+ was not found.
echo Please install Python 3.11+ first, then double-click this file again.
pause
exit /b 1

:use_py
set "PYTHON=py -3"
goto check

:use_python
set "PYTHON=python"
goto check

:check
%PYTHON% -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'; from zoneinfo import ZoneInfo; ZoneInfo('Europe/Bucharest')"
if errorlevel 1 (
  echo.
  echo [Finance SKILL] Python version or Romania timezone data is missing.
  echo On Windows, the timezone database may need a one-time installation:
  echo     %PYTHON% -m pip install tzdata
  echo Check Python is at least 3.11 and retry. No files were modified by this launcher.
  pause
  exit /b 2
)
echo [Finance SKILL] Starting local browser workspace...
%PYTHON% tools\finance_skill_api.py --open-browser
if errorlevel 1 (
  echo.
  echo [Finance SKILL] Startup failed. Please copy the error message above.
  pause
  exit /b 3
)
endlocal
