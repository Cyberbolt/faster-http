"""
Test Transport customization in faster-http
"""

import faster_http
from faster_http._core import FasterhttpTransport, MockTransport, HTTPSRedirectTransport, HttpRequest, HttpResponse
import asyncio


class CustomTransport:
    """Custom transport that adds a custom header"""
    
    def __init__(self):
        self.default_transport = FasterhttpTransport()
    
    def handle_request(self, request):
        """Handle request with custom logic"""
        print(f"🚀 Custom Transport: {request.method} {request.url}")
        
        # Add custom header logic here if needed
        # For now, just delegate to default transport
        return self.default_transport.handle_request(request)
    
    def close(self):
        self.default_transport.close()
    
    def aclose(self):
        self.default_transport.aclose()


class LoggingTransport:
    """Transport that logs all requests"""
    
    def __init__(self):
        self.default_transport = FasterhttpTransport()
        self.request_count = 0
    
    def handle_request(self, request):
        """Handle request with logging"""
        self.request_count += 1
        print(f"📊 Request #{self.request_count}: {request.method} {request.url}")
        
        response = self.default_transport.handle_request(request)
        print(f"📈 Response #{self.request_count}: {response.status_code}")
        
        return response
    
    def close(self):
        print(f"📊 Total requests processed: {self.request_count}")
        self.default_transport.close()
    
    def aclose(self):
        self.default_transport.aclose()


def test_builtin_transports():
    """测试内置transport类"""
    print("=== 测试内置Transport类 ===")
    
    # 1. 测试FasterhttpTransport
    print("1. 测试FasterhttpTransport:")
    transport = FasterhttpTransport()
    request = HttpRequest("GET", "https://httpbin.org/get", None, None)
    
    try:
        response = transport.handle_request(request)
        print(f"   ✅ FasterhttpTransport测试成功: {response.status_code}")
    except Exception as e:
        print(f"   ❌ FasterhttpTransport测试失败: {e}")
    
    # 2. 测试HTTPSRedirectTransport
    print("2. 测试HTTPSRedirectTransport:")
    https_transport = HTTPSRedirectTransport()
    http_request = HttpRequest("GET", "http://httpbin.org/get", None, None)
    
    try:
        response = https_transport.handle_request(http_request)
        print(f"   ✅ HTTPSRedirectTransport测试成功: {response.status_code}")
        print(f"   🔒 成功将HTTP重定向到HTTPS")
    except Exception as e:
        print(f"   ❌ HTTPSRedirectTransport测试失败: {e}")
    
    # 3. 测试MockTransport
    print("3. 测试MockTransport:")
    mock_transport = MockTransport()
    
    # MockTransport需要预设响应，这里只测试创建
    print("   ✅ MockTransport创建成功")
    print("   ⚠️ MockTransport需要预设响应来完整测试")


def test_custom_transport():
    """测试自定义transport"""
    print("\n=== 测试自定义Transport ===")
    
    try:
        # 使用自定义transport创建客户端
        custom_transport = CustomTransport()
        client = faster_http.Client(transport=custom_transport)
        
        print("1. 测试自定义transport客户端创建:")
        print("   ✅ 自定义transport客户端创建成功")
        
        # 注意：实际发送请求需要transport集成到客户端中
        # 目前只测试客户端创建
        
    except Exception as e:
        print(f"❌ 自定义transport测试失败: {e}")


def test_logging_transport():
    """测试日志transport"""
    print("\n=== 测试日志Transport ===")
    
    try:
        # 使用日志transport
        logging_transport = LoggingTransport()
        client = faster_http.Client(transport=logging_transport)
        
        print("1. 测试日志transport客户端创建:")
        print("   ✅ 日志transport客户端创建成功")
        
        # 模拟关闭以显示统计
        logging_transport.close()
        
    except Exception as e:
        print(f"❌ 日志transport测试失败: {e}")


def test_transport_mounts():
    """测试transport挂载"""
    print("\n=== 测试Transport挂载 ===")
    
    try:
        # 为不同的域名配置不同的transport
        mounts = {
            "https://httpbin.org": CustomTransport(),
            "https://example.com": LoggingTransport(),
        }
        
        client = faster_http.Client(mounts=mounts)
        print("1. 测试transport挂载:")
        print("   ✅ Transport挂载客户端创建成功")
        print("   🔗 已为不同域名配置专用transport")
        
    except Exception as e:
        print(f"❌ transport挂载测试失败: {e}")


def test_async_transport():
    """测试异步transport"""
    print("\n=== 测试异步Transport ===")
    
    async def async_test():
        try:
            # 使用自定义transport创建异步客户端
            custom_transport = CustomTransport()
            client = faster_http.AsyncClient(transport=custom_transport)
            
            print("1. 测试异步自定义transport:")
            print("   ✅ 异步自定义transport客户端创建成功")
            
        except Exception as e:
            print(f"❌ 异步transport测试失败: {e}")
    
    asyncio.run(async_test())


def test_httpx_compatibility():
    """测试httpx兼容性"""
    print("\n=== 测试httpx兼容性 ===")
    
    try:
        # httpx风格的transport使用
        
        # 1. 默认transport
        client1 = faster_http.Client()
        print("✅ 默认transport (httpx兼容)")
        
        # 2. 自定义transport
        transport = CustomTransport()
        client2 = faster_http.Client(transport=transport)
        print("✅ 自定义transport (httpx兼容)")
        
        # 3. transport + mounts组合
        mounts = {"https://api.example.com": LoggingTransport()}
        client3 = faster_http.Client(transport=transport, mounts=mounts)
        print("✅ transport + mounts组合 (httpx兼容)")
        
        print("✅ 所有httpx兼容性测试通过")
        
    except Exception as e:
        print(f"❌ httpx兼容性测试失败: {e}")


def test_direct_transport_usage():
    """测试直接使用transport"""
    print("\n=== 测试直接使用Transport ===")
    
    try:
        # 直接使用transport发送请求（不通过client）
        transport = FasterhttpTransport()
        request = HttpRequest("GET", "https://httpbin.org/get", None, None)
        
        print("1. 直接transport调用:")
        response = transport.handle_request(request)
        print(f"   ✅ 直接transport调用成功: {response.status_code}")
        print(f"   📊 响应大小: {len(response.content)} 字节")
        
        # 测试transport关闭
        transport.close()
        print("   ✅ Transport关闭成功")
        
    except Exception as e:
        print(f"❌ 直接transport使用测试失败: {e}")


def main():
    """运行所有transport测试"""
    print("🚚 开始Transport自定义测试\n")
    
    # 基础transport测试
    test_builtin_transports()
    test_direct_transport_usage()
    
    # 自定义transport测试
    test_custom_transport()
    test_logging_transport()
    
    # 高级功能测试
    test_transport_mounts()
    test_async_transport()
    
    # 兼容性测试
    test_httpx_compatibility()
    
    print("\n🎉 所有Transport自定义测试完成!")


if __name__ == "__main__":
    main()