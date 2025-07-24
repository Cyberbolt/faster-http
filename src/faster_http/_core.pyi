"""
Type stubs for faster_http._core

This module contains the Rust-implemented core functionality.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from types import TracebackType
from datetime import timedelta

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
    def reason_phrase(self) -> str: ...
    
    @property
    def headers(self) -> Dict[str, str]: ...
    
    @property
    def url(self) -> str: ...
    
    @property
    def elapsed(self) -> timedelta: ...
    
    @property
    def http_version(self) -> str: ...
    
    @property
    def cookies(self) -> Dict[str, str]: ...
    
    @property
    def encoding(self) -> Optional[str]: ...
    
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
    def is_success(self) -> bool: ...
    
    @property
    def history(self) -> List[Any]: ...
    
    @property
    def request(self) -> Optional[Any]: ...
    
    @property
    def extensions(self) -> Dict[str, Any]: ...
    
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
    
    # Async streaming methods  
    def aiter_bytes(self, chunk_size: Optional[int] = None) -> List[bytes]: ...
    
    def aiter_text(self, chunk_size: Optional[int] = None) -> List[str]: ...
    
    def aiter_lines(self) -> List[str]: ...
    
    def aiter_raw(self, chunk_size: Optional[int] = None) -> List[bytes]: ...
    
    async def aread(self) -> bytes: ...
    
    async def aclose(self) -> None: ...
    
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


class HttpClient:
    """Synchronous HTTP client."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        verify: Optional[Union[bool, str]] = None,
        follow_redirects: Optional[bool] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        proxy: Optional[str] = None,
        proxies: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        http2: Optional[bool] = None,
        event_hooks: Optional[Dict[str, List[Any]]] = None,
        cert: Optional[Union[str, Tuple[str, str], Tuple[str, str, str]]] = None,
        trust_env: Optional[bool] = None,
        transport: Optional[Any] = None,
        mounts: Optional[Dict[str, Any]] = None,
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
    
    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
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
        verify: Optional[Union[bool, str]] = None,
        follow_redirects: Optional[bool] = None,
        auth: Optional[Union[Tuple[str, str], "BasicAuth", "DigestAuth", "NetRCAuth"]] = None,
        proxy: Optional[str] = None,
        proxies: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        http2: Optional[bool] = None,
        event_hooks: Optional[Dict[str, List[Any]]] = None,
        cert: Optional[Union[str, Tuple[str, str], Tuple[str, str, str]]] = None,
        trust_env: Optional[bool] = None,
        transport: Optional[Any] = None,
        mounts: Optional[Dict[str, Any]] = None,
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
    
    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
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

def request(
    method: str,
    url: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    content: Optional[bytes] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
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
) -> HttpResponse: ...

# Rust-implemented data structures
class Headers:
    """HTTP headers container - case-insensitive."""
    
    def __init__(self, headers: Optional[Dict[str, str]] = None) -> None: ...
    def __getitem__(self, key: str) -> str: ...
    def __setitem__(self, key: str, value: str) -> None: ...
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]: ...
    def get_list(self, key: str, split_commas: bool = False) -> List[str]: ...
    def update(self, other: Dict[str, str]) -> None: ...
    def multi_items(self) -> List[Tuple[str, str]]: ...
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
    def get_list(self, key: str) -> List[str]: ...
    def update(self, other: Dict[str, str]) -> None: ...
    def multi_items(self) -> List[Tuple[str, str]]: ...
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
    """URL container - httpx compatible."""
    
    def __init__(self, url: str) -> None: ...
    
    @property
    def scheme(self) -> str: ...
    
    @property
    def authority(self) -> str: ...
    
    @property
    def host(self) -> str: ...
    
    @property
    def port(self) -> Optional[int]: ...
    
    @property
    def path(self) -> str: ...
    
    @property
    def query(self) -> str: ...
    
    @property
    def raw_path(self) -> str: ...
    
    @property
    def fragment(self) -> str: ...
    
    @property
    def is_ssl(self) -> bool: ...
    
    @property
    def is_absolute_url(self) -> bool: ...
    
    @property
    def is_relative_url(self) -> bool: ...
    
    def copy_with(
        self,
        *,
        scheme: Optional[str] = None,
        authority: Optional[str] = None,
        path: Optional[str] = None,
        query: Optional[str] = None,
        fragment: Optional[str] = None,
    ) -> "URL": ...
    
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

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
    
    def auth_flow(self, request: Any) -> Any: ...
    def sync_auth_flow(self, request: Any) -> Any: ...
    async def async_auth_flow(self, request: Any) -> Any: ...
    
    @property
    def requires_request_body(self) -> bool: ...
    
    @property 
    def requires_response_body(self) -> bool: ...
    
    def __repr__(self) -> str: ...

class DigestAuth:
    """Digest authentication."""
    
    def __init__(self, username: str, password: str) -> None: ...
    
    def auth_flow(self, request: Any) -> Any: ...
    def sync_auth_flow(self, request: Any) -> Any: ...
    async def async_auth_flow(self, request: Any) -> Any: ...
    
    @property
    def requires_request_body(self) -> bool: ...
    
    @property 
    def requires_response_body(self) -> bool: ...
    
    def __repr__(self) -> str: ...

class NetRCAuth:
    """NetRC authentication."""
    
    def __init__(self, file: Optional[str] = None) -> None: ...

# Transport classes
class FasterhttpTransport:
    """Default faster-http transport implementation."""
    
    def __init__(self) -> None: ...
    
    def handle_request(self, request: HttpRequest) -> HttpResponse: ...
    
    def close(self) -> None: ...
    
    def aclose(self) -> None: ...

class MockTransport:
    """Mock transport for testing."""
    
    def __init__(
        self, 
        responses: Optional[Dict[str, HttpResponse]] = None,
        default_response: Optional[HttpResponse] = None,
    ) -> None: ...
    
    def add_response(self, url: str, response: HttpResponse) -> None: ...
    
    def set_default_response(self, response: HttpResponse) -> None: ...
    
    def handle_request(self, request: HttpRequest) -> HttpResponse: ...
    
    def close(self) -> None: ...
    
    def aclose(self) -> None: ...

class HTTPSRedirectTransport:
    """Transport that redirects HTTP requests to HTTPS."""
    
    def __init__(self) -> None: ...
    
    def handle_request(self, request: HttpRequest) -> HttpResponse: ...
    
    def close(self) -> None: ...
    
    def aclose(self) -> None: ...

