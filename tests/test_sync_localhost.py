#!/usr/bin/env python
"""Test sync client localhost connection after fixes."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faster_http as http
from tests.utils.test_server import HTTPTestServer

def test_sync_client_localhost():
    """Test if sync client can connect to localhost after all fixes."""
    server = HTTPTestServer(host="127.0.0.1", port=0)
    server.start()
    
    try:
        print(f"Test server running at: {server.base_url}")
        
        # Test sync client
        print("\nTesting sync client (Client):")
        client = http.Client(timeout=2)
        response = client.get(f"{server.base_url}/get")
        print(f"✅ Status: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
        
    finally:
        server.stop()

if __name__ == "__main__":
    success = test_sync_client_localhost()
    if success:
        print("\n🎉 SUCCESS: Sync client can now connect to localhost!")
    else:
        print("\n❌ FAILED: Sync client still cannot connect to localhost")