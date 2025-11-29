#!/usr/bin/env python3
"""
Smart Task Analyzer - Backend Server Launcher (improved logging)
"""

import os
import sys
import subprocess
from pathlib import Path

BACKEND_DIR = Path(__file__).parent / "backend"

def check_dependencies():
    print("🔍 Checking dependencies...")
    try:
        import django
        import rest_framework
        print("✅ Django and Django REST Framework are importable")
        return True
    except Exception as e:
        print(f"❌ Dependency import failed: {e!s}")
        print("📦 Try installing requirements:")
        print(f"   python -m pip install -r {BACKEND_DIR / 'requirements.txt'}")
        return False

def run_cmd(cmd, cwd=None, env=None):
    """Run command and show output in real time, return returncode."""
    print(f"🧭 Running: {' '.join(cmd)} (cwd={cwd})")
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        if proc.stdout:
            print("--- STDOUT ---")
            print(proc.stdout)
        if proc.stderr:
            print("--- STDERR ---")
            print(proc.stderr)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit {e.returncode}")
        if e.stdout:
            print("--- STDOUT ---")
            print(e.stdout)
        if e.stderr:
            print("--- STDERR ---")
            print(e.stderr)
        return e.returncode
    except Exception as e:
        print(f"❌ Unexpected error running command: {e!s}")
        return 1

def main():
    print("=" * 60)
    print("🚀 Smart Task Analyzer - Backend Server (launcher)")
    print("=" * 60)

    print("Python executable:", sys.executable)
    print("Working dir:", Path.cwd())

    if not BACKEND_DIR.exists():
        print(f"❌ Backend directory not found at {BACKEND_DIR}")
        sys.exit(1)

    if not check_dependencies():
        print("❌ Install dependencies and retry.")
        sys.exit(1)

    # ensure manage.py exists
    manage = BACKEND_DIR / "manage.py"
    if not manage.exists():
        print(f"❌ manage.py not found at {manage}")
        sys.exit(1)

    # Optionally export env var for settings if your project requires it:
    env = os.environ.copy()
    # Example: env['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'

    # Run makemigrations and migrate with captured output
    rc = run_cmd([sys.executable, "manage.py", "makemigrations"], cwd=str(BACKEND_DIR), env=env)
    if rc != 0:
        sys.exit(rc)

    rc = run_cmd([sys.executable, "manage.py", "migrate"], cwd=str(BACKEND_DIR), env=env)
    if rc != 0:
        sys.exit(rc)

    print("🌐 Starting Django backend on http://127.0.0.1:8000")
    print("📝 Press Ctrl+C to stop the server")
    print("=" * 60)

    # Start server WITHOUT check=True so the process inherits terminal and you see logs live
    try:
        subprocess.run([sys.executable, "manage.py", "runserver", "127.0.0.1:8000"], cwd=str(BACKEND_DIR), env=env)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e!s}")
        sys.exit(1)

if __name__ == "__main__":
    main()
