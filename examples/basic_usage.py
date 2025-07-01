#!/usr/bin/env python3
"""
Basic usage examples for faster_http.

This demonstrates how to use faster_http as a drop-in replacement for httpx.
"""

import asyncio
import faster_http


def sync_examples():
    """Synchronous usage examples."""
    print("=== Synchronous Examples ===")
    
    # Basic GET request
    print("\n1. Basic GET request:")
    response = faster_http.get("https://httpbin.org/get")
    print(f"Status: {response.status_code}")
    print(f"URL: {response.url}")
    print(f"Headers: {dict(list(response.headers.items())[:3])}...")  # Show first 3 headers
    
    # GET with parameters
    print("\n2. GET with parameters:")
    params = {"param1": "value1", "param2": "value2"}
    response = faster_http.get("https://httpbin.org/get", params=params)
    data = response.json()
    print(f"Query args: {data['args']}")
    
    # POST with JSON
    print("\n3. POST with JSON:")
    json_data = {"name": "faster_http", "version": "0.1.0", "fast": True}
    response = faster_http.post("https://httpbin.org/post", json=json_data)
    data = response.json()
    print(f"Sent JSON: {data['json']}")
    
    # POST with form data
    print("\n4. POST with form data:")
    form_data = {"username": "testuser", "password": "secret123"}
    response = faster_http.post("https://httpbin.org/post", data=form_data)
    data = response.json()
    print(f"Form data: {data['form']}")
    
    # Custom headers
    print("\n5. Custom headers:")
    headers = {
        "User-Agent": "faster-http/0.1.0",
        "Authorization": "Bearer token123",
        "X-Custom-Header": "custom-value"
    }
    response = faster_http.get("https://httpbin.org/get", headers=headers)
    data = response.json()
    print(f"Sent headers: {data['headers']['User-Agent']}")
    print(f"Custom header: {data['headers']['X-Custom-Header']}")


def client_examples():
    """Client usage examples."""
    print("\n=== Client Examples ===")
    
    # Basic client usage
    print("\n1. Basic client:")
    with faster_http.Client() as client:
        response = client.get("https://httpbin.org/get")
        print(f"Status: {response.status_code}")
    
    # Client with base URL
    print("\n2. Client with base URL:")
    with faster_http.Client(base_url="https://httpbin.org") as client:
        response = client.get("/get")
        print(f"Full URL: {response.url}")
        
        response = client.post("/post", json={"message": "Hello from client!"})
        data = response.json()
        print(f"Posted: {data['json']['message']}")
    
    # Client with default headers
    print("\n3. Client with default headers:")
    headers = {"User-Agent": "faster-http-client/0.1.0"}
    with faster_http.Client(headers=headers) as client:
        response = client.get("https://httpbin.org/get")
        data = response.json()
        print(f"Default User-Agent: {data['headers']['User-Agent']}")
    
    # Client with timeout
    print("\n4. Client with timeout:")
    with faster_http.Client(timeout=5.0) as client:
        response = client.get("https://httpbin.org/delay/1")
        print(f"Request completed in {response.elapsed:.2f}s")


async def async_examples():
    """Asynchronous usage examples."""
    print("\n=== Asynchronous Examples ===")
    
    # Basic async request
    print("\n1. Basic async request:")
    async with faster_http.AsyncClient() as client:
        response = await client.get("https://httpbin.org/get")
        print(f"Async status: {response.status_code}")
    
    # Multiple concurrent requests
    print("\n2. Multiple concurrent requests:")
    urls = [
        "https://httpbin.org/get?id=1",
        "https://httpbin.org/get?id=2", 
        "https://httpbin.org/get?id=3",
        "https://httpbin.org/get?id=4",
        "https://httpbin.org/get?id=5"
    ]
    
    async with faster_http.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        
        for i, response in enumerate(responses):
            data = response.json()
            print(f"Request {i+1}: {data['args']}")
    
    # Async POST with JSON
    print("\n3. Async POST with JSON:")
    async with faster_http.AsyncClient() as client:
        json_data = {"async": True, "message": "Hello async world!"}
        response = await client.post("https://httpbin.org/post", json=json_data)
        data = response.json()
        print(f"Async POST result: {data['json']}")


def error_handling_examples():
    """Error handling examples."""
    print("\n=== Error Handling Examples ===")
    
    # Handle HTTP errors
    print("\n1. HTTP error handling:")
    try:
        response = faster_http.get("https://httpbin.org/status/404")
        print(f"Status: {response.status_code}")
        print(f"Is error: {not response.ok}")
        response.raise_for_status()  # This will raise an exception
    except faster_http.HTTPError as e:
        print(f"HTTP Error caught: {e}")
    
    # Handle connection errors
    print("\n2. Connection error handling:")
    try:
        response = faster_http.get("http://127.0.0.1:9999", timeout=1.0)
    except (faster_http.ConnectTimeout, faster_http.RequestError) as e:
        print(f"Connection error caught: {type(e).__name__}")
    
    # Handle timeout
    print("\n3. Timeout handling:")
    try:
        response = faster_http.get("https://httpbin.org/delay/10", timeout=2.0)
    except faster_http.ReadTimeout as e:
        print(f"Timeout error caught: {type(e).__name__}")


def response_features():
    """Response feature examples."""
    print("\n=== Response Features ===")
    
    response = faster_http.get("https://httpbin.org/json")
    
    print(f"Status code: {response.status_code}")
    print(f"OK: {response.ok}")
    print(f"URL: {response.url}")
    print(f"Elapsed time: {response.elapsed:.3f}s")
    print(f"Content length: {len(response.content)} bytes")
    print(f"Text length: {len(response.text)} characters")
    
    # JSON response
    data = response.json()
    print(f"JSON keys: {list(data.keys())}")
    
    # Response representation
    print(f"Response repr: {repr(response)}")
    
    # Status checks
    print(f"Is redirect: {response.is_redirect}")
    print(f"Is client error: {response.is_client_error}")
    print(f"Is server error: {response.is_server_error}")


def main():
    """Run all examples."""
    print("faster_http - Examples")
    print("=" * 50)
    
    sync_examples()
    client_examples()
    
    # Run async examples
    asyncio.run(async_examples())
    
    error_handling_examples()
    response_features()
    
    print("\n" + "=" * 50)
    print("All examples completed successfully!")


if __name__ == "__main__":
    main() 