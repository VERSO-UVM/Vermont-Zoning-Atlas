#!/usr/bin/env python3
"""
Local server launcher for Vermont Zoning Atlas
Serves the website on http://localhost:8000
"""

import os
import sys
import webbrowser
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Change to the script directory
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add headers to prevent caching
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super().end_headers()

    def log_message(self, format, *args):
        # Custom logging
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_server(port=8000):
    """Start local HTTP server"""
    handler = MyHTTPRequestHandler
    server_address = ('', port)
    httpd = HTTPServer(server_address, handler)
    
    print("="*60)
    print("Vermont Zoning Atlas - Local Server")
    print("="*60)
    print(f"\n✓ Server started at: http://localhost:{port}")
    print(f"✓ Serving from: {script_dir}")
    print(f"\n→ Opening in browser in 2 seconds...")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Open browser after a short delay
    time.sleep(2)
    webbrowser.open(f'http://localhost:{port}/index-new.html')
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped.")
        sys.exit(0)

if __name__ == '__main__':
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Usage: python run_server.py [port]")
            print(f"Using default port: {port}")
    
    run_server(port)
