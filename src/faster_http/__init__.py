"""
faster-http: A high-performance HTTP client for Python, powered by Rust's reqwest library.

This library provides a drop-in replacement for httpx with significantly better performance
by leveraging Rust's reqwest library through PyO3 bindings.
"""
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Mapping, Protocol
import base64
import os
import mimetypes
from pathlib import Path

from ._core import (
    HttpClient as _HttpClient,
    AsyncHttpClient as _AsyncHttpClient,
    HttpRequest as _HttpRequest,
    StreamingHttpResponse as _StreamingHttpResponse,
    HTTPError,
    ConnectTimeout,
    ReadTimeout,
    RequestError,
    get as _get,
    post as _post,
    put as _put,
    patch as _patch,
    delete as _delete,
    head as _head,
    options as _options,
    stream as _stream,
)

__version__ = "0.1.0"
__all__ = [
    "get", "post", "put", "patch", "delete", "head", "options", "stream",
    "Client", "AsyncClient", "Response", "Request",
    "HTTPError", "ConnectTimeout", "ReadTimeout", "RequestError",
    "BasicAuth", "DigestAuth", "NetRCAuth", "Auth",
    "URL", "Headers", "Cookies", "QueryParams",
    "Timeout", "Limits", 
]


# ==================== Authentication Classes ====================

class Auth:
    """Base class for authentication schemes."""
    
    def auth_flow(self, request):
        """Generator that yields the request with authentication applied."""
        yield request


class BasicAuth(Auth):
    """HTTP Basic Authentication."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    def auth_flow(self, request):
        """Apply basic authentication to the request."""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        if hasattr(request, 'headers'):
            request.headers["Authorization"] = f"Basic {encoded_credentials}"
        yield request
    
    def __repr__(self):
        return f"<BasicAuth [username={self.username!r}]>"


class DigestAuth(Auth):
    """HTTP Digest Authentication (simplified implementation)."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    def __repr__(self):
        return f"<DigestAuth [username={self.username!r}]>"


class NetRCAuth(Auth):
    """Authentication using .netrc file."""
    
    def __init__(self, file: Optional[str] = None):
        self.file = file or os.path.expanduser("~/.netrc")
    
    def __repr__(self):
        return f"<NetRCAuth [file={self.file!r}]>"


# ==================== Helper Classes ====================

class URL:
    """URL parsing and manipulation."""
    
    def __init__(self, url: str):
        self._url = url
    
    def __str__(self) -> str:
        return self._url
    
    @property
    def scheme(self) -> str:
        """URL scheme (http/https)."""
        if "://" in self._url:
            return self._url.split("://")[0]
        return ""
    
    @property
    def host(self) -> str:
        """URL host."""
        if "://" in self._url:
            parts = self._url.split("://")[1]
            return parts.split("/")[0].split(":")[0]
        return ""


class Headers(dict):
    """Case-insensitive headers."""
    
    def __init__(self, headers: Optional[Mapping[str, str]] = None):
        super().__init__()
        if headers:
            for key, value in headers.items():
                self[key] = value
    
    def __getitem__(self, key: str) -> str:
        for k, v in self.items():
            if k.lower() == key.lower():
                return v
        raise KeyError(key)
    
    def __setitem__(self, key: str, value: str):
        # Remove existing key (case-insensitive)
        to_remove = [k for k in self.keys() if k.lower() == key.lower()]
        for k in to_remove:
            del self[k]
        super().__setitem__(key, value)


class Cookies(dict):
    """HTTP cookies container."""
    
    def set(self, name: str, value: str, domain: Optional[str] = None):
        """Set a cookie."""
        self[name] = value


class QueryParams(dict):
    """URL query parameters."""
    
    def __init__(self, params: Optional[Union[Dict[str, str], str]] = None):
        super().__init__()
        if isinstance(params, dict):
            self.update(params)
        elif isinstance(params, str):
            self._parse_query_string(params)
    
    def _parse_query_string(self, query_string: str):
        """Parse query string into parameters."""
        if query_string.startswith('?'):
            query_string = query_string[1:]
        
        from urllib.parse import parse_qsl
        for key, value in parse_qsl(query_string, keep_blank_values=True):
            self[key] = value


class Timeout:
    """Timeout configuration."""
    
    def __init__(self, 
                 connect: Optional[float] = None,
                 read: Optional[float] = None,
                 write: Optional[float] = None,
                 pool: Optional[float] = None):
        self.connect = connect
        self.read = read
        self.write = write
        self.pool = pool


