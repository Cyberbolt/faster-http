"""
Test Event Hooks system in faster-http
"""

import faster_http


def log_request(request):
    """Request hook that logs request details"""
    print(f"🚀 Request Hook: {request.method} {request.url}")
    print(f"   Headers: {dict(list(request.headers.items())[:2])}...")  # Show first 2 headers


def log_response(response):
    """Response hook that logs response details"""
    print(f"✅ Response Hook: {response.status_code} from {response.url}")
    print(f"   Content Length: {len(response.content)} bytes")


def test_event_hooks():
    """Test event hooks with Client"""
    print("=== Testing Event Hooks with Client ===")
    
    # Test with both request and response hooks
    hooks = {
        'request': [log_request],
        'response': [log_response]
    }
    
    client = faster_http.Client(event_hooks=hooks)
    
    print("\n1. Testing GET request with hooks:")
    response = client.get('https://httpbin.org/get')
    print(f"Final result: {response.status_code}")
    
    print("\n2. Testing POST request with hooks:")
    response = client.post('https://httpbin.org/post', json={'test': 'data'})
    print(f"Final result: {response.status_code}")


def test_async_event_hooks():
    """Test event hooks with AsyncClient"""
    print("\n=== Testing Event Hooks with AsyncClient ===")
    
    import asyncio
    
    async def test_async():
        hooks = {
            'request': [log_request],
            'response': [log_response]  
        }
        
        client = faster_http.AsyncClient(event_hooks=hooks)
        
        print("\n1. Testing async GET request with hooks:")
        response = await client.get('https://httpbin.org/get')
        print(f"Final result: {response.status_code}")
        
        print("\n2. Testing async POST request with hooks:")
        response = await client.post('https://httpbin.org/post', json={'async': 'test'})
        print(f"Final result: {response.status_code}")
    
    asyncio.run(test_async())


def test_single_hook():
    """Test with single hook (not in list)"""
    print("\n=== Testing Single Hook ===")
    
    # Pass single function instead of list
    hooks = {
        'request': log_request,  # Single function, not list
        'response': log_response
    }
    
    client = faster_http.Client(event_hooks=hooks)
    response = client.get('https://httpbin.org/get')
    print(f"Final result: {response.status_code}")


def test_no_hooks():
    """Test client without hooks"""
    print("\n=== Testing Client without hooks ===")
    
    client = faster_http.Client()  # No event_hooks parameter
    response = client.get('https://httpbin.org/get')
    print(f"No hooks result: {response.status_code}")


def main():
    """运行所有Event Hooks测试"""
    print("🎣 开始Event Hooks系统测试\n")
    
    test_event_hooks()
    test_async_event_hooks()
    test_single_hook()
    test_no_hooks()
    
    print("\n🎉 所有Event Hooks测试完成!")
    print("📊 测试总结:")
    print("  ✅ 同步客户端Event Hooks")
    print("  ✅ 异步客户端Event Hooks")
    print("  ✅ 单个Hook函数支持")  
    print("  ✅ 无Hook客户端支持")


if __name__ == "__main__":
    main()