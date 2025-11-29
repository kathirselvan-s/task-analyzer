#!/usr/bin/env python3
"""
Smart Task Analyzer - Simple Application Launcher
Runs both Django backend and serves frontend in a single command.
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
import signal
from pathlib import Path
import http.server
import socketserver
from urllib.parse import urlparse

# Configuration
BACKEND_PORT = 8000
FRONTEND_PORT = 8080
BACKEND_DIR = Path(__file__).parent / "backend"
FRONTEND_DIR = Path(__file__).parent / "frontend"

def run_django_backend():
    """Run Django development server."""
    try:
        print("🚀 Starting Django backend server...")

        # Change to backend directory
        original_dir = os.getcwd()
        os.chdir(BACKEND_DIR)

        # Run migrations first
        print("📊 Running database migrations...")
        result1 = subprocess.run([sys.executable, "manage.py", "makemigrations"],
                                capture_output=True, text=True, cwd=BACKEND_DIR)
        result2 = subprocess.run([sys.executable, "manage.py", "migrate"],
                                capture_output=True, text=True, cwd=BACKEND_DIR)

        if result1.returncode != 0 or result2.returncode != 0:
            print(f"❌ Migration error: {result1.stderr or result2.stderr}")
            return

        # Start Django server
        print(f"🌐 Django backend starting on http://127.0.0.1:{BACKEND_PORT}")
        subprocess.run([sys.executable, "manage.py", "runserver", f"127.0.0.1:{BACKEND_PORT}"],
                      cwd=BACKEND_DIR)

    except Exception as e:
        print(f"❌ Backend startup error: {e}")
    finally:
        # Restore original directory
        os.chdir(original_dir)

def run_frontend_server():
    """Run simple HTTP server for frontend."""
    try:
        print("🎨 Starting frontend server...")

        # Change to frontend directory
        original_dir = os.getcwd()
        os.chdir(FRONTEND_DIR)

        class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                # Add CORS headers for API communication
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                super().end_headers()

            def do_OPTIONS(self):
                self.send_response(200)
                self.end_headers()

            def log_message(self, format, *args):
                # Suppress default logging to reduce noise
                pass

        with socketserver.TCPServer(("", FRONTEND_PORT), CustomHTTPRequestHandler) as httpd:
            print(f"🌐 Frontend server starting on http://localhost:{FRONTEND_PORT}")
            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
    except Exception as e:
        print(f"❌ Frontend server error: {e}")
    finally:
        # Restore original directory
        os.chdir(original_dir)

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")

    try:
        import django
        from rest_framework import status
        print("✅ Django and Django REST Framework found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Please install required packages:")
        print(f"   pip install -r {BACKEND_DIR / 'requirements.txt'}")
        return False

def open_browser():
    """Open browser after servers start."""
    time.sleep(3)  # Wait for servers to start
    print("🌐 Opening browser...")
    webbrowser.open(f"http://localhost:{FRONTEND_PORT}")

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n🛑 Shutting down Smart Task Analyzer...")
    print("✅ Goodbye!")
    sys.exit(0)

def main():
    """Main application launcher."""
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 60)
    print("🎯 Smart Task Analyzer - Application Launcher")
    print("=" * 60)

    # Check if we're in the right directory
    if not BACKEND_DIR.exists() or not FRONTEND_DIR.exists():
        print("❌ Error: Backend or frontend directory not found!")
        print(f"   Expected backend at: {BACKEND_DIR}")
        print(f"   Expected frontend at: {FRONTEND_DIR}")
        print("   Please run this script from the task-analyzer directory.")
        sys.exit(1)

    # Check dependencies
    if not check_dependencies():
        print("❌ Please install dependencies first and try again.")
        sys.exit(1)

    print("\n🚀 Starting Smart Task Analyzer...")
    print(f"   Backend API: http://127.0.0.1:{BACKEND_PORT}")
    print(f"   Frontend UI: http://localhost:{FRONTEND_PORT}")
    print("\n📝 Instructions:")
    print("   1. Wait for both servers to start")
    print("   2. Browser will open automatically")
    print("   3. Use Ctrl+C to stop both servers")
    print("\n" + "=" * 60)

    try:
        # Start backend in a separate thread
        backend_thread = threading.Thread(target=run_django_backend, daemon=True)
        backend_thread.start()

        # Start browser opener in a separate thread
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

        # Run frontend server in main thread (so Ctrl+C works)
        run_frontend_server()

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down Smart Task Analyzer...")
        print("✅ Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
