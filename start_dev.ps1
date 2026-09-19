# ==============================================================================
# start_dev.ps1 - Digital Twin One-Command Local Development Launcher
# Starts both FastAPI Backend (port 8000) and React/Vite Frontend (port 5173)
# ==============================================================================

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "               DIGITAL TWIN - SMART CITY ANALYTICS PLATFORM                   " -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

$RootDir = $PSScriptRoot
$PythonBin = "$RootDir\.venv\Scripts\python.exe"

# 1. Check Python virtual environment
if (-Not (Test-Path $PythonBin)) {
    Write-Host "[!] Virtual environment not detected at .venv" -ForegroundColor Yellow
    Write-Host "[+] Creating virtual environment..." -ForegroundColor Gray
    python -m venv "$RootDir\.venv"
    Write-Host "[+] Installing backend dependencies..." -ForegroundColor Gray
    & "$RootDir\.venv\Scripts\pip.exe" install -r "$RootDir\backend\requirements.txt"
}

# 2. Check Frontend node_modules
if (-Not (Test-Path "$RootDir\frontend\node_modules")) {
    Write-Host "[+] Installing frontend node packages..." -ForegroundColor Gray
    npm --prefix "$RootDir\frontend" install
}

# 3. Launch via unified runner
Write-Host "[+] Starting Digital Twin services..." -ForegroundColor Green
Write-Host ""

& $PythonBin "$RootDir\scripts\run_local.py"
