"""
faster-http: A high-performance HTTP client for Python, powered by Rust's reqwest library.

This library provides a drop-in replacement for httpx with significantly better performance
by leveraging Rust's reqwest library through PyO3 bindings.
"""

from typing import Any, Dict, List, Optional, TypeAlias, Protocol, Tuple
from ._core import (
    HttpClient as _HttpClient,
    AsyncHttpClient as _AsyncHttpClient,
    HttpRequest as _HttpRequest,
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
)

__version__ = "0.1.0"
__all__ = [
    "get", "post", "put", "patch", "delete", "head", "options",
    "Client", "AsyncClient", "Response", "Request",
    "HTTPError", "ConnectTimeout", "ReadTimeout", "RequestError"
]

# Type aliases for better compatibility
Headers: TypeAlias = Optional[Dict[str, str]]
Params: TypeAlias = Optional[Dict[str, str]]
Data: TypeAlias = Optional[Dict[str, Any]]
JSON: TypeAlias = Optional[Dict[str, Any]]
Files: TypeAlias = Optional[Dict[str, Any]]
Timeout: TypeAlias = Optional[float]
Auth: TypeAlias = Optional[Tuple[str, str]]
Cookies: TypeAlias = Optional[Dict[str, str]]

# Response Protocol 定义
class Response(Protocol):
    """HTTP Response protocol compatible with httpx.Response."""
    
    @property
    def status_code(self) -> int:
        """HTTP status code."""
        ...
    
    @property
    def headers(self) -> Dict[str, str]:
        """Response headers."""
        ...
    
    @property
    def url(self) -> str:
        """Request URL."""
        ...
    
    @property
    def ok(self) -> bool:
        """True if status_code is between 200-299."""
        ...
    
    @property
    def content(self) -> bytes:
        """Raw response content."""
        ...
    
    @property
    def text(self) -> str:
        """Response content as text."""
        ...
    
    @property
    def encoding(self) -> Optional[str]:
        """Response text encoding."""
        ...
    
    @encoding.setter
    def encoding(self, value: Optional[str]) -> None:
        """Set response text encoding."""
        ...
    
    @property
    def charset_encoding(self) -> Optional[str]:
        """Character set encoding from Content-Type header."""
        ...
    
    @property
    def elapsed(self) -> float:
        """Request elapsed time in seconds."""
        ...
    
    @property
    def is_client_error(self) -> bool:
        """True if 400 <= status_code < 500."""
        ...
    
    @property
    def is_server_error(self) -> bool:
        """True if status_code >= 500."""
        ...
    
    @property
    def is_redirect(self) -> bool:
        """True if status_code indicates a redirect (3xx)."""
        ...
    
    @property
    def http_version(self) -> str:
        """HTTP version used for the response."""
        ...
    
    @property
    def cookies(self) -> Dict[str, str]:
        """Cookies set by the response."""
        ...
    
    @property
    def history(self) -> List[Any]:
        """List of redirect responses that led to this response."""
        ...
    
    @property
    def request(self) -> Optional[Any]:
        """The request that resulted in this response."""
        ...
    
    def iter_bytes(self, chunk_size: Optional[int] = None) -> List[bytes]:
        """Iterate over response content as bytes."""
        ...
    
    def iter_text(self, chunk_size: Optional[int] = None) -> List[str]:
        """Iterate over response content as text."""
        ...
    
    def iter_lines(self) -> List[str]:
        """Iterate over response content line by line."""
        ...
    
    def iter_raw(self, chunk_size: Optional[int] = None) -> List[bytes]:
        """Iterate over raw response content."""
        ...
    
    def json(self) -> Any:
        """Parse response content as JSON."""
        ...
    
    def raise_for_status(self) -> None:
        """Raise HTTPError if status indicates error."""
        ...

# 直接使用 Rust 的 HttpClient 类作为 Client
Client: TypeAlias = _HttpClient

