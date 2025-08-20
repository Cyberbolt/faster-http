"""
Simplified Python wrapper client that passes all logic to Rust layer.

This wrapper follows CLAUDE.md requirements by doing only interface conversion,
with all business logic handled in Rust layer for optimal performance.
"""

from collections.abc import Callable
from typing import Any

from ._core import HttpClient as RustHttpClient


class Client:
    """
    Simplified Python wrapper for Rust HttpClient.

    This wrapper does only interface conversion and exposes httpx-compatible API.
    All business logic including URL building, parameter merging, headers processing,
    and event hooks execution is handled in the Rust layer.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | dict[str, float] | None = None,
        headers: dict[str, str] | None = None,
        verify: bool | None = None,
        follow_redirects: bool | None = None,
        auth: Any | None = None,
        proxy: Any | None = None,
        proxies: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        http1: bool | None = None,
        http2: bool | None = None,
        event_hooks: dict[str, list[Callable]] | None = None,
        cert: Any | None = None,
        trust_env: bool | None = None,
        transport: Any | None = None,
        mounts: dict[str, Any] | None = None,
        limits: Any | None = None,
        max_redirects: int | None = None,
        default_encoding: str | None = None,
        params: dict[str, str] | None = None,
    ):
        # Create the Rust client with all parameters - Rust handles all logic
        self._rust_client = RustHttpClient(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            verify=verify,
            follow_redirects=follow_redirects,
            auth=auth,
            proxy=proxy,
            proxies=proxies,
            cookies=cookies,
            http1=http1,
            http2=http2,
            event_hooks=event_hooks,  # Pass hooks to Rust for unified handling
            cert=cert,
            trust_env=trust_env,
            transport=transport,
            mounts=mounts,
            limits=limits,
            max_redirects=max_redirects,
            default_encoding=default_encoding,
            params=params,
        )

    def request(
        self,
        method: str,
        url: str,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        auth: tuple | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ):
        """
        Send HTTP request - all logic handled in Rust layer.

        This method only passes parameters to Rust layer which handles:
        1. URL building with base_url and params
        2. Header and cookie merging
        3. Event hooks execution
        4. HTTP request execution
        """
        return self._rust_client.request(
            method=method,
            url=url,
            content=content,
            data=data,
            json=json,
            files=files,
            params=params,
            headers=headers,
            timeout=timeout,
            auth=auth,
            follow_redirects=follow_redirects,
            cookies=cookies,
        )

    def get(self, url: str, **kwargs):
        """Send GET request."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs):
        """Send POST request."""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs):
        """Send PUT request."""
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs):
        """Send PATCH request."""
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs):
        """Send DELETE request."""
        return self.request("DELETE", url, **kwargs)

    def head(self, url: str, **kwargs):
        """Send HEAD request."""
        return self.request("HEAD", url, **kwargs)

    def options(self, url: str, **kwargs):
        """Send OPTIONS request."""
        return self.request("OPTIONS", url, **kwargs)

    def send(self, request):
        """
        Send a pre-built Request object.
        
        Args:
            request: A Request object built using httpx.Request() or faster_http.Request()
        
        Returns:
            Response object
        """
        return self._rust_client.send(request)

    def build_request(
        self,
        method: str,
        url: str,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        stream: bool | None = None,
    ):
        """
        Build a Request object without sending it.
        
        Returns:
            Request object that can be passed to send()
        """
        return self._rust_client.build_request(
            method=method,
            url=url,
            content=content,
            data=data,
            json=json,
            files=files,
            params=params,
            headers=headers,
            stream=stream,
        )

    def stream(self, method: str, url: str, **kwargs):
        """Send streaming request."""
        return self._rust_client.stream(method, url, **kwargs)

    def close(self):
        """Close the client."""
        return self._rust_client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    # Expose Rust client attributes for httpx compatibility
    @property
    def base_url(self):
        """Get base URL."""
        return self._rust_client.base_url

    @property
    def headers(self):
        """Get default headers."""
        return self._rust_client.headers

    @property
    def cookies(self):
        """Get default cookies."""
        return self._rust_client.cookies

    @property
    def params(self):
        """Get default params."""
        return self._rust_client.params

    @property
    def auth(self):
        """Get authentication."""
        return self._rust_client.auth

    @property
    def event_hooks(self):
        """Get event hooks proxy for httpx compatibility."""
        return self._rust_client.event_hooks
