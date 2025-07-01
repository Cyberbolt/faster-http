"""
faster-http: A high-performance HTTP client for Python, powered by Rust's reqwest library.

This library provides a drop-in replacement for httpx with significantly better performance
by leveraging Rust's reqwest library through PyO3 bindings.
"""

from typing import Any, Dict, Optional, Union, Mapping
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
Headers = Optional[Dict[str, str]]
Params = Optional[Dict[str, str]]
Data = Optional[Dict[str, Any]]
JSON = Optional[Dict[str, Any]]
Timeout = Optional[float]

# 直接使用 Rust 的 HttpResponse 类作为 Response
Response = _HttpResponse

# 直接使用 Rust 的 HttpClient 类作为 Client
Client = _HttpClient

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
        self._base_url = base_url
        self._timeout = timeout
        self._headers = headers
    
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
        # For now, we'll use the sync client in a thread pool
        # TODO: Implement proper async support in Rust
        loop = asyncio.get_event_loop()
        sync_client = Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._headers,
        )
        return await loop.run_in_executor(
            None, 
            lambda: sync_client.get(url, params=params, headers=headers, timeout=timeout)
        )
    
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
        loop = asyncio.get_event_loop()
        sync_client = Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._headers,
        )
        return await loop.run_in_executor(
            None,
            lambda: sync_client.post(url, data=data, json=json, params=params, headers=headers, timeout=timeout)
        )
    
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
        loop = asyncio.get_event_loop()
        sync_client = Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._headers,
        )
        return await loop.run_in_executor(
            None,
            lambda: sync_client.put(url, data=data, json=json, params=params, headers=headers, timeout=timeout)
        )
    
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
        loop = asyncio.get_event_loop()
        sync_client = Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._headers,
        )
        return await loop.run_in_executor(
            None,
            lambda: sync_client.patch(url, data=data, json=json, params=params, headers=headers, timeout=timeout)
        )
    
    async def delete(
        self,
        url: str,
        *,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
    ) -> Response:
        """Send a DELETE request asynchronously."""
        loop = asyncio.get_event_loop()
        sync_client = Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._headers,
        )
        return await loop.run_in_executor(
            None,
            lambda: sync_client.delete(url, params=params, headers=headers, timeout=timeout)
        )
    
    async def head(
        self,
        url: str,
        *,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
    ) -> Response:
        """Send a HEAD request asynchronously."""
        loop = asyncio.get_event_loop()
        sync_client = Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._headers,
        )
        return await loop.run_in_executor(
            None,
            lambda: sync_client.head(url, params=params, headers=headers, timeout=timeout)
        )
    
    async def options(
        self,
        url: str,
        *,
        params: Params = None,
        headers: Headers = None,
        timeout: Timeout = None,
    ) -> Response:
        """Send an OPTIONS request asynchronously."""
        loop = asyncio.get_event_loop()
        sync_client = Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._headers,
        )
        return await loop.run_in_executor(
            None,
            lambda: sync_client.options(url, params=params, headers=headers, timeout=timeout)
        )


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
    return _post(url, data, json, params, headers, timeout)


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
    return _put(url, data, json, params, headers, timeout)


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
    return _patch(url, data, json, params, headers, timeout)


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
