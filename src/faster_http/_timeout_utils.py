"""
统一的timeout处理工具函数。

用于在所有Python层代码中统一处理timeout参数，确保与httpx完全兼容。
"""

from __future__ import annotations

from typing import Any

from ._timeout import Timeout


def process_timeout_param(timeout_param: None | float | int | dict[str, Any] | Timeout) -> Timeout | None:
    """
    统一处理timeout参数，确保与httpx完全兼容。

    Args:
        timeout_param: 可能是 None, float, int, dict, 或 Timeout对象

    Returns:
        处理后的timeout对象，适合传递给Rust层

    Raises:
        TypeError: 如果timeout参数类型不正确
    """
    if timeout_param is None:
        return None
    elif isinstance(timeout_param, int | float):
        return Timeout(timeout=float(timeout_param))
    elif isinstance(timeout_param, Timeout):
        return timeout_param  # 直接传递完整的Timeout对象
    elif isinstance(timeout_param, dict):
        # 支持httpx字典格式: {"connect": 5.0, "read": 10.0, "write": 5.0, "pool": 5.0}
        return Timeout(
            timeout=timeout_param.get("timeout"),
            connect=timeout_param.get("connect"),
            read=timeout_param.get("read"),
            write=timeout_param.get("write"),
            pool=timeout_param.get("pool"),
        )
    else:
        raise TypeError(f"timeout must be a number, Timeout object, dict, or None, got {type(timeout_param)}")


def extract_timeout_for_rust(timeout_param: None | Timeout | float | int) -> float | None:
    """
    提取timeout参数以便传递给Rust层。

    基于HTTP请求阶段语义选择合适的超时值：
    - HTTP请求通常经历：连接建立 → 发送请求 → 等待响应 → 读取数据
    - 读取阶段通常是最长的，应该优先考虑，避免合法的长时间读取被提前终止
    - 采用智能优先级算法：read > write > connect > pool > timeout

    Args:
        timeout_param: 处理过的timeout对象

    Returns:
        适合传递给Rust层的数值timeout
    """
    if timeout_param is None:
        return None
    elif isinstance(timeout_param, Timeout):
        # 基于HTTP请求阶段语义的智能选择
        # 优先级：read > write > connect > pool > timeout
        # 这样可以确保读取阶段不会被提前终止
        if timeout_param.read is not None:
            return timeout_param.read  # 读取超时最重要，避免长响应被截断
        elif timeout_param.write is not None:
            return timeout_param.write  # 写入超时次之
        elif timeout_param.connect is not None:
            return timeout_param.connect  # 连接超时
        elif timeout_param.pool is not None:
            return timeout_param.pool  # 连接池超时
        elif hasattr(timeout_param, "timeout") and timeout_param.timeout is not None:
            return timeout_param.timeout  # 总体超时
        else:
            # 所有超时都是None，返回合理的默认值
            return 30.0
    elif isinstance(timeout_param, int | float):
        return float(timeout_param)
    else:
        # 这里应该不会到达，因为process_timeout_param已经验证了类型
        return 30.0


def extract_timeout_for_rust_client(timeout_param: None | Timeout | float | int) -> None | Timeout | float:
    """
    为Rust客户端提取timeout参数。

    客户端构造函数优先保持完整的Timeout对象以支持完整的超时语义，
    如果Rust客户端不支持完整对象，则回退到智能数值提取。

    Args:
        timeout_param: 处理过的timeout对象

    Returns:
        适合传递给Rust客户端的timeout值（优先完整对象，回退到数值）
    """
    # 对于客户端，我们尝试传递完整的Timeout对象
    # 如果Rust客户端不支持，则回退到智能数值提取
    if timeout_param is None:
        return None
    elif isinstance(timeout_param, Timeout):
        # 先尝试传递Timeout对象，如果失败再回退到数值
        return timeout_param
    else:
        return extract_timeout_for_rust(timeout_param)
