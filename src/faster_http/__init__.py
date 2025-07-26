"""
faster-http: A high-performance HTTP client for Python, powered by Rust's reqwest library.

This library provides a drop-in replacement for httpx with significantly better performance
by leveraging Rust's reqwest library through PyO3 bindings.
"""

__version__ = "0.1.0"

# Import specific classes for explicit re-export
from ._core import (
    HttpClient as Client, 
    AsyncHttpClient as AsyncClient, 
    HttpRequest as Request,
    HttpResponse as Response,
    # Exception hierarchy (only httpx-compatible ones)
    HTTPError,
    ConnectError,
    ConnectTimeout,
    TimeoutException,
    ReadTimeout,
    WriteTimeout,
    PoolTimeout,
    RequestError,
    HTTPStatusError,
    StreamError,
    ProtocolError,
    TooManyRedirects,
    TransportError,
    # Transport classes (import available ones from Rust)
    MockTransport,
    # HTTP methods
    get,
    post,
    put,
    patch,
    delete,
    head,
    options,
    request,
    stream,
    # Model classes with httpx-compatible names
    Headers,
    QueryParams, 
    Cookies,
    URL,
    Timeout,
    Limits,
    BasicAuth,
    DigestAuth,
    NetRCAuth,
)

# Import additional modules
from .codes import codes
from .proxy import Proxy
from .event_hooks_proxy import EventHooksProxy

import asyncio

# Create httpx-compatible exception classes that don't exist in Rust code
class InvalidURL(RequestError):
    """Raised when a URL is malformed."""
    pass

class LocalProtocolError(ProtocolError):
    """Raised for local protocol violations."""
    pass

class RemoteProtocolError(ProtocolError):
    """Raised for remote protocol violations."""
    pass

class ReadError(RequestError):
    """Raised when a read error occurs."""
    pass

class WriteError(RequestError):
    """Raised when a write error occurs."""
    pass

class UnsupportedProtocol(RequestError):
    """Raised when an unsupported protocol is used."""
    pass

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
    pass

class AsyncStream:
    """Async stream implementation (placeholder)."""
    pass

# httpx constants (placeholders)
DEFAULT_CIPHERS = "ALL:!aNULL:!eNULL:!SSLv2:!RC4:!DH:!3DES:!MD5:!PSK:!SRP:!CAMELLIA"
DEFAULT_TIMEOUT_CONFIG = {"connect": 5.0, "read": 5.0, "write": 5.0, "pool": 5.0}




# Define public API
__all__ = [
    # Primary API (httpx-compatible names)
    "Client",
    "AsyncClient",
    "Request", 
    "Response",
    # Exception hierarchy (httpx-compatible ones)
    "HTTPError",
    "ConnectError", 
    "ConnectTimeout",
    "TimeoutException",
    "ReadTimeout",
    "WriteTimeout",
    "PoolTimeout",
    "RequestError",
    "HTTPStatusError",
    "StreamError",
    "ProtocolError",
    "TooManyRedirects",
    "TransportError",
    # Additional httpx-compatible exceptions
    "InvalidURL",
    "LocalProtocolError",
    "RemoteProtocolError", 
    "ReadError",
    "WriteError",
    "UnsupportedProtocol",
    # Convenience functions
    "get",
    "post",
    "put",
    "patch", 
    "delete",
    "head",
    "options",
    "request",
    "stream",
    # Model classes (httpx-compatible names)
    "Headers",
    "QueryParams",
    "Cookies", 
    "URL",
    "Timeout",
    "Limits",
    "BasicAuth",
    "DigestAuth", 
    "NetRCAuth",
    # Transport classes  
    "HTTPTransport",
    "AsyncHTTPTransport",
    "AsyncMockTransport",
    "MockTransport",
    # Authentication
    "Auth",
    # Stream classes
    "Stream", 
    "AsyncStream",
    # Constants
    "DEFAULT_CIPHERS",
    "DEFAULT_TIMEOUT_CONFIG",
    # Status codes and proxy configuration
    "codes",
    "Proxy",
    # Event hooks proxy for dynamic hook modification
    "EventHooksProxy",
]

if __name__ == "__main__":
    import sys
    print("faster-http: High-performance HTTP client")
    print("Usage: python -m faster_http")
    sys.exit(0)