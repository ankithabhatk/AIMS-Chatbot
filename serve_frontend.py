#!/usr/bin/env python3
"""
Simple HTTP server for frontend testing
Serves the chatbot UI and handles CORS properly
"""

import http.server
import socketserver
import os
from pathlib import Path


class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Clean log output
        if "GET" in format:
            print(f"   {args[0]} {args[1]}")


def main():
    # Change to frontend directory
    frontend_dir = Path(__file__).parent.parent / "frontend"
    os.chdir(frontend_dir)

    PORT = 5000
    Handler = MyHTTPRequestHandler

    print("\n" + "=" * 80)
    print("🚀 CHATBOT FRONTEND SERVER")
    print("=" * 80)
    print(f"\n📁 Serving from: {frontend_dir}")
    print(f"🌐 Local URL:    http://localhost:{PORT}")
    print(f"🌐 Open in browser: http://localhost:{PORT}/index.html")
    print(f"\n✅ Backend API:  http://localhost:8000")
    print("\n" + "=" * 80)
    print("Press Ctrl+C to stop the server\n")

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Server stopped.")
