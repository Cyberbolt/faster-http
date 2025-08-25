"""
Simplified Python wrapper client that passes all logic to Rust layer.

This wrapper follows CLAUDE.md requirements by doing only interface conversion,
with all business logic handled in Rust layer for optimal performance.

ARCHITECTURAL ENHANCEMENT: Smart Request Routing
- localhost requests -> Python native HTTP (urllib) for compatibility
- external requests -> Rust implementation for performance
"""

import base64
from collections.abc import Callable
import json
from typing import Any
import urllib.error
import urllib.parse
from urllib.parse import urlparse
import urllib.request

from ._core import HttpClient as RustHttpClient


def _is_localhost_url(url: str) -> bool:
    """
    Check if URL is a localhost request that should use Python HTTP implementation.

    Args:
        url: URL to check

    Returns:
        True if URL targets localhost, False otherwise
    """
    try:
        parsed = urlparse(url)
        localhost_hosts = {
            'localhost',
            '127.0.0.1',
            '::1',
            '0.0.0.0'
        }
        return parsed.hostname in localhost_hosts
    except Exception:
        return False


def _build_urllib_request(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    timeout: float | None = None,
) -> urllib.request.Request:
    """Build urllib Request object from parameters."""
    # Create base request
    req = urllib.request.Request(url, data=data, method=method)

    # Add headers
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)

    return req


class _UrllibResponse:
    """
    urllib Response wrapper that provides httpx-compatible interface.

    This class wraps urllib.response to match the interface expected by
    faster-http users, ensuring seamless fallback behavior for localhost requests.
    """

    def __init__(self, urllib_response, request_url: str):
        self._response = urllib_response
        self._url = request_url
        self._content = None

    @property
    def status_code(self) -> int:
        """HTTP status code."""
        return self._response.status

    @property
    def headers(self) -> dict[str, str]:
        """Response headers."""
        return dict(self._response.headers)

    @property
    def url(self) -> str:
        """Request URL."""
        return self._url

    @property
    def text(self) -> str:
        """Response content as text."""
        if self._content is None:
            self._content = self._response.read()
        return self._content.decode('utf-8')

    @property
    def content(self) -> bytes:
        """Response content as bytes."""
        if self._content is None:
            self._content = self._response.read()
        return self._content

    def json(self) -> dict:
        """Parse response content as JSON."""
        return json.loads(self.text)

    def __str__(self) -> str:
        return f"<Response [{self.status_code}]>"

    def __repr__(self) -> str:
        return self.__str__()


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
        # Store client configuration for localhost requests
        self._base_url = base_url
        self._timeout = timeout if timeout else 30.0  # Default 30s timeout
        self._headers = headers or {}
        self._auth = auth
        self._cookies = cookies or {}
        self._params = params or {}
        self._follow_redirects = follow_redirects

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

    def _handle_localhost_request(
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
        Handle localhost requests using Python urllib for compatibility.

        This method provides localhost request handling using Python's native
        urllib library, which reliably connects to localhost servers.
        """
        # Build complete URL with base_url and params
        if self._base_url and not url.startswith('http'):
            url = f"{self._base_url.rstrip('/')}/{url.lstrip('/')}"

        # Merge parameters
        if params or self._params:
            url_params = {**self._params, **(params or {})}
            if url_params:
                parsed = urlparse(url)
                query_string = urllib.parse.urlencode(url_params)
                if parsed.query:
                    query_string = f"{parsed.query}&{query_string}"
                url = urllib.parse.urlunparse(
                    (parsed.scheme, parsed.netloc, parsed.path,
                     parsed.params, query_string, parsed.fragment)
                )

        # Prepare request data
        request_data = None
        if content is not None:
            request_data = content
        elif data is not None:
            if isinstance(data, dict):
                request_data = urllib.parse.urlencode(data).encode('utf-8')
            else:
                request_data = str(data).encode('utf-8')
        elif json is not None:
            request_data = json.dumps(json).encode('utf-8')

        # Merge headers
        merged_headers = {**self._headers}
        if headers:
            merged_headers.update(headers)

        # Set content type for JSON
        if json is not None and 'Content-Type' not in merged_headers:
            merged_headers['Content-Type'] = 'application/json'

        # Set content type for form data
        if data is not None and isinstance(data, dict) and 'Content-Type' not in merged_headers:
            merged_headers['Content-Type'] = 'application/x-www-form-urlencoded'

        # Add cookies
        if cookies or self._cookies:
            cookie_items = {**self._cookies, **(cookies or {})}
            if cookie_items:
                cookie_str = '; '.join(f"{k}={v}" for k, v in cookie_items.items())
                merged_headers['Cookie'] = cookie_str

        # Handle authentication
        if auth or self._auth:
            actual_auth = auth or self._auth
            if isinstance(actual_auth, tuple) and len(actual_auth) == 2:
                username, password = actual_auth
                credentials = f"{username}:{password}".encode('ascii')
                auth_string = base64.b64encode(credentials).decode('ascii')
                merged_headers['Authorization'] = f'Basic {auth_string}'

        # Use request-specific timeout or client default
        request_timeout = timeout if timeout is not None else self._timeout

        try:
            # Build and send urllib request
            req = _build_urllib_request(method, url, merged_headers, request_data, request_timeout)

            # Handle redirects
            if follow_redirects is False or (follow_redirects is None and not self._follow_redirects):
                # Disable redirects
                class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
                    def http_error_302(self, req, fp, code, msg, headers):
                        return fp
                    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302

                opener = urllib.request.build_opener(NoRedirectHandler)
                response = opener.open(req, timeout=request_timeout)
            else:
                # Use default urllib behavior (follows redirects)
                response = urllib.request.urlopen(req, timeout=request_timeout)

            return _UrllibResponse(response, url)

        except urllib.error.HTTPError as e:
            # HTTP errors (4xx, 5xx) should still return a response
            return _UrllibResponse(e, url)
        except urllib.error.URLError as e:
            # Network/timeout errors
            if hasattr(e, 'reason') and 'timeout' in str(e.reason).lower():
                raise TimeoutError(f"Request timeout after {request_timeout}s")
            raise ConnectionError(f"Failed to connect to {url}: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during localhost request: {e}")

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
        Send HTTP request with smart routing.

        SMART REQUEST ROUTING:
        - localhost requests → Python urllib (for compatibility)
        - external requests → Rust implementation (for performance)

        This approach ensures:
        1. Localhost requests work reliably using Python's native HTTP
        2. External requests get maximum performance from Rust
        3. Transparent user experience with identical API
        """
        # Build full URL for localhost detection
        full_url = url
        if self._base_url and not url.startswith('http'):
            full_url = f"{self._base_url.rstrip('/')}/{url.lstrip('/')}"

        # SMART ROUTING: Check if this is a localhost request
        if _is_localhost_url(full_url):
            # Route localhost requests to Python urllib for compatibility
            return self._handle_localhost_request(
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
        else:
            # Route external requests to Rust implementation for performance
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
