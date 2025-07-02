#!/usr/bin/env python3
"""
详细测试HTTP/2功能，包括与真实httpx的对比
"""

import asyncio
import sys

async def test_with_real_httpx():
    """使用真实的httpx测试HTTP/2支持"""
    
    print("=== 使用真实的httpx测试HTTP/2 ===\n")
    
    try:
        import httpx as real_httpx
        print("✓ 找到真实的httpx库")
        
        # 测试HTTP/2支持
        print("\n1. 真实httpx的HTTP/2测试:")
        async with real_httpx.AsyncClient(http2=True, timeout=30.0) as client:
            response = await client.get('https://www.zhihu.com')
            print(f"   URL: https://www.zhihu.com")
            print(f"   HTTP版本: {response.http_version}")
            print(f"   状态码: {response.status_code}")
            
        # 测试百度
        print("\n2. 真实httpx测试百度:")
        async with real_httpx.AsyncClient(http2=True, timeout=30.0) as client:
            response = await client.get('https://www.baidu.com')
            print(f"   URL: https://www.baidu.com")
            print(f"   HTTP版本: {response.http_version}")
            print(f"   状态码: {response.status_code}")
            
    except ImportError:
        print("⚠️  没有安装真实的httpx库，跳过对比测试")
    except Exception as e:
        print(f"❌ 真实httpx测试出错: {e}")

async def test_with_faster_http():
    """使用faster-http测试HTTP/2支持"""
    
    print("\n=== 使用faster-http测试HTTP/2 ===\n")
    
    import faster_http as httpx
    
    timeout = httpx.Timeout(30.0)
    
    # 测试多个在中国可访问且支持HTTP/2的服务器
    test_urls = [
        'https://www.zhihu.com',
        'https://www.baidu.com',
        'https://www.bilibili.com',
        'https://httpbin.org/get'
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"{i}. 测试 {url}:")
        try:
            # 测试 http2=True
            async with httpx.AsyncClient(http2=True, timeout=timeout) as client:
                response = await client.get(url)
                print(f"   http2=True  -> HTTP版本: {response.http_version}, 状态: {response.status_code}")
                
            # 测试 http2=False  
            async with httpx.AsyncClient(http2=False, timeout=timeout) as client:
                response = await client.get(url)
                print(f"   http2=False -> HTTP版本: {response.http_version}, 状态: {response.status_code}")
                
        except Exception as e:
            print(f"   错误: {e}")
        print()

async def check_reqwest_info():
    """检查reqwest的编译信息"""
    
    print("=== 检查reqwest编译信息 ===\n")
    
    # 这个函数需要在Rust端实现，现在先跳过
    print("注意：需要在Rust端添加功能来检查reqwest的编译特性")
    print()

def test_tcp_connection():
    """测试基础TCP连接到HTTP/2服务器"""
    
    print("=== 测试TCP连接 ===\n")
    
    import socket
    import ssl
    
    # 测试到知乎的连接
    print("测试到www.zhihu.com:443的连接:")
    try:
        sock = socket.create_connection(('www.zhihu.com', 443), timeout=10)
        
        # 尝试SSL连接和ALPN
        context = ssl.create_default_context()
        context.set_alpn_protocols(['h2', 'http/1.1'])
        
        with context.wrap_socket(sock, server_hostname='www.zhihu.com') as ssock:
            negotiated_protocol = ssock.selected_alpn_protocol()
            print(f"   ALPN协商结果: {negotiated_protocol}")
            print(f"   TLS版本: {ssock.version()}")
            
    except Exception as e:
        print(f"   连接错误: {e}")
    
    # 测试到百度的连接
    print("\n测试到www.baidu.com:443的连接:")
    try:
        sock = socket.create_connection(('www.baidu.com', 443), timeout=10)
        
        # 尝试SSL连接和ALPN
        context = ssl.create_default_context()
        context.set_alpn_protocols(['h2', 'http/1.1'])
        
        with context.wrap_socket(sock, server_hostname='www.baidu.com') as ssock:
            negotiated_protocol = ssock.selected_alpn_protocol()
            print(f"   ALPN协商结果: {negotiated_protocol}")
            print(f"   TLS版本: {ssock.version()}")
            
    except Exception as e:
        print(f"   连接错误: {e}")
    print()

async def main():
    """主测试函数"""
    
    print("🔍 详细HTTP/2功能测试\n")
    print("=" * 50)
    
    # 先测试真实的httpx作为基准
    await test_with_real_httpx()
    
    # 测试我们的faster-http
    await test_with_faster_http()
    
    # 检查reqwest信息
    await check_reqwest_info()
    
    # 测试底层连接
    test_tcp_connection()
    
    print("=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    asyncio.run(main()) 