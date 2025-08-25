#!/usr/bin/env python
"""Compare async vs sync client."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import faster_http as http
from tests.utils.test_server import HTTPTestServer

async def test_async():
    """Test async client."""
    server = HTTPTestServer(host="127.0.0.1", port=0)
    server.start()
    
    try:
        print(f"Server at: {server.base_url}")
        async with http.AsyncClient() as client:
            response = await client.get(f"{server.base_url}/get")
            print(f"AsyncClient: ✅ {response.status_code}")
            return True
    except Exception as e:
        print(f"AsyncClient: ❌ {e}")
        return False
    finally:
        server.stop()

def test_sync_simple():
    """Test sync client with simplest possible request."""
    # Try external service first
    print("\nTesting sync client with external service...")
    try:
        client = http.Client()
        response = client.get("http://httpbin.org/get")
        print(f"Sync + External: ✅ {response.status_code}")
    except Exception as e:
        print(f"Sync + External: ❌ {e}")
    
    # Now try localhost
    server = HTTPTestServer(host="127.0.0.1", port=0)
    server.start()
    
    try:
        print(f"\nTesting sync client with localhost ({server.base_url})...")
        client = http.Client()
        response = client.get(f"{server.base_url}/get")
        print(f"Sync + Localhost: ✅ {response.status_code}")
        return True
    except Exception as e:
        print(f"Sync + Localhost: ❌ {e}")
        return False
    finally:
        server.stop()

if __name__ == "__main__":
    print("=" * 50)
    print("Testing AsyncClient...")
    asyncio.run(test_async())
    
    print("=" * 50)
    test_sync_simple()