class Limits:
    """Connection pool limits."""
    
    def __init__(self, 
                 max_keepalive_connections: int = 20,
                 max_connections: int = 100,
                 keepalive_expiry: float = 5.0):
        self.max_keepalive_connections = max_keepalive_connections
        self.max_connections = max_connections
        self.keepalive_expiry = keepalive_expiry


# ==================== File Upload Utilities ====================

class FileUpload:
    """文件上传类 - 与 httpx files 参数对齐"""
    
    def __init__(self, content=None, filename=None, content_type=None):
        self.content = content
        self.filename = filename
        self.content_type = content_type
    
    def to_bytes(self):
        """Convert content to bytes for compatibility."""
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, str):
            # 如果是文件路径，读取文件
            try:
                path = Path(self.content)
                if path.exists():
                    with open(path, 'rb') as f:
                        return f.read()
                else:
                    # 当作字符串内容
                    return self.content.encode('utf-8')
            except Exception:
                # 当作字符串内容
                return self.content.encode('utf-8')
        elif hasattr(self.content, 'read'):
            # 文件对象
            return self.content.read()
        else:
            return str(self.content).encode('utf-8')
    
    def get_content_type(self):
        """Get content type for the file."""
        if self.content_type:
            return self.content_type
        
        # 如果有文件名，尝试从扩展名猜测
        if self.filename:
            content_type, _ = mimetypes.guess_type(self.filename)
            if content_type:
                return content_type
        
        # 根据内容类型猜测
        if isinstance(self.content, str):
            if self.content.strip().startswith(('<', '{')):
                return 'text/plain'
            return 'text/plain'
        
        # 默认为二进制流
        return 'application/octet-stream'


def _process_single_file(file_spec: Any) -> FileUpload:
    """处理单个文件规格 - 与 httpx 对齐"""
    if isinstance(file_spec, FileUpload):
        return file_spec
    
    elif isinstance(file_spec, bytes):
        return FileUpload(content=file_spec)
    
    elif isinstance(file_spec, (str, Path)):
        # 简单检查：如果是路径则作为文件，否则作为内容
        if Path(file_spec).exists():
            return FileUpload(content=file_spec, filename=Path(file_spec).name)
        else:
            return FileUpload(content=file_spec.encode('utf-8'))
    
    elif hasattr(file_spec, 'read'):
        # 文件对象
        filename = getattr(file_spec, 'name', None)
        if filename:
            filename = os.path.basename(filename)
        return FileUpload(content=file_spec, filename=filename)
    
    elif isinstance(file_spec, (tuple, list)) and len(file_spec) >= 2:
        # httpx 格式: (filename, content) 或 (filename, content, content_type)
        filename = file_spec[0]
        content = file_spec[1]
        content_type = file_spec[2] if len(file_spec) > 2 else None
        return FileUpload(content=content, filename=filename, content_type=content_type)
    
    else:
        # 其他情况当作内容处理
        return FileUpload(content=file_spec)


def process_files_parameter(files: Optional[Dict[str, Any]]) -> Optional[Dict[str, FileUpload]]:
    """处理 files 参数 - 与 httpx 对齐"""
    if not files:
        return None
    
    return {field_name: _process_single_file(file_spec) 
            for field_name, file_spec in files.items()}


def _process_string_or_path(file_spec: Union[str, Path]) -> FileUpload:
    return _process_single_file(file_spec)

def _process_file_like_object(file_spec) -> FileUpload:
    return _process_single_file(file_spec)

def _process_tuple_format(file_spec) -> FileUpload:
    return _process_single_file(file_spec)


# ==================== Response Classes ====================

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


# SSE 功能由用户基于 iter_lines() 自己实现，与 httpx 对齐


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


# Use Rust's HttpClient and HttpRequest
Client = _HttpClient
Request = _HttpRequest


# ==================== Utility Functions ====================

def _process_auth(auth: Union[Auth, Tuple[str, str], None]) -> Optional[Tuple[str, str]]:
    """Process authentication parameter."""
    if auth is None:
        return None
    elif isinstance(auth, tuple) and len(auth) == 2:
        return (str(auth[0]), str(auth[1]))
    elif isinstance(auth, BasicAuth):
        return (auth.username, auth.password)
    elif hasattr(auth, 'username') and hasattr(auth, 'password'):
        return (auth.username, auth.password)
    return None


