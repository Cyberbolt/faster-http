"""
faster-http: A high-performance HTTP client for Python, powered by Rust's reqwest library.

This library provides a drop-in replacement for httpx with significantly better performance
by leveraging Rust's reqwest library through PyO3 bindings.
"""

from ._core import (
    HttpClient as _HttpClient,
    HttpRequest as _HttpRequest,
    HTTPError,
    ConnectTimeout,
    ReadTimeout,
    RequestError,
)

# Import from our modules
from .auth import Auth, BasicAuth, DigestAuth, NetRCAuth
from .models import URL, Headers, Cookies, QueryParams, Timeout, Limits
from .responses import Response, StreamingResponse
from .client import AsyncClient
from .api import get, post, put, patch, delete, head, options, stream, main

__version__ = "0.1.0"
__all__ = [
    "get", "post", "put", "patch", "delete", "head", "options", "stream",
    "Client", "AsyncClient", "Response", "StreamingResponse", "Request",
    "HTTPError", "ConnectTimeout", "ReadTimeout", "RequestError",
    "BasicAuth", "DigestAuth", "NetRCAuth", "Auth",
    "URL", "Headers", "Cookies", "QueryParams",
    "Timeout", "Limits", 
]

# Use Rust's HttpClient and HttpRequest
Client = _HttpClient
Request = _HttpRequest

# Entry point
if __name__ == "__main__":
    main()
