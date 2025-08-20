"""
faster-http: A high-performance HTTP client for Python, powered by Rust's hyper library.

This library provides a drop-in replacement for httpx with significantly better performance
by leveraging Rust's hyper library through PyO3 bindings.
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
    # Additional httpx-compatible exceptions
    InvalidURL,
    Limits,
    LocalProtocolError,
    # Transport classes temporarily disabled during hyper migration
    # MockTransport,
    NetRCAuth,
    PoolTimeout,
    ProtocolError,
    QueryParams,
    ReadError,
    ReadTimeout,
    RemoteProtocolError,
    RequestError,
    StreamError,
    Timeout,
    TimeoutException,
    TooManyRedirects,
    TransportError,
    UnsupportedProtocol,
    WriteError,
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

# Note: RustClient is available internally but not exposed in public API
from ._core import (
    HttpRequest as Request,
)
from ._core import (
    HttpResponse as Response,
)

# Import the Python wrapper Client instead of direct Rust Client
from ._wrapper_client import Client

# Import additional modules
from .codes import codes
from .proxy import Proxy

# All exception classes are now implemented in Rust and imported from _core
# httpx-compatible exception aliases for better compatibility
RequestTimeout = TimeoutException  # httpx uses RequestTimeout
ConnectionError = ConnectError     # httpx uses ConnectionError
SSLError = ConnectError           # Temporary alias, should be specific SSL error


# Note: Transport and authentication classes are implemented in Rust
# Stream functionality is provided through the Response object


# httpx constants (placeholders)
DEFAULT_CIPHERS = "ALL:!aNULL:!eNULL:!SSLv2:!RC4:!DH:!3DES:!MD5:!PSK:!SRP:!CAMELLIA"
DEFAULT_TIMEOUT_CONFIG = {"connect": 5.0, "read": 5.0, "write": 5.0, "pool": 5.0}


# Define public API
__all__ = [
    "DEFAULT_CIPHERS",
    "DEFAULT_TIMEOUT_CONFIG",
    "URL",
    "AsyncClient",
    "BasicAuth",
    "Client",
    "ConnectError",
    "ConnectTimeout",
    "ConnectionError",
    "Cookies",
    "DigestAuth",
    "HTTPError",
    "HTTPStatusError",
    "Headers",
    "InvalidURL",
    "Limits",
    "LocalProtocolError",
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
    "RequestTimeout",
    "Response",
    "SSLError",
    "StreamError",
    "Timeout",
    "TimeoutException",
    "TooManyRedirects",
    "TransportError",
    "UnsupportedProtocol",
    "WriteError",
    "WriteTimeout",
    "codes",
    "delete",
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
