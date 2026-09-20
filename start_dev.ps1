param(
    [switch]$Interactive,
    [switch]$NewWindow
)

# Enforce UTF-8 console output encoding to eliminate Windows code-page artifacts
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$RootDir = $PSScriptRoot
if (-not $RootDir) {
    $RootDir = (Get-Location).Path
}

# 0. Check if running in a non-interactive output panel (e.g., VS Code Output tab / Code Runner)
$IsRedirected = $false
try {
    $IsRedirected = [Console]::IsInputRedirected
} catch {
    $IsRedirected = $false
}

if ((-not $Interactive) -and ($NewWindow -or $IsRedirected)) {
    Write-Host "[+] Non-interactive Output panel detected." -ForegroundColor Cyan
    Write-Host "[+] Spawning dedicated interactive terminal window (with Ctrl+C support)..." -ForegroundColor Green
    $targetScript = if ($PSCommandPath) { $PSCommandPath } else { "$RootDir\start_dev.ps1" }
    Start-Process powershell.exe -ArgumentList "-NoExit", "-ExecutionPolicy Bypass", "-File `"$targetScript`" -Interactive"
    exit 0
}

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "               DIGITAL TWIN - SMART CITY ANALYTICS PLATFORM                   " -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

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
