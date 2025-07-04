#!/usr/bin/env python3
"""演示 faster-http 的资源管理功能，类似于 httpx。"""

import asyncio
import faster_http


def example_sync_context_manager():
    """同步客户端使用上下文管理器（推荐方式）."""
    print("=== 同步客户端上下文管理器示例 ===")
    
    with faster_http.Client() as client:
        response = client.get("https://httpbin.org/get")
        print(f"状态码: {response.status_code}")
        print("客户端会在 with 块结束时自动关闭")


def example_sync_explicit_close():
    """同步客户端显式关闭."""
    print("\n=== 同步客户端显式关闭示例 ===")
    
    client = faster_http.Client()
    try:
        response = client.get("https://httpbin.org/get")
        print(f"状态码: {response.status_code}")
    finally:
        client.close()  # 手动关闭客户端
        print("客户端已手动关闭")


async def example_async_context_manager():
    """异步客户端使用上下文管理器（推荐方式）."""
    print("\n=== 异步客户端上下文管理器示例 ===")
    
    async with faster_http.AsyncClient() as client:
        response = await client.get("https://httpbin.org/get")
        print(f"状态码: {response.status_code}")
        print("异步客户端会在 async with 块结束时自动关闭")


async def example_async_explicit_close():
    """异步客户端显式关闭."""
    print("\n=== 异步客户端显式关闭示例 ===")
    
    client = faster_http.AsyncClient()
    try:
        response = await client.get("https://httpbin.org/get")
        print(f"状态码: {response.status_code}")
    finally:
        await client.aclose()  # 异步关闭客户端
        print("异步客户端已手动关闭")


def example_global_functions():
    """全局函数使用（内部管理连接池）."""
    print("\n=== 全局函数示例 ===")
    
    # 全局函数使用共享的连接池，不需要手动管理
    response = faster_http.get("https://httpbin.org/get")
    print(f"状态码: {response.status_code}")
    print("全局函数使用共享连接池，无需手动管理")


async def main():
    """运行所有示例."""
    print("faster-http 资源管理示例\n")
    
    # 同步示例
    example_sync_context_manager()
    example_sync_explicit_close()
    
    # 异步示例
    await example_async_context_manager()
    await example_async_explicit_close()
    
    # 全局函数示例
    example_global_functions()
    
    print("\n所有示例执行完成！")


if __name__ == "__main__":
    asyncio.run(main()) 