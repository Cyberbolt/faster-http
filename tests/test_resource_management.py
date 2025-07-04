#!/usr/bin/env python3
"""测试 faster-http 的资源管理功能."""

import asyncio
import pytest
import faster_http


def test_sync_client_close():
    """测试同步客户端的显式关闭功能."""
    print("=== 测试同步客户端显式关闭 ===")
    
    # 测试显式关闭
    client = faster_http.Client()
    try:
        response = client.get("https://httpbin.org/get")
        print(f"请求成功，状态码: {response.status_code}")
        
        # 显式关闭
        client.close()
        print("✓ 客户端已显式关闭")
        
        # 尝试在关闭后使用客户端（应该失败）
        try:
            response = client.get("https://httpbin.org/get")
            print("✗ 错误：关闭后仍能使用客户端")
        except Exception as e:
            print(f"✓ 预期的错误：{e}")
            
    except Exception as e:
        print(f"✗ 测试失败：{e}")


def test_sync_client_context_manager():
    """测试同步客户端的上下文管理器功能."""
    print("\n=== 测试同步客户端上下文管理器 ===")
    
    try:
        with faster_http.Client() as client:
            response = client.get("https://httpbin.org/get")
            print(f"请求成功，状态码: {response.status_code}")
        print("✓ 上下文管理器正常工作，客户端已自动关闭")
        
        # 尝试在上下文外使用客户端（应该失败）
        try:
            response = client.get("https://httpbin.org/get")
            print("✗ 错误：上下文外仍能使用客户端")
        except Exception as e:
            print(f"✓ 预期的错误：{e}")
            
    except Exception as e:
        print(f"✗ 测试失败：{e}")


@pytest.mark.asyncio
async def test_async_client_close():
    """测试异步客户端的显式关闭功能."""
    print("\n=== 测试异步客户端显式关闭 ===")
    
    # 测试异步关闭
    client = faster_http.AsyncClient()
    try:
        response = await client.get("https://httpbin.org/get")
        print(f"请求成功，状态码: {response.status_code}")
        
        # 异步关闭
        await client.aclose()
        print("✓ 异步客户端已显式关闭")
        
        # 尝试在关闭后使用客户端（应该失败）
        try:
            response = await client.get("https://httpbin.org/get")
            print("✗ 错误：关闭后仍能使用客户端")
        except Exception as e:
            print(f"✓ 预期的错误：{e}")
            
    except Exception as e:
        print(f"✗ 测试失败：{e}")


@pytest.mark.asyncio
async def test_async_client_context_manager():
    """测试异步客户端的上下文管理器功能."""
    print("\n=== 测试异步客户端上下文管理器 ===")
    
    try:
        async with faster_http.AsyncClient() as client:
            response = await client.get("https://httpbin.org/get")
            print(f"请求成功，状态码: {response.status_code}")
        print("✓ 异步上下文管理器正常工作，客户端已自动关闭")
        
        # 尝试在上下文外使用客户端（应该失败）
        try:
            response = await client.get("https://httpbin.org/get")
            print("✗ 错误：上下文外仍能使用客户端")
        except Exception as e:
            print(f"✓ 预期的错误：{e}")
            
    except Exception as e:
        print(f"✗ 测试失败：{e}")


def test_global_functions():
    """测试全局函数仍然正常工作."""
    print("\n=== 测试全局函数 ===")
    
    try:
        response = faster_http.get("https://httpbin.org/get")
        print(f"全局函数请求成功，状态码: {response.status_code}")
        print("✓ 全局函数正常工作")
    except Exception as e:
        print(f"✗ 全局函数测试失败：{e}")


async def main():
    """运行所有测试."""
    print("开始测试 faster-http 资源管理功能...\n")
    
    # 测试同步客户端
    test_sync_client_close()
    test_sync_client_context_manager()
    
    # 测试异步客户端
    await test_async_client_close()
    await test_async_client_context_manager()
    
    # 测试全局函数
    test_global_functions()
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    asyncio.run(main()) 