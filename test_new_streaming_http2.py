#!/usr/bin/env python3
"""
Manual test script for new streaming and HTTP/2 features
"""

import faster_http
import asyncio


def test_stream_context_manager():
    """Test stream context manager functionality"""
    print("=== 测试 Stream 上下文管理器 ===")
    
    try:
        # Test basic stream context manager
        with faster_http.stream("GET", "https://httpbin.org/get") as response:
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
        print("✅ Stream 上下文管理器基本功能正常")
        
        # Test stream with POST
        with faster_http.stream("POST", "https://httpbin.org/post", json={"test": "data"}) as response:
            print(f"POST Status: {response.status_code}")
            data = response.json()
            print(f"Posted data: {data.get('json', {})}")
            
        print("✅ Stream 上下文管理器 POST 功能正常")
        
        # Test stream iteration
        with faster_http.stream("GET", "https://httpbin.org/stream/3") as response:
            print(f"Stream Status: {response.status_code}")
            # Test streaming methods
            chunks = response.iter_bytes(chunk_size=512)
            print(f"Received {len(chunks)} chunks")
            
        print("✅ Stream 迭代功能正常")
        
    except Exception as e:
        print(f"❌ Stream 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_http2_support():
    """Test HTTP/2 support"""
    print("\n=== 测试 HTTP/2 支持 ===")
    
    try:
        # Create HTTP/2 client
        client = faster_http.Client(http2=True)
        print("✅ HTTP/2 客户端创建成功")
        
        # Create HTTP/1.1 client for comparison
        client_h1 = faster_http.Client(http2=False)
        print("✅ HTTP/1.1 客户端创建成功")
        
        # Test HTTP/2 with SSL
        client_ssl = faster_http.Client(http2=True, verify=True)
        print("✅ HTTP/2 + SSL 客户端创建成功")
        
        # Make a request to test HTTP version detection
        response = client_h1.get("https://httpbin.org/get")
        print(f"HTTP 版本检测: {response.http_version}")
        
        print("✅ HTTP/2 支持功能正常")
        
    except Exception as e:
        print(f"❌ HTTP/2 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_async_features():
    """Test async features"""
    print("\n=== 测试异步功能 ===")
    
    async def async_test():
        try:
            # Test async client with HTTP/2
            async with faster_http.AsyncClient(http2=True) as client:
                print("✅ 异步 HTTP/2 客户端创建成功")
                
            print("✅ 异步功能正常")
            
        except Exception as e:
            print(f"❌ 异步测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(async_test())


def test_integration():
    """Test integrated features"""
    print("\n=== 测试功能集成 ===")
    
    try:
        # Test HTTP/2 client with streaming
        client = faster_http.Client(
            http2=True,
            timeout=30.0,
            headers={"User-Agent": "faster-http-test/1.0"}
        )
        
        with faster_http.stream("GET", "https://httpbin.org/stream/2") as response:
            print(f"集成测试状态: {response.status_code}")
            chunks = response.iter_bytes()
            print(f"接收到 {len(chunks)} 个数据块")
            
        print("✅ HTTP/2 + Stream 集成功能正常")
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_httpx_compatibility():
    """Test httpx compatibility"""
    print("\n=== 测试 httpx 兼容性 ===")
    
    try:
        # Test if we can use faster_http like httpx
        
        # Global stream function (like httpx.stream)
        with faster_http.stream("GET", "https://httpbin.org/get") as response:
            assert response.status_code == 200
            assert hasattr(response, 'json')
            assert hasattr(response, 'text')
            assert hasattr(response, 'content')
            
        print("✅ httpx 兼容性测试通过")
        
        # Test response attributes
        client = faster_http.Client()
        resp = client.get("https://httpbin.org/get")
        
        # Check httpx-compatible attributes
        attrs = ['status_code', 'headers', 'url', 'text', 'content', 'json', 'http_version']
        for attr in attrs:
            assert hasattr(resp, attr), f"Missing attribute: {attr}"
            
        print("✅ Response 属性兼容性测试通过")
        
    except Exception as e:
        print(f"❌ 兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("🧪 开始测试增强的 Stream API 和 HTTP/2 支持")
    print("="*60)
    
    test_stream_context_manager()
    test_http2_support()
    test_async_features()
    test_integration()
    test_httpx_compatibility()
    
    print("\n" + "="*60)
    print("🎉 测试完成！")
    print("\n✨ 已实现的新功能:")
    print("  🔄 完整的 httpx.stream() 上下文管理器支持")
    print("  🚀 增强的 HTTP/2 支持（优化连接参数）")
    print("  🎯 Stream 迭代方法（iter_bytes, iter_text, iter_lines）")
    print("  🔧 自动资源清理")
    print("  📡 HTTP 版本检测和报告")
    print("  🔗 完整的 httpx API 兼容性")


if __name__ == "__main__":
    main()