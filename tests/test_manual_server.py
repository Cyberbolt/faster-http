#!/usr/bin/env python
"""Manual test with a simple HTTP server."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faster_http as http
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import time

def run_server(port):
    """Run a simple HTTP server."""
    server = HTTPServer(('127.0.0.1', port), SimpleHTTPRequestHandler)
    server.serve_forever()

def test():
    # Start server in background
    port = 8888
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()
    time.sleep(1)  # Wait for server to start
    
    print(f"Testing sync client with http://127.0.0.1:{port}/")
    
    try:
        client = http.Client()
        response = client.get(f"http://127.0.0.1:{port}/")
        print(f"✅ SUCCESS! Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    success = test()
    sys.exit(0 if success else 1)