# 直接使用 Rust 的 HttpRequest 类作为 Request
Request: TypeAlias = _HttpRequest

class AsyncClient:
    """
    Asynchronous HTTP client compatible with httpx.AsyncClient.
    
    Args:
        base_url: Base URL for all requests
        timeout: Default timeout for requests  
        headers: Default headers for all requests
        verify: SSL certificate verification
        follow_redirects: Whether to follow redirects by default
        auth: Default authentication (username, password)
        proxy: Proxy server URL
        cookies: Default cookies for all requests
        http2: Enable HTTP/2 support
    """
    
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: Timeout = None,
        headers: Headers = None,
        verify: Optional[bool] = None,
        follow_redirects: Optional[bool] = None,
        auth: Auth = None,
        proxy: Optional[str] = None,
        cookies: Cookies = None,
        http2: Optional[bool] = None,
    ):
        self._client = _AsyncHttpClient(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            verify=verify,
            follow_redirects=follow_redirects,
            auth=auth,
            proxy=proxy,
            cookies=cookies,
            http2=http2,
        )
    
    def build_request(
        self,
        method: str,
        url: str,
        *,
        params: Params = None,
        headers: Headers = None,
        content: Optional[bytes] = None,
    ) -> Request:
        """Build a request object."""
        return self._client.build_request(
            method, url, params=params, headers=headers, content=content
        )
    
    async def send(self, request: Request) -> Response:
        """Send a pre-built request."""
        return await self._client.send(request)

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    async def get(
        self,
        url: str,
        *,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
        auth: Auth = None,
        follow_redirects: Optional[bool] = None,
        cookies: Cookies = None,
    ) -> Response:
        """Send a GET request asynchronously."""
        return await self._client.get(
            url, params=params, headers=headers, timeout=timeout, 
            auth=auth, follow_redirects=follow_redirects, cookies=cookies
        )
    
    async def post(
        self,
        url: str,
        *,
        content: Optional[bytes] = None,
        data: Data = None,
        json: JSON = None,
        files: Files = None,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
        auth: Auth = None,
        follow_redirects: Optional[bool] = None,
        cookies: Cookies = None,
    ) -> Response:
        """Send a POST request asynchronously."""
        return await self._client.post(
            url, content=content, data=data, json=json, files=files,
            params=params, headers=headers, timeout=timeout,
            auth=auth, follow_redirects=follow_redirects, cookies=cookies
        )
    
    async def put(
        self,
        url: str,
        *,
        content: Optional[bytes] = None,
        data: Data = None,
        json: JSON = None,
        files: Files = None,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
        auth: Auth = None,
        follow_redirects: Optional[bool] = None,
        cookies: Cookies = None,
    ) -> Response:
        """Send a PUT request asynchronously."""
        return await self._client.put(
            url, content=content, data=data, json=json, files=files,
            params=params, headers=headers, timeout=timeout,
            auth=auth, follow_redirects=follow_redirects, cookies=cookies
        )
    
    async def patch(
        self,
        url: str,
        *,
        content: Optional[bytes] = None,
        data: Data = None,
        json: JSON = None,
        files: Files = None,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
        auth: Auth = None,
        follow_redirects: Optional[bool] = None,
        cookies: Cookies = None,
    ) -> Response:
        """Send a PATCH request asynchronously."""
        return await self._client.patch(
            url, content=content, data=data, json=json, files=files,
            params=params, headers=headers, timeout=timeout,
            auth=auth, follow_redirects=follow_redirects, cookies=cookies
        )
    
    async def delete(
        self,
        url: str,
        *,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
        auth: Auth = None,
        follow_redirects: Optional[bool] = None,
        cookies: Cookies = None,
    ) -> Response:
        """Send a DELETE request asynchronously."""
        return await self._client.delete(
            url, params=params, headers=headers, timeout=timeout,
            auth=auth, follow_redirects=follow_redirects, cookies=cookies
        )
    
    async def head(
        self,
        url: str,
        *,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
        auth: Auth = None,
        follow_redirects: Optional[bool] = None,
        cookies: Cookies = None,
    ) -> Response:
        """Send a HEAD request asynchronously."""
        return await self._client.head(
            url, params=params, headers=headers, timeout=timeout,
            auth=auth, follow_redirects=follow_redirects, cookies=cookies
        )
    
    async def options(
        self,
        url: str,
        *,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
        auth: Auth = None,
        follow_redirects: Optional[bool] = None,
        cookies: Cookies = None,
    ) -> Response:
        """Send an OPTIONS request asynchronously."""
        return await self._client.options(
            url, params=params, headers=headers, timeout=timeout,
            auth=auth, follow_redirects=follow_redirects, cookies=cookies
        )