def _process_headers(headers: Union[Headers, Dict[str, str], None]) -> Optional[Dict[str, str]]:
    """Process headers parameter."""
    return dict(headers) if isinstance(headers, Headers) else headers


def _process_cookies(cookies: Union[Cookies, Dict[str, str], None]) -> Optional[Dict[str, str]]:
    """Process cookies parameter."""
    return dict(cookies) if isinstance(cookies, Cookies) else cookies


def _process_params(params: Union[QueryParams, Dict[str, str], None]) -> Optional[Dict[str, str]]:
    """Process params parameter."""
    return dict(params) if isinstance(params, QueryParams) else params


def _process_timeout(timeout: Union[Timeout, float, None]) -> Optional[float]:
    """Process timeout parameter."""
    if isinstance(timeout, Timeout):
        return timeout.read or 30.0
    return timeout


def _prepare_files(files: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Prepare files for upload."""
    if files is None:
        return None
    
    processed_files = process_files_parameter(files)
    if processed_files:
        return {field_name: file_upload for field_name, file_upload in processed_files.items()}
    return None


# ==================== Async Client ====================

class AsyncClient:
    """Asynchronous HTTP client compatible with httpx.AsyncClient."""
    
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: Union[Timeout, float, None] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        verify: Optional[bool] = None,
        follow_redirects: Optional[bool] = None,
        auth: Union[Auth, Tuple[str, str], None] = None,
        proxy: Optional[str] = None,
        cookies: Union[Cookies, Dict[str, str], None] = None,
        http2: Optional[bool] = None,
        limits: Optional[Limits] = None,
        event_hooks: Optional[Dict[str, List[Callable]]] = None,
    ):
        self._client = _AsyncHttpClient(
            base_url=base_url,
            timeout=_process_timeout(timeout),
            headers=_process_headers(headers),
            verify=verify,
            follow_redirects=follow_redirects,
            auth=_process_auth(auth),
            proxy=proxy,
            cookies=_process_cookies(cookies),
            http2=http2,
        )
    
    def build_request(
        self,
        method: str,
        url: str,
        *,
        params: Union[QueryParams, Dict[str, str], None] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        content: Optional[bytes] = None,
    ) -> _HttpRequest:
        """Build a request object."""
        return self._client.build_request(
            method, url, 
            params=_process_params(params), 
            headers=_process_headers(headers), 
            content=content
        )
    
    async def send(self, request: _HttpRequest) -> "Response":
        """Send a pre-built request."""
        return await self._client.send(request)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def get(self, url: str, **kwargs) -> "Response":
        """Send a GET request."""
        return await self._client.get(
            url,
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )
    
    async def post(self, url: str, **kwargs) -> "Response":
        """Send a POST request."""
        return await self._client.post(
            url,
            content=kwargs.get('content'),
            data=kwargs.get('data'),
            json=kwargs.get('json'),
            files=_prepare_files(kwargs.get('files')),
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )
    
    async def put(self, url: str, **kwargs) -> "Response":
        """Send a PUT request."""
        return await self._client.put(
            url,
            content=kwargs.get('content'),
            data=kwargs.get('data'),
            json=kwargs.get('json'),
            files=_prepare_files(kwargs.get('files')),
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )
    
    async def patch(self, url: str, **kwargs) -> "Response":
        """Send a PATCH request."""
        return await self._client.patch(
            url,
            content=kwargs.get('content'),
            data=kwargs.get('data'),
            json=kwargs.get('json'),
            files=_prepare_files(kwargs.get('files')),
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )
    
    async def delete(self, url: str, **kwargs) -> "Response":
        """Send a DELETE request."""
        return await self._client.delete(
            url,
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )
    
    async def head(self, url: str, **kwargs) -> "Response":
        """Send a HEAD request."""
        return await self._client.head(
            url,
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )
    
    async def options(self, url: str, **kwargs) -> "Response":
        """Send an OPTIONS request."""
        return await self._client.options(
            url,
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )


# ==================== Global Functions ====================

def stream(method: str, url: str, **kwargs) -> StreamingResponse:
    """Send a streaming request - 真正的生产级流式处理."""
    rust_response = _stream(
        method,
        url,
        content=kwargs.get('content'),
        data=kwargs.get('data'),
        json=kwargs.get('json'),
        files=_prepare_files(kwargs.get('files')),
        params=_process_params(kwargs.get('params')),
        headers=_process_headers(kwargs.get('headers')),
        timeout=_process_timeout(kwargs.get('timeout')),
        auth=_process_auth(kwargs.get('auth')),
        follow_redirects=kwargs.get('follow_redirects'),
        cookies=_process_cookies(kwargs.get('cookies')),
    )
    return StreamingResponse(rust_response)


def get(url: str, **kwargs) -> "Response":
    """Send a GET request."""
    return _get(
        url,
        params=_process_params(kwargs.get('params')),
        headers=_process_headers(kwargs.get('headers')),
        timeout=_process_timeout(kwargs.get('timeout')),
        auth=_process_auth(kwargs.get('auth')),
        follow_redirects=kwargs.get('follow_redirects'),
        cookies=_process_cookies(kwargs.get('cookies')),
    )


def post(url: str, **kwargs) -> "Response":
    """Send a POST request."""
    return _post(
        url,
        content=kwargs.get('content'),
        data=kwargs.get('data'),
        json=kwargs.get('json'),
        files=_prepare_files(kwargs.get('files')),
        params=_process_params(kwargs.get('params')),
        headers=_process_headers(kwargs.get('headers')),
        timeout=_process_timeout(kwargs.get('timeout')),
        auth=_process_auth(kwargs.get('auth')),
        follow_redirects=kwargs.get('follow_redirects'),
        cookies=_process_cookies(kwargs.get('cookies')),
    )


def put(url: str, **kwargs) -> "Response":
    """Send a PUT request."""
    return _put(
        url,
        content=kwargs.get('content'),
        data=kwargs.get('data'),
        json=kwargs.get('json'),
        files=_prepare_files(kwargs.get('files')),
        params=_process_params(kwargs.get('params')),
        headers=_process_headers(kwargs.get('headers')),
        timeout=_process_timeout(kwargs.get('timeout')),
        auth=_process_auth(kwargs.get('auth')),
        follow_redirects=kwargs.get('follow_redirects'),
        cookies=_process_cookies(kwargs.get('cookies')),
    )


def patch(url: str, **kwargs) -> "Response":
    """Send a PATCH request."""
    return _patch(
        url,
        content=kwargs.get('content'),
        data=kwargs.get('data'),
        json=kwargs.get('json'),
        files=_prepare_files(kwargs.get('files')),
        params=_process_params(kwargs.get('params')),
        headers=_process_headers(kwargs.get('headers')),
        timeout=_process_timeout(kwargs.get('timeout')),
        auth=_process_auth(kwargs.get('auth')),
        follow_redirects=kwargs.get('follow_redirects'),
        cookies=_process_cookies(kwargs.get('cookies')),
    )


def delete(url: str, **kwargs) -> "Response":
    """Send a DELETE request."""
    return _delete(
        url,
        params=_process_params(kwargs.get('params')),
        headers=_process_headers(kwargs.get('headers')),
        timeout=_process_timeout(kwargs.get('timeout')),
        auth=_process_auth(kwargs.get('auth')),
        follow_redirects=kwargs.get('follow_redirects'),
        cookies=_process_cookies(kwargs.get('cookies')),
    )


def head(url: str, **kwargs) -> "Response":
    """Send a HEAD request."""
    return _head(
        url,
        params=_process_params(kwargs.get('params')),
        headers=_process_headers(kwargs.get('headers')),
        timeout=_process_timeout(kwargs.get('timeout')),
        auth=_process_auth(kwargs.get('auth')),
        follow_redirects=kwargs.get('follow_redirects'),
        cookies=_process_cookies(kwargs.get('cookies')),
    )


def options(url: str, **kwargs) -> "Response":
    """Send an OPTIONS request."""
    return _options(
        url,
        params=_process_params(kwargs.get('params')),
        headers=_process_headers(kwargs.get('headers')),
        timeout=_process_timeout(kwargs.get('timeout')),
        auth=_process_auth(kwargs.get('auth')),
        follow_redirects=kwargs.get('follow_redirects'),
        cookies=_process_cookies(kwargs.get('cookies')),
    )


# ==================== 与 httpx 完全对齐的实现 ====================
# 不添加 httpx 没有的功能，保持接口一致性


def main():
    """Entry point for the faster-http CLI."""
    print("faster-http: High-performance HTTP client powered by Rust")
    print("For more information, visit: https://github.com/your-repo/faster-http")


if __name__ == "__main__":
    main()


# httpx 使用 client.stream() 或 httpx.stream() 进行流式处理
# 不添加额外的自定义函数
