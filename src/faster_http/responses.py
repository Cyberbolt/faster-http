"""Response classes for faster-http."""
from typing import Any, Dict, Optional, Iterator

from ._core import HttpResponse

# Response is an alias for the Rust HttpResponse
Response = HttpResponse


class StreamingResponse:
    """Streaming response wrapper with httpx-compatible interface."""
    
    def __init__(self, rust_response):
        self._rust_response = rust_response
        self._regular_response = None  # For fallback cases
    
    @classmethod
    def _from_response(cls, response: Response):
        """Create a StreamingResponse from a regular Response - 兼容性方法."""
        instance = cls.__new__(cls)
        instance._rust_response = None
        instance._regular_response = response
        return instance
    
    @property
    def status_code(self) -> int:
        if self._regular_response:
            return self._regular_response.status_code
        return self._rust_response.status_code
    
    @property
    def headers(self) -> Dict[str, str]:
        if self._regular_response:
            return self._regular_response.headers
        return self._rust_response.headers
    
    @property
    def url(self) -> str:
        if self._regular_response:
            return self._regular_response.url
        return self._rust_response.url
    
    @property
    def ok(self) -> bool:
        if self._regular_response:
            return self._regular_response.ok
        return self._rust_response.ok
    
    @property
    def encoding(self) -> Optional[str]:
        if self._regular_response:
            return self._regular_response.encoding
        return self._rust_response.encoding
    
    @property
    def cookies(self) -> Dict[str, str]:
        if self._regular_response:
            return self._regular_response.cookies
        return self._rust_response.cookies
    
    @property
    def content(self) -> bytes:
        """Get response content as bytes."""
        if self._regular_response:
            return self._regular_response.content
        return self._rust_response.content
    
    @property
    def text(self) -> str:
        """Get response content as text."""
        if self._regular_response:
            return self._regular_response.text
        return self._rust_response.text
    
    def json(self) -> Any:
        """Parse response as JSON."""
        if self._regular_response:
            return self._regular_response.json()
        return self._rust_response.json()
    
    def iter_bytes(self, chunk_size: int = 8192) -> Iterator[bytes]:
        """Iterate over response content as bytes chunks."""
        if self._regular_response:
            # 对于降级的普通响应，模拟流式迭代
            content = self._regular_response.content
            for i in range(0, len(content), chunk_size):
                yield content[i:i + chunk_size]
        else:
            # 真正的流式迭代
            while True:
                chunk = self._rust_response.read_chunk(chunk_size)
                if chunk is None:
                    break
                yield chunk
    
    def iter_text(self, chunk_size: int = 8192) -> Iterator[str]:
        """Iterate over response content as text chunks."""
        if self._regular_response:
            # 对于降级的普通响应，模拟流式迭代
            text = self._regular_response.text
            for i in range(0, len(text), chunk_size):
                yield text[i:i + chunk_size]
        else:
            # 真正的流式迭代（简化实现）
            for byte_chunk in self.iter_bytes(chunk_size):
                yield byte_chunk.decode(self.encoding or 'utf-8', errors='replace')
    
    def iter_lines(self) -> Iterator[str]:
        """Iterate over response content as lines."""
        if self._regular_response:
            # 对于降级的普通响应
            return iter(self._regular_response.text.splitlines())
        else:
            # 真正的流式迭代（简化实现）
            buffer = ""
            for text_chunk in self.iter_text():
                buffer += text_chunk
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    yield line
            if buffer:  # 最后一行可能没有换行符
                yield buffer
    
    def iter_raw(self, chunk_size: int = 8192) -> Iterator[bytes]:
        """Iterate over raw response content."""
        return self.iter_bytes(chunk_size)
    
    def close(self) -> None:
        """Close the response."""
        if self._rust_response:
            self._rust_response.close()
    
    def __enter__(self) -> "StreamingResponse":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
    
    def __repr__(self) -> str:
        return f"<StreamingResponse [{self.status_code}]>"

 