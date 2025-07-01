"""
faster-http: A high-performance HTTP client for Python, powered by Rust's reqwest library.

This library provides a drop-in replacement for httpx with significantly better performance
by leveraging Rust's reqwest library through PyO3 bindings.
"""

from typing import Any, Dict, Optional, Union, Mapping, TypeAlias, Protocol
import asyncio
from ._core import (
    HttpClient as _HttpClient,
    AsyncHttpClient as _AsyncHttpClient,
    HttpResponse as _HttpResponse,
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
    "Client", "AsyncClient", "Response",
    "HTTPError", "ConnectTimeout", "ReadTimeout", "RequestError"
]

# Type aliases for better compatibility
Headers: TypeAlias = Optional[Dict[str, str]]
Params: TypeAlias = Optional[Dict[str, str]]
Data: TypeAlias = Optional[Dict[str, Any]]
JSON: TypeAlias = Optional[Dict[str, Any]]
Timeout: TypeAlias = Optional[float]

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
        """True if status_code < 400."""
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
    
    def json(self) -> Any:
        """Parse response content as JSON."""
        ...
    
    def raise_for_status(self) -> None:
        """Raise HTTPError if status indicates error."""
        ...

# 直接使用 Rust 的 HttpClient 类作为 Client
Client: TypeAlias = _HttpClient

class AsyncClient:
    """
    Asynchronous HTTP client compatible with httpx.AsyncClient.
    
    Args:
        base_url: Base URL for all requests
        timeout: Default timeout for requests in seconds
        headers: Default headers to include with all requests
        verify: Whether to verify SSL certificates (default: True)
    """
    
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: Timeout = None,
        headers: Headers = None,
        verify: bool = True,
    ):
        self._client = _AsyncHttpClient(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            verify=verify,
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
    
    async def aclose(self):
        """Close the client and clean up resources."""
        # For now, this is a no-op since the Rust client handles cleanup
        pass
    
    async def get(
        self,
        url: str,
        *,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
    ) -> Response:
        """Send a GET request asynchronously."""
        return await self._client.get(url, params=params, headers=headers, timeout=timeout)
    
    async def post(
        self,
        url: str,
        *,
        content: Optional[bytes] = None,
        data: Data = None,
        json: JSON = None,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
    ) -> Response:
        """Send a POST request asynchronously."""
        return await self._client.post(url, content=content, data=data, json=json, params=params, headers=headers, timeout=timeout)
    
    async def put(
        self,
        url: str,
        *,
        content: Optional[bytes] = None,
        data: Data = None,
        json: JSON = None,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
    ) -> Response:
        """Send a PUT request asynchronously."""
        return await self._client.put(url, content=content, data=data, json=json, params=params, headers=headers, timeout=timeout)
    
    async def patch(
        self,
        url: str,
        *,
        content: Optional[bytes] = None,
        data: Data = None,
        json: JSON = None,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
    ) -> Response:
        """Send a PATCH request asynchronously."""
        return await self._client.patch(url, content=content, data=data, json=json, params=params, headers=headers, timeout=timeout)
    
    async def delete(
        self,
        url: str,
        *,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
    ) -> Response:
        """Send a DELETE request asynchronously."""
        return await self._client.delete(url, params=params, headers=headers, timeout=timeout)
    
    async def head(
        self,
        url: str,
        *,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
    ) -> Response:
        """Send a HEAD request asynchronously."""
        return await self._client.head(url, params=params, headers=headers, timeout=timeout)
    
    async def options(
        self,
        url: str,
        *,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
    ) -> Response:
        """Send an OPTIONS request asynchronously."""
        return await self._client.options(url, params=params, headers=headers, timeout=timeout)


# Top-level convenience functions
def get(
    url: str,
    *,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
) -> Response:
    """Send a GET request."""
    return _get(url, params, headers, timeout)


def post(
    url: str,
    *,
    content: Optional[bytes] = None,
    data: Data = None,
    json: JSON = None,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
) -> Response:
    """Send a POST request."""
    return _post(url, content, data, json, params, headers, timeout)


def put(
    url: str,
    *,
    content: Optional[bytes] = None,
    data: Data = None,
    json: JSON = None,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
) -> Response:
    """Send a PUT request."""
    return _put(url, content, data, json, params, headers, timeout)


def patch(
    url: str,
    *,
    content: Optional[bytes] = None,
    data: Data = None,
    json: JSON = None,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
) -> Response:
    """Send a PATCH request."""
    return _patch(url, content, data, json, params, headers, timeout)


def delete(
    url: str,
    *,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
) -> Response:
    """Send a DELETE request."""
    return _delete(url, params, headers, timeout)


def head(
    url: str,
    *,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
) -> Response:
    """Send a HEAD request."""
    return _head(url, params, headers, timeout)


def options(
    url: str,
    *,
    params: Params = None,
    headers: Headers = None,
    timeout: Timeout = None,
) -> Response:
    """Send an OPTIONS request."""
    return _options(url, params, headers, timeout)


def main():
    """Main entry point for the CLI."""
    print("faster-http: A high-performance HTTP client for Python")
    print(f"Version: {__version__}")
    print("Usage: import faster_http as httpx  # Drop-in replacement for httpx")
