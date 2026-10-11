@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title BVB News Desk - Diagnose
echo ====================================================
echo BVB News Desk Diagnostic
echo ====================================================
echo.
echo [1] Current folder:
echo %CD%
echo.
echo [2] Required files:
for %%F in (BVB_Server.ps1 index.html app.js styles.css materials-data.js collection-core.js news-sources.json) do (
 if exist "%%F" (echo [OK] %%F) else (echo [MISSING] %%F)
)
echo.
echo [3] Windows PowerShell:
where powershell.exe 2>nul
powershell.exe -NoLogo -NoProfile -Command "Write-Host ('PowerShell version: ' + $PSVersionTable.PSVersion.ToString())"
echo.
echo [4] Port 18986 connections (may be blank):
netstat -ano | findstr :18986
echo.
echo [5] Open local status check (only when server is running):
echo http://127.0.0.1:18986/api/status
echo.
echo Please send a screenshot of this window with the startup error.
pause
