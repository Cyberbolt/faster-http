"""
Simplified Python wrapper client that passes all logic to Rust layer.

This wrapper follows CLAUDE.md requirements by doing only interface conversion,
with all business logic handled in Rust layer for optimal performance.

ARCHITECTURAL ENHANCEMENT: Smart Request Routing
- localhost requests -> Python native HTTP (urllib for sync, aiohttp for async) for compatibility
- external requests -> Rust implementation for performance
"""

# Async support
from collections.abc import Callable
from typing import Any

from ._core import USE_CLIENT_DEFAULT

# Direct Rust client imports - Python layer is interface-only
from ._core import AsyncHttpClient as RustAsyncHttpClient
from ._core import HttpClient as RustHttpClient
from ._timeout import Timeout
from ._timeout_utils import extract_timeout_for_rust, extract_timeout_for_rust_client, process_timeout_param

# Create module-level default timeout to avoid B008 warning
_DEFAULT_TIMEOUT = Timeout(timeout=5.0)

# _is_localhost_url function removed - all requests go through Rust


# _build_urllib_request and _UrllibResponse removed - all requests go through Rust


class Client:
    """
    Simplified Python wrapper for Rust HttpClient.

    This wrapper does only interface conversion and exposes httpx-compatible API.
    All business logic including URL building, parameter merging, headers processing,
    and event hooks execution is handled in the Rust layer.
    """

    def __init__(
        self,
        *,
        auth: Any | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        verify: bool = True,
        cert: Any | None = None,
        http1: bool = True,
        http2: bool = False,
        proxy: Any | None = None,
        mounts: dict[str, Any] | None = None,
        timeout=_DEFAULT_TIMEOUT,
        follow_redirects: bool = False,
        limits: Any | None = None,
        max_redirects: int = 20,
        event_hooks: dict[str, list[Callable]] | None = None,
        base_url: str | None = "",
        transport: Any | None = None,
        trust_env: bool = True,
        default_encoding: str | None = "utf-8",
    ):
        # Store client configuration for localhost requests
        self._base_url = base_url
        # Handle timeout parameter correctly - preserve complete Timeout object for USE_CLIENT_DEFAULT
        self._original_timeout = timeout
        processed_timeout = process_timeout_param(timeout)
        if processed_timeout is None:
            processed_timeout = Timeout(timeout=30.0)
            self._timeout = processed_timeout  # 保存完整对象
            self._timeout_for_rust = 30.0  # Rust层用的数值
        elif isinstance(processed_timeout, Timeout):
            self._timeout = processed_timeout  # 保存完整Timeout对象
            self._timeout_for_rust = extract_timeout_for_rust(processed_timeout)  # Rust层用的数值
        else:
            float_timeout = float(processed_timeout)
            processed_timeout = Timeout(timeout=float_timeout)
            self._timeout = processed_timeout  # 保存完整对象
            self._timeout_for_rust = float_timeout  # Rust层用的数值
        self._headers = headers or {}
        self._auth = auth
        self._cookies = cookies or {}
        self._params = params or {}
        self._follow_redirects = follow_redirects

        # Create the Rust client with all parameters - Rust handles all logic
        # Pass the processed timeout object to Rust layer for complete support
        rust_timeout = extract_timeout_for_rust_client(processed_timeout)
        self._rust_client = RustHttpClient(
            base_url=base_url,
            timeout=rust_timeout,
            headers=headers,
            verify=verify,
            follow_redirects=follow_redirects,
            auth=auth,
            proxy=proxy,
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

    def _process_client_defaults(self, auth, follow_redirects, timeout):
        """Helper method to process USE_CLIENT_DEFAULT values."""
        if auth is USE_CLIENT_DEFAULT:
            auth = self._auth
        if follow_redirects is USE_CLIENT_DEFAULT:
            follow_redirects = self._follow_redirects
        if timeout is USE_CLIENT_DEFAULT:
            timeout = self._timeout_for_rust  # 使用预先计算的Rust层数值
        return auth, follow_redirects, timeout

    # _handle_localhost_request method removed - all requests go through Rust

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
        auth: Any | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ):
        """
        Send HTTP request with GIL-free processing.

        All requests are routed through the GIL-free Rust implementation
        for true zero-GIL processing.
        """
        # Direct Rust execution - no Python business logic
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

    def get(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send GET request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return self.request(
            "GET",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    def post(
        self,
        url: str,
        *,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send POST request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return self.request(
            "POST",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    def put(
        self,
        url: str,
        *,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send PUT request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return self.request(
            "PUT",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    def patch(
        self,
        url: str,
        *,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send PATCH request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return self.request(
            "PATCH",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    def delete(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send DELETE request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return self.request(
            "DELETE",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    def head(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send HEAD request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return self.request(
            "HEAD",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    def options(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send OPTIONS request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return self.request(
            "OPTIONS",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

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
        cookies: dict[str, str] | None = None,
        timeout: float | None = None,
        extensions: dict[str, Any] | None = None,
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
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
            stream=stream,
        )

    def stream(self, method: str, url: str, **kwargs):
        """Send streaming request."""
        return self._rust_client.stream(
            method,
            url,
            kwargs.get("content"),
            kwargs.get("data"),
            kwargs.get("json"),
            kwargs.get("files"),
            kwargs.get("params"),
            kwargs.get("headers"),
            kwargs.get("timeout"),
            kwargs.get("auth"),
            kwargs.get("follow_redirects"),
            kwargs.get("cookies"),
        )

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

    @property
    def follow_redirects(self):
        """Get follow_redirects setting."""
        return self._rust_client.follow_redirects

    # Internal connection pool monitoring methods (not part of httpx API)
    def _get_connection_stats(self):
        """Internal: Get connection pool statistics for monitoring."""
        return self._rust_client.get_connection_stats()

    def _is_connection_healthy(self):
        """Internal: Check if connection pool is healthy."""
        return self._rust_client.is_connection_healthy()

    async def _cleanup_connections(self):
        """Internal: Cleanup idle connections in the pool."""
        return await self._rust_client.cleanup_connections()

    # Missing httpx compatibility methods
    def is_closed(self):
        """Check if the client is closed."""
        return getattr(self._rust_client, "is_closed", lambda: False)()

    @property
    def timeout(self):
        """Get the timeout setting."""
        return getattr(self._rust_client, "timeout", self._timeout)

    @property
    def trust_env(self):
        """Get the trust_env setting."""
        return getattr(self._rust_client, "trust_env", True)

    @property
    def max_redirects(self):
        """Get max redirects setting, compatible with httpx.Client."""
        # Check if we have a Python-side override first
        if hasattr(self, "_max_redirects_override"):
            return self._max_redirects_override
        return getattr(self._rust_client, "max_redirects", 20)

    @max_redirects.setter
    def max_redirects(self, value: int):
        """Set max redirects setting."""
        # Try to set on Rust client first
        if hasattr(self._rust_client, "set_max_redirects"):
            self._rust_client.set_max_redirects(value)
        else:
            # If Rust client doesn't support setting, store in Python layer
            self._max_redirects_override = value


# ============================================================================
# ASYNC CLIENT WITH SMART ROUTING SUPPORT
# ============================================================================


# _AiohttpResponse class removed - all requests go through Rust


class AsyncClient:
    """
    Simplified Python wrapper for Rust AsyncHttpClient.

    This wrapper provides httpx-compatible async API with all requests
    routed through the Rust implementation.
    """

    def __init__(
        self,
        *,
        auth: Any | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        verify: bool = True,
        cert: Any | None = None,
        http1: bool = True,
        http2: bool = False,
        proxy: Any | None = None,
        mounts: dict[str, Any] | None = None,
        timeout=_DEFAULT_TIMEOUT,
        follow_redirects: bool = False,
        limits: Any | None = None,
        max_redirects: int = 20,
        event_hooks: dict[str, list[Callable]] | None = None,
        base_url: str | None = "",
        transport: Any | None = None,
        trust_env: bool = True,
        default_encoding: str | None = "utf-8",
    ):
        # Store client configuration for localhost requests
        self._base_url = base_url
        # Handle timeout parameter correctly - preserve complete Timeout object for USE_CLIENT_DEFAULT
        self._original_timeout = timeout
        processed_timeout = process_timeout_param(timeout)
        if processed_timeout is None:
            processed_timeout = Timeout(timeout=30.0)
            self._timeout = processed_timeout  # 保存完整对象
            self._timeout_for_rust = 30.0  # Rust层用的数值
        elif isinstance(processed_timeout, Timeout):
            self._timeout = processed_timeout  # 保存完整Timeout对象
            self._timeout_for_rust = extract_timeout_for_rust(processed_timeout)  # Rust层用的数值
        else:
            float_timeout = float(processed_timeout)
            processed_timeout = Timeout(timeout=float_timeout)
            self._timeout = processed_timeout  # 保存完整对象
            self._timeout_for_rust = float_timeout  # Rust层用的数值
        self._headers = headers or {}
        self._auth = auth
        self._cookies = cookies or {}
        self._params = params or {}
        self._follow_redirects = follow_redirects

        # Create the Rust async client with all parameters - Rust handles all logic
        # Pass the processed timeout object to Rust layer for complete support
        rust_timeout = extract_timeout_for_rust_client(processed_timeout)
        self._rust_client = RustAsyncHttpClient(
            base_url=base_url,
            timeout=rust_timeout,
            headers=headers,
            verify=verify,
            follow_redirects=follow_redirects,
            auth=auth,
            proxy=proxy,
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

    def _process_client_defaults(self, auth, follow_redirects, timeout):
        """Helper method to process USE_CLIENT_DEFAULT values."""
        if auth is USE_CLIENT_DEFAULT:
            auth = self._auth
        if follow_redirects is USE_CLIENT_DEFAULT:
            follow_redirects = self._follow_redirects
        if timeout is USE_CLIENT_DEFAULT:
            timeout = self._timeout_for_rust  # 使用预先计算的Rust层数值
        return auth, follow_redirects, timeout

    # _handle_localhost_request_async method removed - all requests go through Rust

    async def request(
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
        auth: Any | None = None,
        follow_redirects: bool | None = None,
        cookies: dict[str, str] | None = None,
    ):
        """
        Send async HTTP request with GIL-free async processing.

        Use specialized GIL-free async path.
        This bypasses the standard future_into_py conversion overhead.
        """

        # Direct async Rust execution - no Python business logic
        return await self._rust_client.request(
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

    async def get(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send GET request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return await self.request(
            "GET",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    async def post(
        self,
        url: str,
        *,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send POST request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return await self.request(
            "POST",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    async def put(
        self,
        url: str,
        *,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send PUT request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return await self.request(
            "PUT",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    async def patch(
        self,
        url: str,
        *,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send PATCH request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return await self.request(
            "PATCH",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    async def delete(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send DELETE request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return await self.request(
            "DELETE",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    async def head(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send HEAD request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return await self.request(
            "HEAD",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    async def options(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth=USE_CLIENT_DEFAULT,
        follow_redirects=USE_CLIENT_DEFAULT,
        timeout=USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ):
        """Send OPTIONS request."""
        auth, follow_redirects, timeout = self._process_client_defaults(auth, follow_redirects, timeout)

        return await self.request(
            "OPTIONS",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    async def send(self, request):
        """
        Send a pre-built Request object.

        Args:
            request: A Request object built using httpx.Request() or faster_http.Request()

        Returns:
            Response object
        """
        return await self._rust_client.send(request)

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
        cookies: dict[str, str] | None = None,
        timeout: float | None = None,
        extensions: dict[str, Any] | None = None,
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
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
            stream=stream,
        )

    def stream(self, method: str, url: str, **kwargs):
        """Send streaming request."""
        return self._rust_client.stream(
            method,
            url,
            kwargs.get("content"),
            kwargs.get("data"),
            kwargs.get("json"),
            kwargs.get("files"),
            kwargs.get("params"),
            kwargs.get("headers"),
            kwargs.get("timeout"),
            kwargs.get("auth"),
            kwargs.get("follow_redirects"),
            kwargs.get("cookies"),
        )

    async def aclose(self):
        """Close the async client."""
        return await self._rust_client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()
        return False

    # Expose Rust client attributes for httpx compatibility
    @property
    def base_url(self):
        """Get base URL."""
        return self._rust_client.base_url()

    @property
    def headers(self):
        """Get default headers."""
        return self._rust_client.headers()

    @property
    def cookies(self):
        """Get default cookies."""
        return self._rust_client.cookies()

    @property
    def params(self):
        """Get default params."""
        return self._rust_client.params()

    @property
    def auth(self):
        """Get authentication."""
        return self._rust_client.auth()

    @property
    def event_hooks(self):
        """Get event hooks proxy for httpx compatibility."""
        return self._rust_client.event_hooks()

    @property
    def follow_redirects(self):
        """Get follow_redirects setting."""
        return self._rust_client.follow_redirects()

    # Internal connection pool monitoring methods (not part of httpx API)
    def _get_connection_stats(self):
        """Internal: Get connection pool statistics for monitoring."""
        return self._rust_client.get_connection_stats()

    def _is_connection_healthy(self):
        """Internal: Check if connection pool is healthy."""
        return self._rust_client.is_connection_healthy()

    async def _cleanup_connections(self):
        """Internal: Cleanup idle connections in the pool."""
        return await self._rust_client.cleanup_connections()

    # Missing httpx compatibility methods
    def is_closed(self):
        """Check if the client is closed."""
        return getattr(self._rust_client, "is_closed", lambda: False)()

    @property
    def timeout(self):
        """Get the timeout setting."""
        return getattr(self._rust_client, "timeout", self._timeout)

    @property
    def trust_env(self):
        """Get the trust_env setting."""
        return getattr(self._rust_client, "trust_env", True)

    @property
    def max_redirects(self):
        """Get max redirects setting, compatible with httpx.AsyncClient."""
        # Check if we have a Python-side override first
        if hasattr(self, "_max_redirects_override"):
            return self._max_redirects_override
        return getattr(self._rust_client, "max_redirects", 20)

    @max_redirects.setter
    def max_redirects(self, value: int):
        """Set max redirects setting."""
        # Try to set on Rust client first
        if hasattr(self._rust_client, "set_max_redirects"):
            self._rust_client.set_max_redirects(value)
        else:
            # If Rust client doesn't support setting, store in Python layer
            self._max_redirects_override = value
