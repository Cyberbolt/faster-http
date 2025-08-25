#!/usr/bin/env python
"""Simple test for sync client localhost connection."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faster_http as http
from tests.utils.test_server import HTTPTestServer
import time

def test():
    server = HTTPTestServer(host="127.0.0.1", port=0)
    server.start()
    
    try:
        print(f"Server at: {server.base_url}")
        client = http.Client()
        
        start = time.time()
        try:
            response = client.get(f"{server.base_url}/get")
            print(f"✅ SUCCESS! Status: {response.status_code}")
            print(f"Time: {time.time() - start:.2f}s")
            return True
        except Exception as e:
            print(f"❌ Failed after {time.time() - start:.2f}s: {e}")
            return False
    finally:
        server.stop()

if __name__ == "__main__":
    success = test()
    sys.exit(0 if success else 1)