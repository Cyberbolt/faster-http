#!/usr/bin/env python3
"""
测试 content 参数功能
"""

import faster_http
import asyncio

def test_sync_content():
    """测试同步方法的 content 参数"""
    print("=== 测试同步 content 参数 ===")
    
    # 测试 POST 请求 with content
    try:
        response = faster_http.post(
            "https://httpbin.org/post", 
            content=b"Hello, World!"
        )
        print(f"POST with content - Status: {response.status_code}")
        result = response.json()
        print(f"Data received: {result.get('data')}")
        assert result.get('data') == "Hello, World!"
        print("✓ POST with content 测试成功")
    except Exception as e:
        print(f"✗ POST with content 测试失败: {e}")
    
    # 测试 PUT 请求 with content
    try:
        response = faster_http.put(
            "https://httpbin.org/put",
            content=b'{"message": "test content"}'
        )
        print(f"PUT with content - Status: {response.status_code}")
        result = response.json()
        print(f"Data received: {result.get('data')}")
        print("✓ PUT with content 测试成功")
    except Exception as e:
        print(f"✗ PUT with content 测试失败: {e}")
    
    # 测试 PATCH 请求 with content
    try:
        response = faster_http.patch(
            "https://httpbin.org/patch",
            content=b"patch data"
        )
        print(f"PATCH with content - Status: {response.status_code}")
        result = response.json()
        print(f"Data received: {result.get('data')}")
        print("✓ PATCH with content 测试成功")
    except Exception as e:
        print(f"✗ PATCH with content 测试失败: {e}")

async def test_async_content():
    """测试异步方法的 content 参数"""
    print("\n=== 测试异步 content 参数 ===")
    
    async with faster_http.AsyncClient() as client:
        # 测试 POST 请求 with content
        try:
            response = await client.post(
                "https://httpbin.org/post",
                content=b"Async Hello, World!"
            )
            print(f"Async POST with content - Status: {response.status_code}")
            result = response.json()
            print(f"Data received: {result.get('data')}")
            assert result.get('data') == "Async Hello, World!"
            print("✓ Async POST with content 测试成功")
        except Exception as e:
            print(f"✗ Async POST with content 测试失败: {e}")
        
        # 测试 PUT 请求 with content
        try:
            response = await client.put(
                "https://httpbin.org/put",
                content=b'{"async": "put test"}'
            )
            print(f"Async PUT with content - Status: {response.status_code}")
            result = response.json()
            print(f"Data received: {result.get('data')}")
            print("✓ Async PUT with content 测试成功")
        except Exception as e:
            print(f"✗ Async PUT with content 测试失败: {e}")

def test_content_priority():
    """测试 content 参数的优先级（content > json > data）"""
    print("\n=== 测试 content 优先级 ===")
    
    try:
        # 同时提供 content, json, data，应该优先使用 content
        response = faster_http.post(
            "https://httpbin.org/post",
            content=b"content data",
            json={"json": "data"},
            data={"form": "data"}
        )
        result = response.json()
        print(f"优先级测试结果 - Data: {result.get('data')}")
        assert result.get('data') == "content data"
        print("✓ content 优先级测试成功")
    except Exception as e:
        print(f"✗ content 优先级测试失败: {e}")

def test_backward_compatibility():
    """测试向后兼容性 - json 和 data 参数仍然工作"""
    print("\n=== 测试向后兼容性 ===")
    
    try:
        # 测试 json 参数
        response = faster_http.post(
            "https://httpbin.org/post",
            json={"message": "json test"}
        )
        result = response.json()
        print(f"JSON 测试结果: {result.get('json')}")
        assert result.get('json') == {"message": "json test"}
        print("✓ JSON 参数向后兼容测试成功")
    except Exception as e:
        print(f"✗ JSON 参数测试失败: {e}")
    
    try:
        # 测试 data 参数
        response = faster_http.post(
            "https://httpbin.org/post",
            data={"key": "value"}
        )
        result = response.json()
        print(f"Data 测试结果: {result.get('form')}")
        assert result.get('form') == {"key": "value"}
        print("✓ Data 参数向后兼容测试成功")
    except Exception as e:
        print(f"✗ Data 参数测试失败: {e}")

if __name__ == "__main__":
    print("开始测试 faster-http content 参数功能...")
    
    test_sync_content()
    asyncio.run(test_async_content())
    test_content_priority()
    test_backward_compatibility()
    
    print("\n=== 测试完成 ===") 