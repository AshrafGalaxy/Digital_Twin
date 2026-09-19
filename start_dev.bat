@echo off
REM ==============================================================================
REM start_dev.bat - Interactive Dev Launcher for Digital Twin Platform
REM Spawns a dedicated, fully interactive terminal window with Ctrl+C support
REM ==============================================================================
echo [+] Starting Digital Twin in dedicated interactive console window...
start "Digital Twin Dev Platform" powershell -NoExit -ExecutionPolicy Bypass -File "%~dp0start_dev.ps1" -Interactive
