"""
faster-http: HTTP client compatible with httpx API, powered by Rust's hyper library.

This library provides a drop-in replacement for httpx API, implemented using Rust's hyper library through PyO3 bindings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# All imports at the top following Python best practices
from . import proxy as _proxy_module
from ._core import (
    URL,
    USE_CLIENT_DEFAULT,
    ASGITransport,
    AsyncBaseTransport,
    AsyncByteStream,
    AsyncHTTPTransport,
    Auth,
    BaseTransport,
    BasicAuth,
    ByteStream,
    CloseError,
    ConnectError,
    ConnectTimeout,
    CookieConflict,
    Cookies,
    DecodingError,
    DigestAuth,
    Headers,
    HTTPError,
    HTTPStatusError,
    HTTPTransport,
    InvalidURL,
    Limits,
    LocalProtocolError,
    MockTransport,
    NetRCAuth,
    NetworkError,
    PoolTimeout,
    ProtocolError,
    ProxyError,
    QueryParams,
    ReadError,
    ReadTimeout,
    RemoteProtocolError,
    RequestError,
    RequestNotRead,
    ResponseNotRead,
    StreamClosed,
    StreamConsumed,
    StreamError,
    SyncByteStream,
    TimeoutException,
    TooManyRedirects,
    TransportError,
    UnsupportedProtocol,
    WriteError,
    WriteTimeout,
    WSGITransport,
    create_ssl_context,
    delete,
    get,
    head,
    main,
    options,
    patch,
    post,
    put,
    request,
    stream,
)
from ._core import (
    HttpRequest as Request,
)
from ._core import (
    HttpResponse as Response,
)
from ._timeout import Timeout
from ._wrapper_client import AsyncClient, Client
from .codes import codes

__version__ = "0.1.0"
__title__ = "faster-http"
__description__ = "HTTP client compatible with httpx API, powered by Rust's hyper library"
__name = "faster-http"
# All imports now at the top

# Proxy setup
Proxy = _proxy_module.Proxy
del _proxy_module

# Add __locals for httpx compatibility
__locals = locals()

# Store original Rust HTTP functions
_rust_get = get
_rust_post = post
_rust_put = put
_rust_patch = patch
_rust_delete = delete
_rust_head = head
_rust_options = options
_rust_request = request

# Create module-level default timeout to avoid B008 warning
_MODULE_DEFAULT_TIMEOUT = Timeout(timeout=5.0)


def _process_timeout_for_request(timeout: float | Timeout | None) -> Any:
    """Helper function to process timeout parameter for all request methods."""
    from ._timeout_utils import extract_timeout_for_rust, process_timeout_param

    processed_timeout = process_timeout_param(timeout)
    return extract_timeout_for_rust(processed_timeout)


# Create Python wrapper functions with proper default values
def get(
    url: str | URL,
    *,
    params: dict[str, Any] | QueryParams | None = None,
    headers: dict[str, str] | Headers | None = None,
    cookies: dict[str, str] | Cookies | None = None,
    auth: Auth | None = None,
    proxy: Proxy | None = None,
    follow_redirects: bool = False,
    verify: bool | str = True,
    timeout: float | Timeout | None = _MODULE_DEFAULT_TIMEOUT,
    trust_env: bool = True,
) -> Response:
    """Send GET request with httpx-compatible defaults."""
    rust_timeout = _process_timeout_for_request(timeout)
    return _rust_get(
        url,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        proxy=proxy,
        follow_redirects=follow_redirects,
        verify=verify,
        timeout=rust_timeout,
        trust_env=trust_env,
    )


def post(
    url: str | URL,
    *,
    content: str | bytes | None = None,
    data: dict[str, Any] | list[tuple] | bytes | str | None = None,
    json: Any | None = None,
    files: dict[str, Any] | None = None,
    params: dict[str, Any] | QueryParams | None = None,
    headers: dict[str, str] | Headers | None = None,
    cookies: dict[str, str] | Cookies | None = None,
    auth: Auth | None = None,
    proxy: Proxy | None = None,
    follow_redirects: bool = False,
    verify: bool | str = True,
    timeout: float | Timeout | None = _MODULE_DEFAULT_TIMEOUT,
    trust_env: bool = True,
) -> Response:
    """Send POST request with httpx-compatible defaults."""
    rust_timeout = _process_timeout_for_request(timeout)
    return _rust_post(
        url,
        content=content,
        data=data,
        json=json,
        files=files,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        proxy=proxy,
        follow_redirects=follow_redirects,
        verify=verify,
        timeout=rust_timeout,
        trust_env=trust_env,
    )


def put(
    url: str | URL,
    *,
    content: str | bytes | None = None,
    data: dict[str, Any] | list[tuple] | bytes | str | None = None,
    json: Any | None = None,
    files: dict[str, Any] | None = None,
    params: dict[str, Any] | QueryParams | None = None,
    headers: dict[str, str] | Headers | None = None,
    cookies: dict[str, str] | Cookies | None = None,
    auth: Auth | None = None,
    proxy: Proxy | None = None,
    follow_redirects: bool = False,
    verify: bool | str = True,
    timeout: float | Timeout | None = _MODULE_DEFAULT_TIMEOUT,
    trust_env: bool = True,
) -> Response:
    """Send PUT request with httpx-compatible defaults."""
    rust_timeout = _process_timeout_for_request(timeout)
    return _rust_put(
        url,
        content=content,
        data=data,
        json=json,
        files=files,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        proxy=proxy,
        follow_redirects=follow_redirects,
        verify=verify,
        timeout=rust_timeout,
        trust_env=trust_env,
    )


def patch(
    url: str | URL,
    *,
    content: str | bytes | None = None,
    data: dict[str, Any] | list[tuple] | bytes | str | None = None,
    json: Any | None = None,
    files: dict[str, Any] | None = None,
    params: dict[str, Any] | QueryParams | None = None,
    headers: dict[str, str] | Headers | None = None,
    cookies: dict[str, str] | Cookies | None = None,
    auth: Auth | None = None,
    proxy: Proxy | None = None,
    follow_redirects: bool = False,
    verify: bool | str = True,
    timeout: float | Timeout | None = _MODULE_DEFAULT_TIMEOUT,
    trust_env: bool = True,
) -> Response:
    """Send PATCH request with httpx-compatible defaults."""
    rust_timeout = _process_timeout_for_request(timeout)
    return _rust_patch(
        url,
        content=content,
        data=data,
        json=json,
        files=files,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        proxy=proxy,
        follow_redirects=follow_redirects,
        verify=verify,
        timeout=rust_timeout,
        trust_env=trust_env,
    )


def delete(
    url: str | URL,
    *,
    params: dict[str, Any] | QueryParams | None = None,
    headers: dict[str, str] | Headers | None = None,
    cookies: dict[str, str] | Cookies | None = None,
    auth: Auth | None = None,
    proxy: Proxy | None = None,
    follow_redirects: bool = False,
    verify: bool | str = True,
    timeout: float | Timeout | None = _MODULE_DEFAULT_TIMEOUT,
    trust_env: bool = True,
) -> Response:
    """Send DELETE request with httpx-compatible defaults."""
    rust_timeout = _process_timeout_for_request(timeout)
    return _rust_delete(
        url,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        proxy=proxy,
        follow_redirects=follow_redirects,
        verify=verify,
        timeout=rust_timeout,
        trust_env=trust_env,
    )


def head(
    url: str | URL,
    *,
    params: dict[str, Any] | QueryParams | None = None,
    headers: dict[str, str] | Headers | None = None,
    cookies: dict[str, str] | Cookies | None = None,
    auth: Auth | None = None,
    proxy: Proxy | None = None,
    follow_redirects: bool = False,
    verify: bool | str = True,
    timeout: float | Timeout | None = _MODULE_DEFAULT_TIMEOUT,
    trust_env: bool = True,
) -> Response:
    """Send HEAD request with httpx-compatible defaults."""
    rust_timeout = _process_timeout_for_request(timeout)
    return _rust_head(
        url,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        proxy=proxy,
        follow_redirects=follow_redirects,
        verify=verify,
        timeout=rust_timeout,
        trust_env=trust_env,
    )


def options(
    url: str | URL,
    *,
    params: dict[str, Any] | QueryParams | None = None,
    headers: dict[str, str] | Headers | None = None,
    cookies: dict[str, str] | Cookies | None = None,
    auth: Auth | None = None,
    proxy: Proxy | None = None,
    follow_redirects: bool = False,
    verify: bool | str = True,
    timeout: float | Timeout | None = _MODULE_DEFAULT_TIMEOUT,
    trust_env: bool = True,
) -> Response:
    """Send OPTIONS request with httpx-compatible defaults."""
    rust_timeout = _process_timeout_for_request(timeout)
    return _rust_options(
        url,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        proxy=proxy,
        follow_redirects=follow_redirects,
        verify=verify,
        timeout=rust_timeout,
        trust_env=trust_env,
    )


def request(
    method: str,
    url: str | URL,
    *,
    content: str | bytes | None = None,
    data: dict[str, Any] | list[tuple] | bytes | str | None = None,
    json: Any | None = None,
    files: dict[str, Any] | None = None,
    params: dict[str, Any] | QueryParams | None = None,
    headers: dict[str, str] | Headers | None = None,
    cookies: dict[str, str] | Cookies | None = None,
    auth: Auth | None = None,
    proxy: Proxy | None = None,
    follow_redirects: bool = False,
    verify: bool | str = True,
    timeout: float | Timeout | None = _MODULE_DEFAULT_TIMEOUT,
    trust_env: bool = True,
) -> Response:
    """Send HTTP request with httpx-compatible defaults."""
    rust_timeout = _process_timeout_for_request(timeout)
    return _rust_request(
        method,
        url,
        content=content,
        data=data,
        json=json,
        files=files,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        proxy=proxy,
        follow_redirects=follow_redirects,
        verify=verify,
        timeout=rust_timeout,
        trust_env=trust_env,
    )


# All exception classes are now implemented in Rust and imported from _core
# Remove non-httpx compatible aliases - these don't exist in httpx


# Enhance HTTPStatusError and RequestError to support keyword arguments
# Store original constructors in closure scope to avoid variable deletion issues
def _create_enhanced_exceptions() -> tuple[Any, Any]:
    """Create enhanced exception classes with keyword argument support."""
    # Store original constructors in local scope
    orig_http_status_error_init = HTTPStatusError.__init__
    orig_request_error_init = RequestError.__init__

    def enhanced_httpstatuserror_init(
        self: HTTPStatusError,
        message: str | None = None,
        *,
        request: Request | None = None,
        response: Response | None = None,
    ) -> None:
        """Enhanced HTTPStatusError initializer with keyword argument support."""
        if message is None:
            message = "HTTP status error"
        # Call original constructor
        orig_http_status_error_init(self, message)
        # Store request and response as attributes for httpx compatibility
        if request is not None:
            self.request = request
        if response is not None:
            self.response = response

    def enhanced_requesterror_init(
        self: RequestError, message: str | None = None, *, request: Request | None = None
    ) -> None:
        """Enhanced RequestError initializer with keyword argument support."""
        if message is None:
            message = "Request error"
        # Call original constructor
        orig_request_error_init(self, message)
        if request is not None:
            self.request = request

    # Apply enhanced implementations
    HTTPStatusError.__init__ = enhanced_httpstatuserror_init
    RequestError.__init__ = enhanced_requesterror_init

    return enhanced_httpstatuserror_init, enhanced_requesterror_init


# Create enhanced exceptions and store references to prevent garbage collection
_enhanced_httpstatuserror_init, _enhanced_requesterror_init = _create_enhanced_exceptions()


# Note: Transport and authentication classes are implemented in Rust
# Stream functionality is provided through the Response object


# Remove non-httpx constants


# Define public API
__all__ = [
    "URL",
    "USE_CLIENT_DEFAULT",
    "ASGITransport",
    "AsyncBaseTransport",
    "AsyncByteStream",
    "AsyncClient",
    "AsyncHTTPTransport",
    "Auth",
    "BaseTransport",
    "BasicAuth",
    "ByteStream",
    "Client",
    "CloseError",
    "ConnectError",
    "ConnectTimeout",
    "CookieConflict",
    "Cookies",
    "DecodingError",
    "DigestAuth",
    "HTTPError",
    "HTTPStatusError",
    "HTTPTransport",
    "Headers",
    "InvalidURL",
    "Limits",
    "LocalProtocolError",
    "MockTransport",
    "NetRCAuth",
    "NetworkError",
    "PoolTimeout",
    "ProtocolError",
    "Proxy",
    "ProxyError",
    "QueryParams",
    "ReadError",
    "ReadTimeout",
    "RemoteProtocolError",
    "Request",
    "RequestError",
    "RequestNotRead",
    "Response",
    "ResponseNotRead",
    "StreamClosed",
    "StreamConsumed",
    "StreamError",
    "SyncByteStream",
    "Timeout",
    "TimeoutException",
    "TooManyRedirects",
    "TransportError",
    "UnsupportedProtocol",
    "WSGITransport",
    "WriteError",
    "WriteTimeout",
    "__description__",
    "__title__",
    "__version__",
    "codes",
    "create_ssl_context",
    "delete",
    "get",
    "head",
    "main",
    "options",
    "patch",
    "post",
    "put",
    "request",
    "stream",
]

# Hide internal implementation details from public API at module end

# Hide internal modules that shouldn't be exposed in httpx API
try:
    del _core
except NameError:
    pass

try:
    del _timeout
except NameError:
    pass

try:
    del _wrapper_client
except NameError:
    pass

# Explicitly remove proxy module reference to prevent exposure
try:
    del proxy
except NameError:
    pass

# Clean up internal symbols that shouldn't appear in dir()
# Remove all internal symbols that may leak to public API
del _create_enhanced_exceptions, _enhanced_httpstatuserror_init, _enhanced_requesterror_init

# Remove other internal symbols
try:
    del TYPE_CHECKING
except NameError:
    pass

try:
    del annotations
except NameError:
    pass

# Note: Internal variables are kept for module function usage and should not be deleted
# API visibility is controlled through __all__ list above

if __name__ == "__main__":
    import sys

    # Module information available through __doc__ or help() if needed
    sys.exit(0)
