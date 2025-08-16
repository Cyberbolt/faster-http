"""
faster-http: A high-performance HTTP client for Python, powered by Rust's reqwest library.

This library provides a drop-in replacement for httpx with significantly better performance
by leveraging Rust's reqwest library through PyO3 bindings.
"""

__version__ = "0.1.0"

# Import specific classes for explicit re-export
from ._core import (
    URL,
    BasicAuth,
    ConnectError,
    ConnectTimeout,
    Cookies,
    DigestAuth,
    # Model classes with httpx-compatible names
    Headers,
    # Exception hierarchy (only httpx-compatible ones)
    HTTPError,
    HTTPStatusError,
    Limits,
    # Transport classes (import available ones from Rust)
    MockTransport,
    NetRCAuth,
    PoolTimeout,
    ProtocolError,
    QueryParams,
    ReadTimeout,
    RequestError,
    StreamError,
    Timeout,
    TimeoutException,
    TooManyRedirects,
    TransportError,
    WriteTimeout,
    delete,
    # HTTP methods
    get,
    head,
    options,
    patch,
    post,
    put,
    request,
    stream,
)
from ._core import (
    AsyncHttpClient as AsyncClient,
)
from ._core import (
    HttpClient as Client,
)
from ._core import (
    HttpRequest as Request,
)
from ._core import (
    HttpResponse as Response,
)

# Import additional modules
from .codes import codes
from .event_hooks_proxy import EventHooksProxy
from .proxy import Proxy


# Create httpx-compatible exception classes that don't exist in Rust code
class InvalidURL(RequestError):
    """Raised when a URL is malformed."""


class LocalProtocolError(ProtocolError):
    """Raised for local protocol violations."""


class RemoteProtocolError(ProtocolError):
    """Raised for remote protocol violations."""


class ReadError(RequestError):
    """Raised when a read error occurs."""


class WriteError(RequestError):
    """Raised when a write error occurs."""


class UnsupportedProtocol(RequestError):
    """Raised when an unsupported protocol is used."""


# Create httpx-compatible transport and other classes that don't exist in Rust code
class HTTPTransport:
    """HTTP transport implementation (placeholder)."""

    def __init__(self, **kwargs):
        pass


class AsyncHTTPTransport:
    """Async HTTP transport implementation (placeholder)."""

    def __init__(self, **kwargs):
        pass


class AsyncMockTransport:
    """Async mock transport implementation (placeholder)."""

    def __init__(self, handler=None, **kwargs):
        self.handler = handler


class Auth:
    """Base authentication class (placeholder)."""

    def auth_flow(self, request):
        yield request

    async def async_auth_flow(self, request):
        yield request


class Stream:
    """Stream implementation (placeholder)."""


class AsyncStream:
    """Async stream implementation (placeholder)."""


# httpx constants (placeholders)
DEFAULT_CIPHERS = "ALL:!aNULL:!eNULL:!SSLv2:!RC4:!DH:!3DES:!MD5:!PSK:!SRP:!CAMELLIA"
DEFAULT_TIMEOUT_CONFIG = {"connect": 5.0, "read": 5.0, "write": 5.0, "pool": 5.0}


# Define public API
__all__ = [
    # Constants
    "DEFAULT_CIPHERS",
    "DEFAULT_TIMEOUT_CONFIG",
    "URL",
    "AsyncClient",
    "AsyncHTTPTransport",
    "AsyncMockTransport",
    "AsyncStream",
    # Authentication
    "Auth",
    "BasicAuth",
    # Primary API (httpx-compatible names)
    "Client",
    "ConnectError",
    "ConnectTimeout",
    "Cookies",
    "DigestAuth",
    # Event hooks proxy for dynamic hook modification
    "EventHooksProxy",
    # Exception hierarchy (httpx-compatible ones)
    "HTTPError",
    "HTTPStatusError",
    # Transport classes
    "HTTPTransport",
    # Model classes (httpx-compatible names)
    "Headers",
    # Additional httpx-compatible exceptions
    "InvalidURL",
    "Limits",
    "LocalProtocolError",
    "MockTransport",
    "NetRCAuth",
    "PoolTimeout",
    "ProtocolError",
    "Proxy",
    "QueryParams",
    "ReadError",
    "ReadTimeout",
    "RemoteProtocolError",
    "Request",
    "RequestError",
    "Response",
    # Stream classes
    "Stream",
    "StreamError",
    "Timeout",
    "TimeoutException",
    "TooManyRedirects",
    "TransportError",
    "UnsupportedProtocol",
    "WriteError",
    "WriteTimeout",
    # Status codes and proxy configuration
    "codes",
    "delete",
    # Convenience functions
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "request",
    "stream",
]

if __name__ == "__main__":
    import sys

    print("faster-http: High-performance HTTP client")
    print("Usage: python -m faster_http")
    sys.exit(0)
