"""
faster-http: A high-performance HTTP client for Python, powered by Rust's reqwest library.

This library provides a drop-in replacement for httpx with significantly better performance
by leveraging Rust's reqwest library through PyO3 bindings.
"""

from ._core import (
    # Core client classes
    HttpClient as _HttpClient,
    AsyncHttpClient as _AsyncHttpClient,
    HttpRequest as _HttpRequest,
    HttpResponse as _HttpResponse,
    StreamingHttpResponse as _StreamingHttpResponse,
    
    # Exception types
    HTTPError,
    ConnectTimeout,
    ReadTimeout,
    RequestError,
    
    # Data structures
    Headers as _Headers,
    QueryParams as _QueryParams,
    Cookies as _Cookies,
    URL as _URL,
    Timeout as _Timeout,
    Limits as _Limits,
    BasicAuth as _BasicAuth,
    DigestAuth as _DigestAuth,
    NetRCAuth as _NetRCAuth,
    
    # Global functions
    get,
    post,
    put,
    patch,
    delete,
    head,
    options,
    stream,
)

__version__ = "0.1.0"
__all__ = [
    "get", "post", "put", "patch", "delete", "head", "options", "stream",
    "Client", "AsyncClient", "Response", "StreamingResponse", "Request",
    "HTTPError", "ConnectTimeout", "ReadTimeout", "RequestError",
    "BasicAuth", "DigestAuth", "NetRCAuth",
    "URL", "Headers", "Cookies", "QueryParams",
    "Timeout", "Limits", 
]

# Use Rust's implementations - these are the exported public API
Client = _HttpClient
AsyncClient = _AsyncHttpClient
Request = _HttpRequest
Response = _HttpResponse
StreamingResponse = _StreamingHttpResponse
Headers = _Headers
QueryParams = _QueryParams
Cookies = _Cookies
URL = _URL
Timeout = _Timeout
Limits = _Limits
BasicAuth = _BasicAuth
DigestAuth = _DigestAuth
NetRCAuth = _NetRCAuth

# CLI entry point
def main():
    """CLI entry point."""
    import sys
    print("faster-http: High-performance HTTP client")
    print("Usage: python -m faster_http")
    sys.exit(0)

# Entry point
if __name__ == "__main__":
    main()
