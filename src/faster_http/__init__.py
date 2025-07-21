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
    StreamingHttpResponse as StreamingResponse,
    HTTPError,
    ConnectTimeout,
    ReadTimeout,
    RequestError,
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


# Define public API
__all__ = [
    # Primary API (httpx-compatible names)
    "Client",
    "AsyncClient",
    "Request", 
    "Response",
    "StreamingResponse",
    # Original names (for advanced users)
    "HttpClient",
    "AsyncHttpClient",
    "HttpRequest",
    "HttpResponse", 
    "StreamingHttpResponse",
    # Exception hierarchy
    "HTTPError",
    "ConnectTimeout",
    "ReadTimeout",
    "RequestError", 
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
    # Model classes (already httpx-compatible names)
    "Headers",
    "QueryParams",
    "Cookies", 
    "URL",
    "Timeout",
    "Limits",
    "BasicAuth",
    "DigestAuth", 
    "NetRCAuth",
]

def main():
    """CLI entry point."""
    import sys
    print("faster-http: High-performance HTTP client")
    print("Usage: python -m faster_http")
    sys.exit(0)

if __name__ == "__main__":
    main()