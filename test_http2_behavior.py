#!/usr/bin/env python3
"""
测试faster-http的HTTP/2行为是否与httpx一致
"""

import faster_http as httpx
import asyncio

async def test_http2_behavior():
    """测试HTTP/2协商和降级行为"""
    
    print("=== 测试HTTP/2行为与httpx的一致性 ===\n")
    
    # 增加超时设置
    timeout = httpx.Timeout(30.0)
    
    # 测试HTTP/2支持的服务器 (httpbin)
    print("1. 测试支持HTTP/2的服务器:")
    try:
        async with httpx.AsyncClient(http2=True, timeout=timeout) as client:
            response = await client.get('https://httpbin.org/get')
            print(f"   URL: https://httpbin.org/get")
            print(f"   http2=True -> HTTP版本: {response.http_version}")
            print(f"   状态码: {response.status_code}")
            print()
    except Exception as e:
        print(f"   错误: {e}")
        print()
    
    # 测试HTTP/2关闭时只使用HTTP/1.1
    print("2. 测试http2=False时强制使用HTTP/1.1:")
    try:
        async with httpx.AsyncClient(http2=False, timeout=timeout) as client:
            response = await client.get('https://httpbin.org/get')
            print(f"   URL: https://httpbin.org/get")
            print(f"   http2=False -> HTTP版本: {response.http_version}")
            print(f"   状态码: {response.status_code}")
            print()
    except Exception as e:
        print(f"   错误: {e}")
        print()
    
    # 测试GitHub (支持HTTP/2)
    print("3. 测试GitHub API的HTTP/2支持:")
    try:
        async with httpx.AsyncClient(http2=True, timeout=timeout) as client:
            response = await client.get('https://api.github.com/zen')
            print(f"   URL: https://api.github.com/zen")
            print(f"   http2=True -> HTTP版本: {response.http_version}")
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.text[:50]}...")
            print()
    except Exception as e:
        print(f"   错误: {e}")
        print()

    print("=== 测试连接复用 ===\n")
    
    # 测试HTTP/2多路复用
    print("4. 测试HTTP/2多路复用 (同一个连接发送多个请求):")
    try:
        async with httpx.AsyncClient(http2=True, timeout=timeout) as client:
            # 发送多个并发请求到同一个服务器
            tasks = [
                client.get('https://httpbin.org/uuid'),
                client.get('https://httpbin.org/uuid'),
                client.get('https://httpbin.org/uuid')
            ]
            
            import time
            start_time = time.time()
            responses = await asyncio.gather(*tasks)
            end_time = time.time()
            
            print(f"   发送了3个并发请求，总耗时: {end_time - start_time:.2f}秒")
            for i, response in enumerate(responses):
                print(f"   请求{i+1}: HTTP版本={response.http_version}, 状态码={response.status_code}")
            print()
    except Exception as e:
        print(f"   错误: {e}")
        print()

    print("=== 测试协议协商和自动降级 ===\n")
    
    # 测试一个只支持HTTP/1.1的服务器（如果有的话）
    print("5. 验证HTTP/2到HTTP/1.1的自动降级:")
    print("   （注意：大多数现代服务器都支持HTTP/2，这个测试主要验证不会出错）")
    try:
        async with httpx.AsyncClient(http2=True, timeout=timeout) as client:
            response = await client.get('https://httpbin.org/status/200')
            print(f"   URL: https://httpbin.org/status/200")
            print(f"   http2=True -> HTTP版本: {response.http_version}")
            print(f"   状态码: {response.status_code}")
            
            # 验证是否支持HTTP/2
            if response.http_version == "HTTP/2":
                print("   ✓ 服务器支持HTTP/2，协商成功")
            elif response.http_version in ["HTTP/1.1", "HTTP/1.0"]:
                print("   ✓ 服务器不支持HTTP/2，自动降级到HTTP/1.1")
            else:
                print(f"   ? 未知的HTTP版本: {response.http_version}")
            print()
    except Exception as e:
        print(f"   错误: {e}")
        print()

if __name__ == "__main__":
    asyncio.run(test_http2_behavior()) 