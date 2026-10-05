@echo off
REM ==============================================================================
REM start_dev.bat - Local Development Launcher for Digital Twin Platform
REM Executes directly within the integrated IDE terminal.
REM ==============================================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_dev.ps1" %*
exit /b %ERRORLEVEL%
