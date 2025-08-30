"""
faster-http: HTTP client compatible with httpx API, powered by Rust's hyper library.

This library provides a drop-in replacement for httpx API, implemented using Rust's hyper library through PyO3 bindings.
"""

__version__ = "0.1.0"

# Import specific classes for explicit re-export
# Import Proxy directly without exposing the module
from . import proxy as _proxy_module
from ._core import (
    URL,
    # Missing httpx core components - Fixed
    USE_CLIENT_DEFAULT,
    ASGITransport,
    AsyncBaseTransport,
    AsyncByteStream,
    AsyncHTTPTransport,
    Auth,
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
    # Main function for CLI compatibility
    main,
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

Proxy = _proxy_module.Proxy
del _proxy_module

# All exception classes are now implemented in Rust and imported from _core
# Remove non-httpx compatible aliases - these don't exist in httpx

# Enhance existing exception classes to support keyword arguments

# Store references to original constructors
_orig_http_status_error_new = HTTPStatusError.__new__
_orig_http_status_error_init = HTTPStatusError.__init__
_orig_request_error_init = RequestError.__init__


def _standard_httpstatuserror_new(cls, message=None, *, request=None, response=None):
    """Standard HTTPStatusError constructor with keyword argument support."""
    if message is None:
        message = "HTTP status error"
    # Use the original constructor for all cases
    if _orig_http_status_error_new is object.__new__:
        return object.__new__(cls)
    else:
        return _orig_http_status_error_new(cls)


def _standard_httpstatuserror_init(self, message=None, *, request=None, response=None):
    """Standard HTTPStatusError initializer."""
    if message is None:
        message = "HTTP status error"
    _orig_http_status_error_init(self, message)
    # Store request and response as attributes for httpx compatibility
    if request is not None:
        self.request = request
    if response is not None:
        self.response = response


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

# Explicitly remove proxy module reference to prevent exposure
# The proxy module gets imported automatically when we import from .proxy
# We need to manually remove it to match httpx interface exactly
try:
    del proxy
except NameError:
    pass

if __name__ == "__main__":
    import sys
    # Module information available through __doc__ or help() if needed
    sys.exit(0)
