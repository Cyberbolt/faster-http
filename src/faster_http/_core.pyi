"""
Type stubs for faster_http._core

This module contains the Rust-implemented core functionality.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from types import TracebackType

# Exception types
class HTTPError(Exception):
    """Base HTTP exception."""
    ...

class ConnectTimeout(HTTPError):
    """Connection timeout exception."""
    ...

class ReadTimeout(HTTPError):
    """Read timeout exception."""
    ...

class RequestError(HTTPError):
    """Request error exception."""
    ...

# Core classes
class HttpRequest:
    """HTTP request object."""
    
    def __init__(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None,
    ) -> None: ...
    
    @property
    def method(self) -> str: ...
    
    @property
    def url(self) -> str: ...
    
    @property
    def headers(self) -> Dict[str, str]: ...
    
    @property
    def content(self) -> Optional[bytes]: ...
    
    def __repr__(self) -> str: ...

class HttpResponse:
    """HTTP response object."""
    
    # Basic properties
    @property
    def status_code(self) -> int: ...
    
    @property
    def headers(self) -> Dict[str, str]: ...
    
    @property
    def url(self) -> str: ...
    
    @property
    def elapsed(self) -> float: ...
    
    @property
    def http_version(self) -> str: ...
    
    @property
    def cookies(self) -> Dict[str, str]: ...
    
    @property
    def encoding(self) -> Optional[str]: ...
    
    @property
    def num_bytes_downloaded(self) -> int: ...
    
    # Status checks
    @property
    def is_redirect(self) -> bool: ...
    
    @property
    def ok(self) -> bool: ...
    
    @property
    def is_client_error(self) -> bool: ...
    
    @property
    def is_server_error(self) -> bool: ...
    
    @property
    def is_error(self) -> bool: ...
    
    @property
    def is_success(self) -> bool: ...
    
    @property
    def is_informational(self) -> bool: ...
    
    @property
    def history(self) -> List[Any]: ...
    
    @property
    def request(self) -> Optional[Any]: ...
    
    @property
    def extensions(self) -> Dict[str, Any]: ...
    
    @property
    def next_request(self) -> Optional[Any]: ...
    
    # Content access
    @property
    def content(self) -> bytes: ...
    
    @property
    def text(self) -> str: ...
    
    def json(self) -> Any: ...
    
    # Streaming methods
    def iter_bytes(self, chunk_size: Optional[int] = None) -> List[bytes]: ...
    
    def iter_text(self, chunk_size: Optional[int] = None) -> List[str]: ...
    
    def iter_lines(self) -> List[str]: ...
    
    def iter_raw(self, chunk_size: Optional[int] = None) -> List[bytes]: ...
    
    # Other methods
    def raise_for_status(self) -> None: ...
    
    def close(self) -> None: ...
    
    @property
    def is_closed(self) -> bool: ...
    
    # Context manager support
    def __enter__(self) -> "HttpResponse": ...
    
    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool: ...
    
    def __repr__(self) -> str: ...

class StreamingHttpResponse:
    """Streaming HTTP response object."""
    
    # Basic properties
    @property
    def status_code(self) -> int: ...
    
    @property
    def headers(self) -> Dict[str, str]: ...
    
    @property
    def url(self) -> str: ...
    
    @property
    def ok(self) -> bool: ...
    
    @property
    def encoding(self) -> Optional[str]: ...
    
    @property
    def cookies(self) -> Dict[str, str]: ...
    
    @property
    def num_bytes_downloaded(self) -> int: ...
    
    @property
    def is_closed(self) -> bool: ...
    
    # Streaming methods
    def read_chunk(self, chunk_size: Optional[int] = None) -> Optional[bytes]: ...
    
    def iter_bytes(self, chunk_size: Optional[int] = None) -> "StreamingBytesIterator": ...
    
    def iter_text(self, chunk_size: Optional[int] = None) -> "StreamingTextIterator": ...
    
    def iter_lines(self) -> "StreamingLinesIterator": ...
    
    def iter_raw(self, chunk_size: Optional[int] = None) -> "StreamingBytesIterator": ...
    
    # Content access (one-time read)
    @property
    def content(self) -> bytes: ...
    
    @property
    def text(self) -> str: ...
    
    def json(self) -> Any: ...
    
    # Resource management
    def close(self) -> None: ...
    
    # Context manager support
    def __enter__(self) -> "StreamingHttpResponse": ...
    
    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool: ...
    
    def __repr__(self) -> str: ...

class StreamingBytesIterator:
    """Streaming bytes iterator."""
    
    def __iter__(self) -> "StreamingBytesIterator": ...
    
    def __next__(self) -> Optional[bytes]: ...

class StreamingTextIterator:
    """Streaming text iterator."""
    
    def __iter__(self) -> "StreamingTextIterator": ...
    
    def __next__(self) -> Optional[str]: ...

class StreamingLinesIterator:
    """Streaming lines iterator."""
    
    def __iter__(self) -> "StreamingLinesIterator": ...
    
    def __next__(self) -> Optional[str]: ...

class HttpClient:
    """Synchronous HTTP client."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        verify: Optional[bool] = None,
        follow_redirects: Optional[bool] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        proxy: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        http2: Optional[bool] = None,
    ) -> None: ...
    
    def build_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None,
    ) -> HttpRequest: ...
    
    def send(self, request: HttpRequest) -> HttpResponse: ...
    
    def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    def post(
        self,
        url: str,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    def put(
        self,
        url: str,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    def patch(
        self,
        url: str,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    def delete(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    def head(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    def options(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    # Context manager support
    def __enter__(self) -> "HttpClient": ...
    
    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool: ...

class AsyncHttpClient:
    """Asynchronous HTTP client."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        verify: Optional[bool] = None,
        follow_redirects: Optional[bool] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        proxy: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        http2: Optional[bool] = None,
    ) -> None: ...
    
    def build_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None,
    ) -> HttpRequest: ...
    
    async def send(self, request: HttpRequest) -> HttpResponse: ...
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    async def post(
        self,
        url: str,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    async def put(
        self,
        url: str,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    async def patch(
        self,
        url: str,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    async def delete(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    async def head(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    async def options(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> HttpResponse: ...
    
    # Context manager support
    async def __aenter__(self) -> "AsyncHttpClient": ...
    
    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool: ...

# Global functions
def get(
    url: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    auth: Optional[Tuple[str, str]] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Optional[Dict[str, str]] = None,
) -> HttpResponse: ...

def post(
    url: str,
    content: Optional[bytes] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    auth: Optional[Tuple[str, str]] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Optional[Dict[str, str]] = None,
) -> HttpResponse: ...

def put(
    url: str,
    content: Optional[bytes] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    auth: Optional[Tuple[str, str]] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Optional[Dict[str, str]] = None,
) -> HttpResponse: ...

def patch(
    url: str,
    content: Optional[bytes] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    auth: Optional[Tuple[str, str]] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Optional[Dict[str, str]] = None,
) -> HttpResponse: ...

def delete(
    url: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    auth: Optional[Tuple[str, str]] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Optional[Dict[str, str]] = None,
) -> HttpResponse: ...

def head(
    url: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    auth: Optional[Tuple[str, str]] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Optional[Dict[str, str]] = None,
) -> HttpResponse: ...

def options(
    url: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    auth: Optional[Tuple[str, str]] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Optional[Dict[str, str]] = None,
) -> HttpResponse: ...

def stream(
    method: str,
    url: str,
    content: Optional[bytes] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    auth: Optional[Tuple[str, str]] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Optional[Dict[str, str]] = None,
) -> StreamingHttpResponse: ...

def hello_from_bin() -> str: ...

# Rust-implemented data structures
class Headers:
    """HTTP headers container - case-insensitive."""
    
    def __init__(self, headers: Optional[Dict[str, str]] = None) -> None: ...
    def __getitem__(self, key: str) -> str: ...
    def __setitem__(self, key: str, value: str) -> None: ...
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]: ...
    def update(self, other: Dict[str, str]) -> None: ...
    def items(self) -> List[Tuple[str, str]]: ...
    def keys(self) -> List[str]: ...
    def values(self) -> List[str]: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> List[str]: ...

class QueryParams:
    """URL query parameters container."""
    
    def __init__(self, params: Optional[Union[Dict[str, str], str]] = None) -> None: ...
    def __getitem__(self, key: str) -> str: ...
    def __setitem__(self, key: str, value: str) -> None: ...
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]: ...
    def update(self, other: Dict[str, str]) -> None: ...
    def items(self) -> List[Tuple[str, str]]: ...
    def keys(self) -> List[str]: ...
    def values(self) -> List[str]: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> List[str]: ...

class Cookies:
    """HTTP cookies container."""
    
    def __init__(self, cookies: Optional[Dict[str, str]] = None) -> None: ...
    def __getitem__(self, key: str) -> str: ...
    def __setitem__(self, key: str, value: str) -> None: ...
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]: ...
    def set(self, name: str, value: str, domain: Optional[str] = None) -> None: ...
    def update(self, other: Dict[str, str]) -> None: ...
    def items(self) -> List[Tuple[str, str]]: ...
    def keys(self) -> List[str]: ...
    def values(self) -> List[str]: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> List[str]: ...

class URL:
    """URL container."""
    
    def __init__(self, url: str) -> None: ...
    def __str__(self) -> str: ...

class Timeout:
    """Timeout configuration."""
    
    def __init__(
        self,
        connect: Optional[float] = None,
        read: Optional[float] = None,
        write: Optional[float] = None,
        pool: Optional[float] = None,
    ) -> None: ...
    
    @property
    def connect(self) -> Optional[float]: ...
    
    @property
    def read(self) -> Optional[float]: ...
    
    @property
    def write(self) -> Optional[float]: ...
    
    @property
    def pool(self) -> Optional[float]: ...

class Limits:
    """Connection pool limits."""
    
    def __init__(
        self,
        max_keepalive_connections: int = 20,
        max_connections: int = 100,
        keepalive_expiry: float = 5.0,
    ) -> None: ...
    
    @property
    def max_keepalive_connections(self) -> int: ...
    
    @property
    def max_connections(self) -> int: ...
    
    @property
    def keepalive_expiry(self) -> float: ...

class BasicAuth:
    """Basic authentication."""
    
    def __init__(self, username: str, password: str) -> None: ...
    
    @property
    def username(self) -> str: ...
    
    @property
    def password(self) -> str: ...
    
    def auth_flow(self, request: Any) -> Any: ...
    
    def __repr__(self) -> str: ...

class DigestAuth:
    """Digest authentication."""
    
    def __init__(self, username: str, password: str) -> None: ...
    
    @property
    def username(self) -> str: ...
    
    @property
    def password(self) -> str: ...
    
    def auth_flow(self, request: Any) -> Any: ...
    
    def __repr__(self) -> str: ...

class NetRCAuth:
    """NetRC authentication."""
    
    def __init__(self, file: Optional[str] = None) -> None: ...
    
    @property
    def file(self) -> str: ...
    
    def auth_flow(self, request: Any) -> Any: ...
    
    def __repr__(self) -> str: ...
