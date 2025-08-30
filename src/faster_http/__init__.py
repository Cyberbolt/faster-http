"""
faster-http: HTTP client compatible with httpx API, powered by Rust's hyper library.

This library provides a drop-in replacement for httpx API, implemented using Rust's hyper library through PyO3 bindings.
"""

__version__ = "0.1.0"

# Import specific classes for explicit re-export
from ._core import (
    URL,
    # 8 missing httpx core components - Critical API compatibility fix
    USE_CLIENT_DEFAULT,
    ASGITransport,
    AsyncByteStream,
    AsyncHTTPTransport,
    BaseTransport,
    BasicAuth,
    ByteStream,
    # Missing httpx-compatible exceptions
    CloseError,
    ConnectError,
    ConnectTimeout,
    CookieConflict,
    Cookies,
    DecodingError,
    DigestAuth,
    # Model classes with httpx-compatible names
    Headers,
    # Exception hierarchy (only httpx-compatible ones)
    HTTPError,
    HTTPStatusError,
    HTTPTransport,
    # Additional httpx-compatible exceptions
    InvalidURL,
    Limits,
    LocalProtocolError,
    # Transport classes temporarily disabled during hyper migration
    MockTransport,
    NetRCAuth,
    NetworkError,  # Re-added - exists in httpx and now properly implemented
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
    SSLError,
    StreamClosed,
    StreamConsumed,
    StreamError,
    SyncByteStream,
    # Timeout imported separately below
    TimeoutException,
    TooManyRedirects,
    TransportError,
    UnsupportedProtocol,
    WriteError,
    WriteTimeout,
    WSGITransport,
    create_ssl_context,
    delete,
    # HTTP methods
    get,
    head,
    # Exception factory functions
    new_http_status_error,
    options,
    patch,
    post,
    put,
    request,
    stream,
)

# Note: RustClient is available internally but not exposed in public API
from ._core import (
    HttpRequest as Request,
)
from ._core import (
    HttpResponse as Response,
)

# Import the Python wrapper Timeout instead of direct Rust Timeout
from ._timeout import Timeout

# Import the Python wrapper AsyncClient instead of direct Rust AsyncClient
# Import the Python wrapper Client instead of direct Rust Client
from ._wrapper_client import AsyncClient, Client

# Import additional modules
from .codes import codes
from .proxy import Proxy

# All exception classes are now implemented in Rust and imported from _core
# httpx-compatible exception aliases for compatibility
RequestTimeout = TimeoutException  # httpx uses RequestTimeout
ConnectionError = ConnectError  # httpx uses ConnectionError
# SSLError now imported directly from _core with proper implementation

# Enhance existing exception classes to support keyword arguments

# Store references to original constructors
_orig_http_status_error_new = HTTPStatusError.__new__
_orig_http_status_error_init = HTTPStatusError.__init__
_orig_request_error_init = RequestError.__init__


def _standard_httpstatuserror_new(cls, message=None, *, request=None, response=None):
    """Standard HTTPStatusError constructor with keyword argument support."""
    if message is None:
        message = "HTTP status error"
    if request is not None or response is not None:
        # Use the factory function for keyword arguments - it returns the proper instance
        return new_http_status_error(message, request=request, response=response)
    else:
        # Use the original constructor for positional arguments
        if _orig_http_status_error_new is object.__new__:
            return object.__new__(cls)
        else:
            return _orig_http_status_error_new(cls)


def _standard_httpstatuserror_init(self, message=None, *, request=None, response=None):
    """Standard HTTPStatusError initializer."""
    if message is None:
        message = "HTTP status error"
    # Only initialize if not already done by factory function
    if not hasattr(self, "args") or len(self.args) == 0:
        _orig_http_status_error_init(self, message)


def _standard_requesterror_init(self, message=None, *, request=None):
    """Standard RequestError initializer with keyword argument support."""
    if message is None:
        message = "Request error"
    _orig_request_error_init(self, message)
    if request is not None:
        self.request = request


# Apply standard implementations to existing classes
HTTPStatusError.__new__ = _standard_httpstatuserror_new
HTTPStatusError.__init__ = _standard_httpstatuserror_init
RequestError.__init__ = _standard_requesterror_init


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
    "USE_CLIENT_DEFAULT",
    "ASGITransport",
    "AsyncByteStream",
    "AsyncClient",
    "AsyncHTTPTransport",
    "BaseTransport",
    "BasicAuth",
    "ByteStream",
    "Client",
    "CloseError",
    "ConnectError",
    "ConnectTimeout",
    "ConnectionError",
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
    "RequestTimeout",
    "Response",
    "ResponseNotRead",
    "SSLError",
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
    "codes",
    "create_ssl_context",
    "delete",
    "get",
    "head",
    "new_http_status_error",
    "options",
    "patch",
    "post",
    "put",
    "request",
    "stream",
]

if __name__ == "__main__":
    import sys
    # Module information available through __doc__ or help() if needed
    sys.exit(0)
