#!/usr/bin/env python3
"""
Smart Task Analyzer - Frontend Server Launcher
Starts only the frontend HTTP server.
"""

import os
import sys
import webbrowser
import time
import threading
from pathlib import Path
import http.server
import socketserver

# Configuration
FRONTEND_PORT = 8080
FRONTEND_DIR = Path(__file__).parent / "frontend"

def open_browser():
    """Open browser after server starts."""
    time.sleep(2)  # Wait for server to start
    print("🌐 Opening browser...")
    webbrowser.open(f"http://localhost:{FRONTEND_PORT}")

def main():
    """Start frontend HTTP server."""
    print("=" * 50)
    print("🎨 Smart Task Analyzer - Frontend Server")
    print("=" * 50)
    
    # Check if frontend directory exists
    if not FRONTEND_DIR.exists():
        print(f"❌ Error: Frontend directory not found at {FRONTEND_DIR}")
        sys.exit(1)
    
    try:
        # Change to frontend directory
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
        
        # Start browser opener in a separate thread
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start HTTP server
        with socketserver.TCPServer(("", FRONTEND_PORT), CustomHTTPRequestHandler) as httpd:
            print(f"🌐 Frontend server running on http://localhost:{FRONTEND_PORT}")
            print("📝 Press Ctrl+C to stop the server")
            print("=" * 50)
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
    except Exception as e:
        print(f"❌ Error starting frontend server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
