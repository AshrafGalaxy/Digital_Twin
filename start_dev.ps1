param(
    [switch]$NewWindow
)

# Enforce UTF-8 console output encoding
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$RootDir = $PSScriptRoot
if (-not $RootDir) {
    $RootDir = (Get-Location).Path
}

# Optional: Only spawn external window if explicitly requested via -NewWindow switch
if ($NewWindow) {
    $targetScript = if ($PSCommandPath) { $PSCommandPath } else { "$RootDir\start_dev.ps1" }
    Start-Process powershell.exe -ArgumentList "-NoExit", "-ExecutionPolicy Bypass", "-File `"$targetScript`""
    exit 0
}

$PythonBin = "$RootDir\.venv\Scripts\python.exe"

# 1. Verify or bootstrap Python virtual environment
if (-Not (Test-Path $PythonBin)) {
    Write-Host "[!] Virtual environment not detected at .venv" -ForegroundColor Yellow
    Write-Host "[+] Creating virtual environment..." -ForegroundColor Gray
    python -m venv "$RootDir\.venv"
    Write-Host "[+] Installing backend dependencies..." -ForegroundColor Gray
    & "$RootDir\.venv\Scripts\pip.exe" install -r "$RootDir\backend\requirements.txt"
}

# 2. Verify or install Frontend node packages
if (-Not (Test-Path "$RootDir\frontend\node_modules")) {
    Write-Host "[+] Installing frontend node packages..." -ForegroundColor Gray
    npm --prefix "$RootDir\frontend" install
}

# 3. Launch unified runner directly in current terminal
& $PythonBin "$RootDir\scripts\run_local.py"

