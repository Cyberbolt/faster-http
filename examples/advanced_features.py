#!/usr/bin/env python3
"""
Advanced Features Demo for faster_http.

This example demonstrates advanced httpx-compatible features:
- Authentication (BasicAuth, DigestAuth, NetRCAuth)
- Cookies (sending and receiving)
- Headers and helper classes
- Timeouts and proxy support
- Streaming responses
- Error handling
"""

import asyncio
import faster_http
from faster_http import (
    BasicAuth, DigestAuth, NetRCAuth,
    Headers, Cookies, QueryParams, Timeout,
    Client, AsyncClient, stream
)


def demo_authentication():
    """Demonstrate authentication features."""
    print("🔐 Authentication Demo")
    print("=" * 50)
    
    # 1. BasicAuth
    print("1. BasicAuth:")
    auth = BasicAuth("demo_user", "demo_password")
    try:
        response = faster_http.get("https://httpbin.org/get", auth=auth)
        print(f"   Status: {response.status_code}")
    except Exception as e:
        print(f"   Note: {e}")
    
    # 2. DigestAuth
    print("\n2. DigestAuth:")
    digest_auth = DigestAuth("digest_user", "digest_pass")
    print(f"   Created: {digest_auth}")
    
    # 3. NetRCAuth
    print("\n3. NetRCAuth:")
    netrc_auth = NetRCAuth()
    print(f"   NetRC file: {netrc_auth.file}")
    
    # 4. Auth with Client
    print("\n4. Client with Authentication:")
    with Client(auth=(auth.username, auth.password)) as client:
        try:
            response = client.get("https://httpbin.org/get")
            print(f"   Client auth status: {response.status_code}")
        except Exception as e:
            print(f"   Note: {e}")
    
    print()


def demo_cookies():
    """Demonstrate cookies functionality."""
    print("🍪 Cookies Demo")
    print("=" * 50)
    
    # 1. Sending cookies
    print("1. Sending cookies:")
    cookies = {"session_id": "abc123", "user_pref": "dark_mode"}
    response = faster_http.get("https://httpbin.org/cookies", cookies=cookies)
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Server received: {data.get('cookies', {})}")
    
    # 2. Client with default cookies
    print("\n2. Client with default cookies:")
    with Client(cookies={"client_cookie": "persistent"}) as client:
        response = client.get("https://httpbin.org/cookies")
        data = response.json()
        print(f"   Default cookies sent: {data.get('cookies', {})}")
    
    # 3. Response cookies
    print("\n3. Response cookies:")
    response = faster_http.get("https://httpbin.org/get")
    print(f"   Response cookies: {response.cookies}")
    print(f"   Cookies type: {type(response.cookies)}")
    
    print()


def demo_helper_classes():
    """Demonstrate helper classes."""
    print("🛠️ Helper Classes Demo")
    print("=" * 50)
    
    # 1. Headers (case-insensitive)
    print("1. Case-insensitive Headers:")
    headers = Headers({
        "User-Agent": "faster-http-demo/1.0",
        "Content-Type": "application/json"
    })
    headers["X-Custom"] = "custom-value"
    print(f"   Content-Type: {headers['content-type']}")  # lowercase
    print(f"   X-Custom: {headers['x-custom']}")         # lowercase
    
    # 2. Cookies class
    print("\n2. Cookies class:")
    cookies = Cookies()
    cookies.set("session", "value123", domain="example.com")
    cookies["preference"] = "setting"
    print(f"   Session: {cookies['session']}")
    print(f"   Preference: {cookies['preference']}")
    
    # 3. QueryParams
    print("\n3. QueryParams:")
    params_dict = QueryParams({"search": "python", "limit": "10"})
    params_str = QueryParams("?category=tech&sort=date")
    print(f"   From dict: {dict(params_dict)}")
    print(f"   From string: {dict(params_str)}")
    
    # 4. Timeout
    print("\n4. Timeout:")
    timeout = Timeout(connect=5.0, read=30.0, write=10.0)
    print(f"   Connect: {timeout.connect}s")
    print(f"   Read: {timeout.read}s")
    print(f"   Write: {timeout.write}s")
    
    print()


def demo_streaming():
    """Demonstrate streaming features."""
    print("🌊 Streaming Demo")
    print("=" * 50)
    
    # 1. Basic streaming
    print("1. Basic streaming response:")
    try:
        with stream("GET", "https://httpbin.org/get") as response:
            print(f"   Status: {response.status_code}")
            print(f"   Headers available: {bool(response.headers)}")
    except Exception as e:
        print(f"   Note: {e}")
    
    # 2. Response iteration methods
    print("\n2. Response iteration:")
    response = faster_http.get("https://httpbin.org/json")
    
    # Iterate over bytes
    byte_chunks = response.iter_bytes(chunk_size=100)
    print(f"   Byte chunks: {len(byte_chunks)}")
    
    # Iterate over text
    text_chunks = response.iter_text(chunk_size=50)
    print(f"   Text chunks: {len(text_chunks)}")
    
    # Iterate over lines
    lines = response.iter_lines()
    print(f"   Lines: {len(lines)}")
    
    print()


