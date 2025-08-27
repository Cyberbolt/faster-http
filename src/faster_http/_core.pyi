"""
Type stubs for faster_http._core

This module contains the Rust-implemented core functionality.
"""

from datetime import timedelta
from types import TracebackType
from typing import Any

# Exception types
class HTTPError(Exception):
    """Base HTTP exception."""

class ConnectTimeout(HTTPError):
    """Connection timeout exception."""

class ReadTimeout(HTTPError):
    """Read timeout exception."""

class RequestError(HTTPError):
    """Request error exception."""

# Core classes
class HttpRequest:
    """HTTP request object."""

    def __init__(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        params: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        data: Any | None = None,
        files: Any | None = None,
        json: Any | None = None,
        stream: bool | None = None,
    ) -> None: ...
    @property
    def method(self) -> str: ...
    @property
    def url(self) -> str: ...
    @property
    def headers(self) -> dict[str, str]: ...
    @property
    def content(self) -> bytes | None: ...
    @property
    def params(self) -> dict[str, str]: ...
    @property
    def cookies(self) -> dict[str, str]: ...
    @property
    def data(self) -> Any | None: ...
    @property
    def files(self) -> Any | None: ...
    @property
    def json(self) -> Any | None: ...
    @property
    def stream(self) -> bool: ...
    def __repr__(self) -> str: ...

class HttpResponse:
    """HTTP response object."""

    # Basic properties
    @property
    def status_code(self) -> int: ...
    @property
    def reason_phrase(self) -> str: ...
    @property
    def headers(self) -> dict[str, str]: ...
    @property
    def url(self) -> str: ...
    @property
    def elapsed(self) -> timedelta: ...
    @property
    def http_version(self) -> str: ...
    @property
    def cookies(self) -> dict[str, str]: ...
    @property
    def encoding(self) -> str | None: ...

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
    def history(self) -> list[Any]: ...
    @property
    def request(self) -> Any | None: ...
    @property
    def extensions(self) -> dict[str, Any]: ...

    # Content access
    @property
    def content(self) -> bytes: ...
    @property
    def text(self) -> str: ...
    def json(self) -> Any: ...

    # Streaming methods
    def iter_bytes(self, chunk_size: int | None = None) -> list[bytes]: ...
    def iter_text(self, chunk_size: int | None = None) -> list[str]: ...
    def iter_lines(self) -> list[str]: ...
    def iter_raw(self, chunk_size: int | None = None) -> list[bytes]: ...

    # Async streaming methods
    def aiter_bytes(self, chunk_size: int | None = None) -> list[bytes]: ...
    def aiter_text(self, chunk_size: int | None = None) -> list[str]: ...
    def aiter_lines(self) -> list[str]: ...
    def aiter_raw(self, chunk_size: int | None = None) -> list[bytes]: ...
    def read(self) -> bytes: ...
    async def aread(self) -> bytes: ...
    def next(self) -> Any | None: ...
    async def anext(self) -> Any | None: ...
    async def aclose(self) -> None: ...

    # Other methods
    def raise_for_status(self) -> None: ...
    def close(self) -> None: ...
    @property
    def is_closed(self) -> bool: ...

    # Context manager support
    def __enter__(self) -> HttpResponse: ...
    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool: ...
    def __repr__(self) -> str: ...

