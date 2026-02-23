#!/usr/bin/env python3
import http.server
import socketserver
import os
import webbrowser
import sys
from pathlib import Path

# Get the directory where this script is located
BASE_DIR = Path(__file__).parent

# Default port
PORT = 8000
if len(sys.argv) > 1:
    try:
        PORT = int(sys.argv[1])
    except ValueError:
        print(f"Invalid port: {sys.argv[1]}, using default port {PORT}")

class NoCache(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that disables caching for easier development"""
    
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def log_message(self, format, *args):
        """Add timestamp to log messages"""
        print(f"[{self.log_date_time_string()}] {format % args}")

# Change to base directory so relative paths work
os.chdir(BASE_DIR)

try:
    with socketserver.TCPServer(("", PORT), NoCache) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"Starting Vermont Zoning Atlas server on {url}")
        print(f"Press Ctrl+C to stop the server")
        
        # Auto-open browser
        try:
            webbrowser.open(url)
            print(f"Opened {url} in your default browser")
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
        
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped")
except OSError as e:
    if e.errno == 48:  # Address already in use
        print(f"Error: Port {PORT} is already in use.")
        print(f"Try using a different port: python run_server.py 8001")
    else:
        print(f"Server error: {e}")
