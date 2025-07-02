"""Response classes for faster-http."""
from typing import Any, Dict, Protocol

from ._core import StreamingHttpResponse as _StreamingHttpResponse


class StreamingResponse:
    """Streaming response wrapper - 真正的生产级流式处理"""
    
    def __init__(self, rust_response):
        """包装 Rust 的 StreamingHttpResponse"""
        if isinstance(rust_response, _StreamingHttpResponse):
            self._response = rust_response
        else:
            # 如果传入的是普通 HttpResponse，转换为说明
            raise TypeError("StreamingResponse requires a StreamingHttpResponse from Rust")
    
    def __getattr__(self, name):
        """代理所有属性到底层 Rust 响应"""
        return getattr(self._response, name)
    
    # httpx 的标准流式方法 - 真正的流式处理
    def iter_bytes(self, chunk_size: int = 8192):
        """真正的流式字节迭代 - 直接对接 reqwest"""
        while True:
            chunk = self._response.read_chunk(chunk_size)
            if chunk is None:
                break
            yield chunk
    
    def iter_text(self, chunk_size: int = 8192):
        """真正的流式文本迭代 - 直接对接 reqwest"""
        for bytes_chunk in self.iter_bytes(chunk_size):
            # 使用响应的编码解码文本
            encoding = self._response.encoding or 'utf-8'
            try:
                text_chunk = bytes_chunk.decode(encoding)
                yield text_chunk
            except UnicodeDecodeError:
                # 如果解码失败，使用 utf-8 with 错误处理
                text_chunk = bytes_chunk.decode('utf-8', errors='replace')
                yield text_chunk
    
    def iter_lines(self):
        """真正的流式行迭代 - 直接对接 reqwest"""
        buffer = ""
        for text_chunk in self.iter_text():
            buffer += text_chunk
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                yield line.rstrip('\r')
        
        # 处理最后一行（如果没有换行符结尾）
        if buffer:
            yield buffer.rstrip('\r')
    
    def iter_raw(self, chunk_size: int = 8192):
        """真正的流式原始字节迭代 - 直接对接 reqwest"""
        return self.iter_bytes(chunk_size)
    
    # httpx 的异步版本 - 基于真正的流式迭代器
    async def aiter_bytes(self, chunk_size: int = 8192):
        """异步字节迭代 - 基于真正的流式处理"""
        for chunk in self.iter_bytes(chunk_size):
            yield chunk
    
    async def aiter_text(self, chunk_size: int = 8192):
        """异步文本迭代 - 基于真正的流式处理"""
        for text in self.iter_text(chunk_size):
            yield text
    
    async def aiter_lines(self):
        """异步行迭代 - 基于真正的流式处理"""
        for line in self.iter_lines():
            yield line
    
    # Context manager 支持
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def close(self):
        """关闭流式响应"""
        self._response.close()
    
    @property
    def is_closed(self):
        """检查是否已关闭"""
        return self._response.is_closed
    
    def read(self, chunk_size: int = 8192):
        """读取下一个数据块"""
        return self._response.read_chunk(chunk_size)


class Response(Protocol):
    """HTTP Response protocol."""
    
    @property
    def status_code(self) -> int: ...
    
    @property
    def headers(self) -> Dict[str, str]: ...
    
    @property
    def url(self) -> str: ...
    
    @property
    def ok(self) -> bool: ...
    
    @property
    def content(self) -> bytes: ...
    
    @property
    def text(self) -> str: ...
    
    def json(self) -> Any: ...
    
    def raise_for_status(self) -> None: ... 