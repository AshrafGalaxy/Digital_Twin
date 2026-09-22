"""
run_local.py

Unified local development launcher.
Starts both the FastAPI backend and React/Vite frontend in parallel,
prefixes their terminal logs, and handles clean graceful shutdown on Ctrl+C.

Usage:
    python scripts/run_local.py
"""

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"

PYTHON_BIN = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_banner():
    banner = f"""
{CYAN}{BOLD}==============================================================================
               DIGITAL TWIN — SMART CITY ANALYTICS PLATFORM
=============================================================================={RESET}
{GREEN}[OK] Backend API Server:{RESET}      http://localhost:8000
{GREEN}[OK] Swagger API Docs:{RESET}        http://localhost:8000/docs
{GREEN}[OK] Operations Dashboard:{RESET}    http://localhost:5173
{GREEN}[OK] WebSocket State Stream:{RESET}  ws://localhost:8000/api/v1/stream/state
------------------------------------------------------------------------------
{YELLOW}Tip:{RESET} Run {BOLD}python scripts/publish_stream.py{RESET} in another terminal to stream live telemetry!
{YELLOW}Press Ctrl+C anytime to stop both services.{RESET}
{CYAN}=============================================================================={RESET}
"""
    print(banner)

def stream_output(pipe, prefix, color):
    try:
        for line in iter(pipe.readline, ''):
            if not line:
                break
            clean_line = line.rstrip()
            if not clean_line:
                continue
            
            # Clean up unrendered arrow glyphs, Windows code-page artifacts (âžœ), and leading clutter
            clean_line = (
                clean_line
                .replace("âžœ", "")
                .replace("➜", "")
                .replace("\u279c", "")
                .strip()
            )
            
            if clean_line:
                print(f"{color}[{prefix}]{RESET} {clean_line}")
    except Exception:
        pass
    finally:
        pipe.close()

def wait_for_backend(host="127.0.0.1", port=8000, timeout=25.0):
    """
    Polls the backend health endpoint until it returns 200 OK or timeout expires.
    Prevents Vite from proxying into an uninitialized socket on startup.
    """
    import urllib.request
    url = f"http://{host}:{port}/health"
    start_time = time.time()
    print(f"{CYAN}[SYSTEM]{RESET} Waiting for FastAPI backend to prime database & initialize services...")
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DigitalTwin-HealthCheck"})
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.3)
    return False

def main():
    print_banner()

    backend_proc = None
    frontend_proc = None

    def cleanup(signum=None, frame=None):
        print(f"\n{YELLOW}[SYSTEM] Shutting down Digital Twin services...{RESET}")
        try:
            if sys.platform == "win32":
                if backend_proc and backend_proc.pid:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(backend_proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if frontend_proc and frontend_proc.pid:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(frontend_proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                if backend_proc:
                    backend_proc.terminate()
                if frontend_proc:
                    frontend_proc.terminate()
        except Exception:
            pass
        print(f"{GREEN}[SYSTEM] All services stopped cleanly. Goodbye!{RESET}")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # 1. Start Backend Process
    backend_cmd = [
        PYTHON_BIN, "-m", "uvicorn", "backend.main:app",
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ]
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    print(f"{CYAN}[SYSTEM]{RESET} Launching FastAPI backend on port 8000...")
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env
    )

    # Stream backend logs immediately so user sees startup progress
    t_backend = threading.Thread(target=stream_output, args=(backend_proc.stdout, "BACKEND", CYAN), daemon=True)
    t_backend.start()

    # 2. Wait for Backend Health Readiness before launching Vite
    backend_ready = wait_for_backend(host="127.0.0.1", port=8000, timeout=25.0)
    if backend_ready:
        print(f"{GREEN}[SYSTEM]{RESET} FastAPI backend ready & healthy at http://127.0.0.1:8000. Launching Vite frontend...")
    else:
        print(f"{YELLOW}[SYSTEM]{RESET} Backend health check timed out. Launching Vite frontend anyway...")

    # 3. Start Frontend Process
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_cmd = [npm_cmd, "run", "dev"]

    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=str(FRONTEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )

    t_frontend = threading.Thread(target=stream_output, args=(frontend_proc.stdout, "FRONTEND", GREEN), daemon=True)
    t_frontend.start()

    try:
        while True:
            time.sleep(0.5)
            # If any process terminated unexpectedly, notify
            if backend_proc and backend_proc.poll() is not None:
                print(f"{YELLOW}[SYSTEM] Backend process terminated (code {backend_proc.returncode}).{RESET}")
                break
            if frontend_proc and frontend_proc.poll() is not None:
                print(f"{YELLOW}[SYSTEM] Frontend process terminated (code {frontend_proc.returncode}).{RESET}")
                break
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