class HttpClient:
    """Synchronous HTTP client."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        verify: bool | str | None = None,
        follow_redirects: bool | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        proxy: str | None = None,
        proxies: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        http1: bool | None = None,
        http2: bool | None = None,
        event_hooks: dict[str, list[Any]] | None = None,
        cert: str | tuple[str, str] | tuple[str, str, str] | None = None,
        trust_env: bool | None = None,
        transport: Any | None = None,
        mounts: dict[str, Any] | None = None,
        max_redirects: int | None = None,
        default_encoding: str | None = None,
        params: dict[str, str] | None = None,
    ) -> None: ...
    def build_request(
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        data: Any | None = None,
        files: Any | None = None,
        json: Any | None = None,
        cookies: dict[str, str] | None = None,
        timeout: float | None = None,
        extensions: dict[str, Any] | None = None,
        stream: bool | None = None,
    ) -> HttpRequest: ...
    def send(self, request: HttpRequest) -> HttpResponse: ...
    def get(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    def post(
        self,
        url: str,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    def put(
        self,
        url: str,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    def patch(
        self,
        url: str,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    def delete(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    def head(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    def options(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    def request(
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...

    # Context manager support
    def __enter__(self) -> HttpClient: ...
    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool: ...

class AsyncHttpClient:
    """Asynchronous HTTP client."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        verify: bool | str | None = None,
        follow_redirects: bool | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        proxy: str | None = None,
        proxies: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        http1: bool | None = None,
        http2: bool | None = None,
        event_hooks: dict[str, list[Any]] | None = None,
        cert: str | tuple[str, str] | tuple[str, str, str] | None = None,
        trust_env: bool | None = None,
        transport: Any | None = None,
        mounts: dict[str, Any] | None = None,
        max_redirects: int | None = None,
        default_encoding: str | None = None,
        params: dict[str, str] | None = None,
    ) -> None: ...
    def build_request(
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        data: Any | None = None,
        files: Any | None = None,
        json: Any | None = None,
        cookies: dict[str, str] | None = None,
        timeout: float | None = None,
        extensions: dict[str, Any] | None = None,
        stream: bool | None = None,
    ) -> HttpRequest: ...
    async def send(self, request: HttpRequest) -> HttpResponse: ...
    async def get(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    async def post(
        self,
        url: str,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    async def put(
        self,
        url: str,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    async def patch(
        self,
        url: str,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    async def delete(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    async def head(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    async def options(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...
    async def request(
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | BasicAuth | DigestAuth | NetRCAuth | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HttpResponse: ...

    # Context manager support
    async def __aenter__(self) -> AsyncHttpClient: ...
    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool: ...

# Global functions
def get(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    auth: tuple[str, str] | None = None,
    follow_redirects: bool | None = None,
    cookies: dict[str, str] | None = None,
) -> HttpResponse: ...
def post(
    url: str,
    content: bytes | None = None,
    data: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    auth: tuple[str, str] | None = None,
    follow_redirects: bool | None = None,
    cookies: dict[str, str] | None = None,
) -> HttpResponse: ...
def put(
    url: str,
    content: bytes | None = None,
    data: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    auth: tuple[str, str] | None = None,
    follow_redirects: bool | None = None,
    cookies: dict[str, str] | None = None,
) -> HttpResponse: ...
def patch(
    url: str,
    content: bytes | None = None,
    data: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    auth: tuple[str, str] | None = None,
    follow_redirects: bool | None = None,
    cookies: dict[str, str] | None = None,
) -> HttpResponse: ...
def delete(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    auth: tuple[str, str] | None = None,
    follow_redirects: bool | None = None,
    cookies: dict[str, str] | None = None,
) -> HttpResponse: ...
def head(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    auth: tuple[str, str] | None = None,
    follow_redirects: bool | None = None,
    cookies: dict[str, str] | None = None,
) -> HttpResponse: ...
def options(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    auth: tuple[str, str] | None = None,
    follow_redirects: bool | None = None,
    cookies: dict[str, str] | None = None,
) -> HttpResponse: ...
def request(
    method: str,
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    content: bytes | None = None,
    data: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    timeout: float | None = None,
    auth: tuple[str, str] | None = None,
    follow_redirects: bool | None = None,
    cookies: dict[str, str] | None = None,
) -> HttpResponse: ...
def stream(
    method: str,
    url: str,
    content: bytes | None = None,
    data: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    auth: tuple[str, str] | None = None,
    follow_redirects: bool | None = None,
    cookies: dict[str, str] | None = None,
) -> StreamingClient: ...

# Rust-implemented data structures
class Headers:
    """HTTP headers container - case-insensitive."""

    def __init__(self, headers: dict[str, str] | None = None) -> None: ...
    def __getitem__(self, key: str) -> str: ...
    def __setitem__(self, key: str, value: str) -> None: ...
    def get(self, key: str, default: str | None = None) -> str | None: ...
    def get_list(self, key: str, split_commas: bool = False) -> list[str]: ...
    def update(self, other: dict[str, str]) -> None: ...
    def multi_items(self) -> list[tuple[str, str]]: ...
    def items(self) -> list[tuple[str, str]]: ...
    def keys(self) -> list[str]: ...
    def values(self) -> list[str]: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> list[str]: ...

class QueryParams:
    """URL query parameters container."""

    def __init__(self, params: dict[str, str] | str | None = None) -> None: ...
    def __getitem__(self, key: str) -> str: ...
    def __setitem__(self, key: str, value: str) -> None: ...
    def get(self, key: str, default: str | None = None) -> str | None: ...
    def get_list(self, key: str) -> list[str]: ...
    def update(self, other: dict[str, str]) -> None: ...
    def multi_items(self) -> list[tuple[str, str]]: ...
    def items(self) -> list[tuple[str, str]]: ...
    def keys(self) -> list[str]: ...
    def values(self) -> list[str]: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> list[str]: ...

class Cookies:
    """HTTP cookies container."""

    def __init__(self, cookies: dict[str, str] | None = None) -> None: ...
    def __getitem__(self, key: str) -> str: ...
    def __setitem__(self, key: str, value: str) -> None: ...
    def get(self, key: str, default: str | None = None) -> str | None: ...
    def set(self, name: str, value: str, domain: str | None = None) -> None: ...
    def update(self, other: dict[str, str]) -> None: ...
    def items(self) -> list[tuple[str, str]]: ...
    def keys(self) -> list[str]: ...
    def values(self) -> list[str]: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> list[str]: ...

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
    def port(self) -> int | None: ...
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
        scheme: str | None = None,
        authority: str | None = None,
        path: str | None = None,
        query: str | None = None,
        fragment: str | None = None,
    ) -> URL: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Timeout:
    """Timeout configuration."""

    def __init__(
        self,
        connect: float | None = None,
        read: float | None = None,
        write: float | None = None,
        pool: float | None = None,
    ) -> None: ...
    @property
    def connect(self) -> float | None: ...
    @property
    def read(self) -> float | None: ...
    @property
    def write(self) -> float | None: ...
    @property
    def pool(self) -> float | None: ...

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

    def __init__(self, file: str | None = None) -> None: ...

# Transport classes
class FasterhttpTransport:
    """Default faster-http transport implementation."""

    def __init__(self) -> None: ...
    def handle_request(self, request: HttpRequest) -> HttpResponse: ...
    def close(self) -> None: ...
    def aclose(self) -> None: ...

# MockTransport temporarily disabled during hyper migration
# class MockTransport:
#     """Mock transport for testing."""
#
#     def __init__(
#         self,
#         responses: dict[str, HttpResponse] | None = None,
#         default_response: HttpResponse | None = None,
#     ) -> None: ...
#     def add_response(self, url: str, response: HttpResponse) -> None: ...
#     def set_default_response(self, response: HttpResponse) -> None: ...
#     def handle_request(self, request: HttpRequest) -> HttpResponse: ...
#     def close(self) -> None: ...
#     def aclose(self) -> None: ...

class HTTPSRedirectTransport:
    """Transport that redirects HTTP requests to HTTPS."""

    def __init__(self) -> None: ...
    def handle_request(self, request: HttpRequest) -> HttpResponse: ...
    def close(self) -> None: ...
    def aclose(self) -> None: ...

class StreamingClient:
    """Streaming HTTP client providing httpx.stream() context manager functionality."""

    def __init__(
        self,
        config: Any,
        method: str,
        url: str,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple[str, str] | None = None,
        follow_redirects: bool = False,
        cookies: dict[str, str] | None = None,
    ) -> None: ...

    # Context manager support
    def __enter__(self) -> HttpResponse: ...
    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool: ...

    # Async context manager support
    async def __aenter__(self) -> HttpResponse: ...
    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool: ...
    def __repr__(self) -> str: ...

# Status codes and proxy configuration classes
class _StatusCodes:
    """HTTP status code constants"""

    # Informational 1xx
    CONTINUE: int
    SWITCHING_PROTOCOLS: int
    PROCESSING: int
    EARLY_HINTS: int

    # Successful 2xx
    OK: int
    CREATED: int
    ACCEPTED: int
    NON_AUTHORITATIVE_INFORMATION: int
    NO_CONTENT: int
    RESET_CONTENT: int
    PARTIAL_CONTENT: int
    MULTI_STATUS: int
    ALREADY_REPORTED: int
    IM_USED: int

    # Redirection 3xx
    MULTIPLE_CHOICES: int
    MOVED_PERMANENTLY: int
    FOUND: int
    SEE_OTHER: int
    NOT_MODIFIED: int
    USE_PROXY: int
    TEMPORARY_REDIRECT: int
    PERMANENT_REDIRECT: int

    # Client Error 4xx
    BAD_REQUEST: int
    UNAUTHORIZED: int
    PAYMENT_REQUIRED: int
    FORBIDDEN: int
    NOT_FOUND: int
    METHOD_NOT_ALLOWED: int
    NOT_ACCEPTABLE: int
    PROXY_AUTHENTICATION_REQUIRED: int
    REQUEST_TIMEOUT: int
    CONFLICT: int
    GONE: int
    LENGTH_REQUIRED: int
    PRECONDITION_FAILED: int
    PAYLOAD_TOO_LARGE: int
    URI_TOO_LONG: int
    UNSUPPORTED_MEDIA_TYPE: int
    RANGE_NOT_SATISFIABLE: int
    EXPECTATION_FAILED: int
    IM_A_TEAPOT: int
    MISDIRECTED_REQUEST: int
    UNPROCESSABLE_ENTITY: int
    LOCKED: int
    FAILED_DEPENDENCY: int
    TOO_EARLY: int
    UPGRADE_REQUIRED: int
    PRECONDITION_REQUIRED: int
    TOO_MANY_REQUESTS: int
    REQUEST_HEADER_FIELDS_TOO_LARGE: int
    UNAVAILABLE_FOR_LEGAL_REASONS: int

    # Server Error 5xx
    INTERNAL_SERVER_ERROR: int
    NOT_IMPLEMENTED: int
    BAD_GATEWAY: int
    SERVICE_UNAVAILABLE: int
    GATEWAY_TIMEOUT: int
    HTTP_VERSION_NOT_SUPPORTED: int
    VARIANT_ALSO_NEGOTIATES: int
    INSUFFICIENT_STORAGE: int
    LOOP_DETECTED: int
    NOT_EXTENDED: int
    NETWORK_AUTHENTICATION_REQUIRED: int

    def __contains__(self, status_code: int) -> bool: ...
    def get_reason_phrase(self, status_code: int) -> str: ...

# Create singleton instance
codes: _StatusCodes

class Proxy:
    """HTTP proxy configuration class"""

    def __init__(
        self,
        url: str | URL,
        *,
        ssl_context: Any | None = None,
        auth: tuple[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None: ...
    @property
    def url(self) -> URL: ...
    @property
    def auth(self) -> tuple[str, str] | None: ...
    @property
    def headers(self) -> Headers: ...
    @property
    def ssl_context(self) -> Any | None: ...
    def copy_with(
        self,
        *,
        url: str | URL | None = None,
        ssl_context: Any | None = None,
        auth: tuple[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Proxy: ...
    def get_proxy_url_for_scheme(self, scheme: str) -> str: ...
    def supports_scheme(self, scheme: str) -> bool: ...
    def to_dict(self) -> dict[str, str]: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def __eq__(self, other: Any) -> bool: ...
    def __hash__(self) -> int: ...
