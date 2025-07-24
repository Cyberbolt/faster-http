#!/usr/bin/env python3
"""
Test script to verify new faster-http features
"""

import asyncio
import sys
import traceback
from typing import Dict, Any

import faster_http

def test_event_hooks():
    """Test event hooks functionality"""
    print("=== Testing Event Hooks ===")
    
    request_logs = []
    response_logs = []
    
    def log_request(request):
        request_logs.append(f"Request: {request.method} {request.url}")
    
    def log_response(response):
        response_logs.append(f"Response: {response.status_code}")
    
    # Test synchronous client with event hooks
    hooks = {
        'request': [log_request],
        'response': [log_response]
    }
    
    try:
        with faster_http.Client(event_hooks=hooks) as client:
            response = client.get('https://httpbin.org/get')
            print(f"Status: {response.status_code}")
            print(f"Request logs: {request_logs}")
            print(f"Response logs: {response_logs}")
            assert len(request_logs) > 0, "Request hooks should be called"
            assert len(response_logs) > 0, "Response hooks should be called"
        print("✓ Event hooks working")
    except Exception as e:
        print(f"✗ Event hooks failed: {e}")
        traceback.print_exc()

def test_limits_config():
    """Test connection limits configuration"""
    print("\n=== Testing Limits Configuration ===")
    
    try:
        limits = faster_http.Limits(
            max_keepalive_connections=10,
            max_connections=50,
            keepalive_expiry=3.0
        )
        
        with faster_http.Client(limits=limits) as client:
            response = client.get('https://httpbin.org/get')
            print(f"Status: {response.status_code}")
            print(f"Limits - max_keepalive: {limits.max_keepalive_connections}")
            print(f"Limits - max_connections: {limits.max_connections}")
            print(f"Limits - keepalive_expiry: {limits.keepalive_expiry}")
            
        print("✓ Limits configuration working")
    except Exception as e:
        print(f"✗ Limits configuration failed: {e}")
        traceback.print_exc()

def test_exception_hierarchy():
    """Test new exception types"""
    print("\n=== Testing Exception Hierarchy ===")
    
    # Test that exceptions are properly imported
    exceptions_to_test = [
        'HTTPError', 'ConnectError', 'ConnectTimeout', 'TimeoutException',
        'ReadTimeout', 'WriteTimeout', 'PoolTimeout', 'RequestError',
        'ResponseError', 'HTTPStatusError', 'ClientError', 'ServerError',
        'StreamError', 'StreamConsumed', 'StreamClosed', 'ProtocolError',
        'DecodingError', 'TooManyRedirects', 'TransportError', 'ProxyError',
        'SSLError', 'CertificateError', 'NetworkError', 'DNSError'
    ]
    
    try:
        for exc_name in exceptions_to_test:
            exc_class = getattr(faster_http, exc_name)
            print(f"  {exc_name}: {exc_class}")
        print("✓ All exception types imported successfully")
    except Exception as e:
        print(f"✗ Exception hierarchy test failed: {e}")
        traceback.print_exc()

def test_response_features():
    """Test enhanced response features"""
    print("\n=== Testing Response Features ===")
    
    try:
        with faster_http.Client() as client:
            response = client.get('https://httpbin.org/get')
            
            # Test new response methods
            print(f"Status: {response.status_code}")
            print(f"Reason phrase: {response.reason_phrase}")
            print(f"Is success: {response.is_success}")
            print(f"Is client error: {response.is_client_error}")
            print(f"Is server error: {response.is_server_error}")
            print(f"Has redirect location: {response.has_redirect_location}")
            print(f"Links: {response.links}")
            
            # Test extensions
            response.set_extension('test_key', 'test_value')
            assert response.has_extension('test_key'), "Extension should be set"
            assert response.get_extension('test_key') == 'test_value', "Extension value should match"
            
        print("✓ Response features working")
    except Exception as e:
        print(f"✗ Response features failed: {e}")
        traceback.print_exc()

async def test_async_streaming():
    """Test async streaming functionality"""
    print("\n=== Testing Async Streaming ===")
    
    try:
        async with faster_http.AsyncClient() as client:
            # Get streaming response
            response = await client.stream('GET', 'https://httpbin.org/get')
            
            print(f"Status: {response.status_code}")
            
            # Test async iteration methods
            chunks = await response.aiter_bytes()
            print(f"Received {len(chunks)} byte chunks")
            
            lines = await response.aiter_lines()
            print(f"Received {len(lines)} lines")
            
            # Close the response
            await response.aclose()
                
        print("✓ Async streaming working")
    except Exception as e:
        print(f"✗ Async streaming failed: {e}")
        traceback.print_exc()

def test_auth_types():
    """Test authentication types"""
    print("\n=== Testing Authentication Types ===")
    
    try:
        # Test BasicAuth
        basic_auth = faster_http.BasicAuth('user', 'pass')
        print(f"BasicAuth: {basic_auth}")
        print(f"Username: {basic_auth.username}")
        
        # Test DigestAuth
        digest_auth = faster_http.DigestAuth('user', 'pass')
        print(f"DigestAuth: {digest_auth}")
        
        # Test NetRCAuth
        netrc_auth = faster_http.NetRCAuth()
        print(f"NetRCAuth: {netrc_auth}")
        
        print("✓ Authentication types working")
    except Exception as e:
        print(f"✗ Authentication types failed: {e}")
        traceback.print_exc()

def main():
    """Run all tests"""
    print("Testing faster-http new features...\n")
    
    # Test basic features first
    test_exception_hierarchy()
    test_auth_types()
    test_limits_config()
    test_response_features()
    test_event_hooks()
    
    # Test async features
    print("\n=== Running Async Tests ===")
    try:
        asyncio.run(test_async_streaming())
    except Exception as e:
        print(f"✗ Async tests failed: {e}")
        traceback.print_exc()
    
    print("\n=== All Tests Completed ===")

if __name__ == "__main__":
    main()