def demo_advanced_requests():
    """Demonstrate advanced request features."""
    print("⚡ Advanced Requests Demo")
    print("=" * 50)
    
    # 1. Complex request with all parameters
    print("1. Complex request:")
    headers = Headers({"X-Demo": "advanced"})
    cookies = {"demo": "session"}
    params = {"test": "value", "demo": "true"}
    timeout = Timeout(read=15.0)
    
    response = faster_http.get(
        "https://httpbin.org/get",
        params=params,
        headers=headers,
        cookies=cookies,
        timeout=timeout.read,
        follow_redirects=True
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Query params: {data.get('args', {})}")
    print(f"   Custom header: {data.get('headers', {}).get('X-Demo')}")
    
    # 2. POST with JSON and files
    print("\n2. POST with mixed content:")
    json_data = {"name": "faster_http", "version": "latest"}
    response = faster_http.post(
        "https://httpbin.org/post",
        json=json_data,
        headers={"X-Upload": "demo"}
    )
    print(f"   POST status: {response.status_code}")
    
    # 3. File upload
    print("\n3. File upload:")
    files = {"demo_file": b"Demo file content for upload"}
    response = faster_http.post("https://httpbin.org/post", files=files)
    print(f"   File upload status: {response.status_code}")
    
    print()


async def demo_async_features():
    """Demonstrate async features."""
    print("🚀 Async Features Demo")
    print("=" * 50)
    
    # 1. Async client with all features
    print("1. Async client with advanced features:")
    headers = Headers({"X-Async": "demo"})
    cookies = {"async_session": "active"}
    
    async with AsyncClient(
        headers=headers,
        cookies=cookies,
        timeout=30
    ) as client:
        response = await client.get("https://httpbin.org/get")
        print(f"   Async status: {response.status_code}")
        data = response.json()
        print(f"   Async header: {data.get('headers', {}).get('X-Async')}")
    
    # 2. Concurrent async requests
    print("\n2. Concurrent requests:")
    urls = [
        "https://httpbin.org/get?id=1",
        "https://httpbin.org/get?id=2",
        "https://httpbin.org/get?id=3"
    ]
    
    async with AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        
        for i, response in enumerate(responses, 1):
            data = response.json()
            print(f"   Request {i}: {data.get('args', {})}")
    
    # 3. Async with auth
    print("\n3. Async with authentication:")
    auth = BasicAuth("async_user", "async_pass")
    async with AsyncClient(auth=(auth.username, auth.password)) as client:
        response = await client.get("https://httpbin.org/get")
        print(f"   Auth async status: {response.status_code}")
    
    print()


def demo_error_handling():
    """Demonstrate error handling."""
    print("⚠️ Error Handling Demo")
    print("=" * 50)
    
    # 1. HTTP errors
    print("1. HTTP error handling:")
    try:
        response = faster_http.get("https://httpbin.org/status/404")
        print(f"   404 status: {response.status_code}")
        print(f"   Is client error: {response.is_client_error}")
        response.raise_for_status()
    except faster_http.HTTPError as e:
        print(f"   ✓ Caught HTTPError: {type(e).__name__}")
    
    # 2. Timeout errors
    print("\n2. Timeout handling:")
    try:
        response = faster_http.get("https://httpbin.org/delay/5", timeout=1.0)
    except Exception as e:
        print(f"   ✓ Caught timeout: {type(e).__name__}")
    
    # 3. Connection errors
    print("\n3. Connection error handling:")
    try:
        response = faster_http.get("http://127.0.0.1:9999", timeout=1.0)
    except Exception as e:
        print(f"   ✓ Caught connection error: {type(e).__name__}")
    
    print()


def demo_httpx_compatibility():
    """Demonstrate httpx compatibility."""
    print("🔄 httpx Compatibility Demo")
    print("=" * 50)
    
    # Use faster_http as httpx replacement
    import faster_http as httpx
    
    print("1. As httpx replacement:")
    response = httpx.get("https://httpbin.org/get")
    print(f"   httpx.get() status: {response.status_code}")
    
    with httpx.Client() as client:
        response = client.get("https://httpbin.org/get")
        print(f"   httpx.Client status: {response.status_code}")
    
    print("\n2. Response compatibility:")
    response = faster_http.get("https://httpbin.org/get")
    
    # Check httpx attributes
    httpx_attrs = [
        'status_code', 'headers', 'url', 'ok', 'content', 'text',
        'encoding', 'elapsed', 'http_version', 'cookies',
        'is_client_error', 'is_server_error', 'is_redirect',
        'json', 'raise_for_status'
    ]
    
    missing = [attr for attr in httpx_attrs if not hasattr(response, attr)]
    if missing:
        print(f"   ❌ Missing: {missing}")
    else:
        print("   ✅ All httpx attributes present")
    
    print()


def main():
    """Run all advanced feature demos."""
    print("🎯 faster-http: Advanced Features Demo")
    print("=" * 60)
    print("Demonstrating advanced httpx-compatible features\n")
    
    try:
        # Synchronous demos
        demo_authentication()
        demo_cookies()
        demo_helper_classes()
        demo_streaming()
        demo_advanced_requests()
        demo_error_handling()
        demo_httpx_compatibility()
        
        # Asynchronous demo
        print("Running async features demo...")
        asyncio.run(demo_async_features())
        
        print("🎉 All advanced features demo completed!")
        print("\n📋 Summary of advanced features:")
        print("✅ Authentication (BasicAuth, DigestAuth, NetRCAuth)")
        print("✅ Cookies (sending and receiving)")
        print("✅ Helper classes (Headers, Cookies, QueryParams, Timeout)")
        print("✅ Streaming responses and iteration")
        print("✅ Advanced request parameters")
        print("✅ Async client with all features")
        print("✅ Comprehensive error handling")
        print("✅ Complete httpx compatibility")
        print("\n🚀 faster-http provides enterprise-grade HTTP client features!")
        
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 