# 全局函数 - 同步版本
def get(
    url: str,
    *,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
    auth: Auth = None,
    follow_redirects: Optional[bool] = None,
    cookies: Cookies = None,
) -> Response:
    """Send a GET request."""
    return _get(
        url, params=params, headers=headers, timeout=timeout,
        auth=auth, follow_redirects=follow_redirects, cookies=cookies
    )


def post(
    url: str,
    *,
    content: Optional[bytes] = None,
    data: Data = None,
    json: JSON = None,
    files: Files = None,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
    auth: Auth = None,
    follow_redirects: Optional[bool] = None,
    cookies: Cookies = None,
) -> Response:
    """Send a POST request."""
    return _post(
        url, content=content, data=data, json=json, files=files,
        params=params, headers=headers, timeout=timeout,
        auth=auth, follow_redirects=follow_redirects, cookies=cookies
    )


def put(
    url: str,
    *,
    content: Optional[bytes] = None,
    data: Data = None,
    json: JSON = None,
    files: Files = None,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
    auth: Auth = None,
    follow_redirects: Optional[bool] = None,
    cookies: Cookies = None,
) -> Response:
    """Send a PUT request."""
    return _put(
        url, content=content, data=data, json=json, files=files,
        params=params, headers=headers, timeout=timeout,
        auth=auth, follow_redirects=follow_redirects, cookies=cookies
    )


def patch(
    url: str,
    *,
    content: Optional[bytes] = None,
    data: Data = None,
    json: JSON = None,
    files: Files = None,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
    auth: Auth = None,
    follow_redirects: Optional[bool] = None,
    cookies: Cookies = None,
) -> Response:
    """Send a PATCH request."""
    return _patch(
        url, content=content, data=data, json=json, files=files,
        params=params, headers=headers, timeout=timeout,
        auth=auth, follow_redirects=follow_redirects, cookies=cookies
    )


def delete(
    url: str,
    *,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
    auth: Auth = None,
    follow_redirects: Optional[bool] = None,
    cookies: Cookies = None,
) -> Response:
    """Send a DELETE request."""
    return _delete(
        url, params=params, headers=headers, timeout=timeout,
        auth=auth, follow_redirects=follow_redirects, cookies=cookies
    )


def head(
    url: str,
    *,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
    auth: Auth = None,
    follow_redirects: Optional[bool] = None,
    cookies: Cookies = None,
) -> Response:
    """Send a HEAD request."""
    return _head(
        url, params=params, headers=headers, timeout=timeout,
        auth=auth, follow_redirects=follow_redirects, cookies=cookies
    )


def options(
    url: str,
    *,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
    auth: Auth = None,
    follow_redirects: Optional[bool] = None,
    cookies: Cookies = None,
) -> Response:
    """Send an OPTIONS request."""
    return _options(
        url, params=params, headers=headers, timeout=timeout,
        auth=auth, follow_redirects=follow_redirects, cookies=cookies
    )


def main():
    """Main entry point for the CLI."""
    print("faster-http: A high-performance HTTP client for Python")
    print(f"Version: {__version__}")
    print("Usage: import faster_http as httpx  # Drop-in replacement for httpx")
