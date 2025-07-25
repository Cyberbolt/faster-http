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
    StreamingClient,
    # Complete exception hierarchy
    HTTPError,
    ConnectError,
    ConnectTimeout,
    TimeoutException,
    ReadTimeout,
    WriteTimeout,
    PoolTimeout,
    RequestError,
    ResponseError,
    HTTPStatusError,
    ClientError,
    ServerError,
    StreamError,
    StreamConsumed,
    StreamClosed,
    ProtocolError,
    DecodingError,
    TooManyRedirects,
    TransportError,
    ProxyError,
    SSLError,
    CertificateError,
    NetworkError,
    DNSError,
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

import asyncio
from typing import List, Union


# Simple async iterator to wrap sync data for async iteration
class SimpleAsyncIterator:
    """Simple async iterator that wraps a list for async iteration."""
    
    def __init__(self, items: List):
        self._items = items
        self._index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self._index >= len(self._items):
            raise StopAsyncIteration
        
        item = self._items[self._index]
        self._index += 1
        
        # Yield control to allow other tasks to run
        await asyncio.sleep(0)
        return item


# Monkey patch Response class to provide true async iteration
def _patch_response_async_methods():
    """Patch Response class to provide httpx-compatible async iteration."""
    
    # Store original methods
    Response._orig_aiter_lines = Response.aiter_lines
    Response._orig_aiter_bytes = Response.aiter_bytes  
    Response._orig_aiter_text = Response.aiter_text
    Response._orig_aiter_raw = Response.aiter_raw
    
    # Replace with async wrapper versions
    def aiter_lines(self):
        lines = self._orig_aiter_lines()
        return SimpleAsyncIterator(lines)
    
    def aiter_bytes(self, chunk_size=None):
        chunks = self._orig_aiter_bytes(chunk_size)
        return SimpleAsyncIterator(chunks)
        
    def aiter_text(self, chunk_size=None):
        chunks = self._orig_aiter_text(chunk_size)
        return SimpleAsyncIterator(chunks)
        
    def aiter_raw(self, chunk_size=None):
        chunks = self._orig_aiter_raw(chunk_size)
        return SimpleAsyncIterator(chunks)
    
    Response.aiter_lines = aiter_lines
    Response.aiter_bytes = aiter_bytes
    Response.aiter_text = aiter_text
    Response.aiter_raw = aiter_raw

# Apply the patch
_patch_response_async_methods()


# Define public API
__all__ = [
    # Primary API (httpx-compatible names)
    "Client",
    "AsyncClient",
    "Request", 
    "Response",
    "StreamingResponse",
    "StreamingClient",
    # Original names (for advanced users)
    "HttpClient",
    "AsyncHttpClient",
    "HttpRequest",
    "HttpResponse", 
    "StreamingHttpResponse",
    # Exception hierarchy
    "HTTPError",
    "ConnectError",
    "ConnectTimeout",
    "TimeoutException",
    "ReadTimeout",
    "WriteTimeout",
    "PoolTimeout",
    "RequestError",
    "ResponseError",
    "HTTPStatusError",
    "ClientError",
    "ServerError",
    "StreamError",
    "StreamConsumed",
    "StreamClosed",
    "ProtocolError",
    "DecodingError",
    "TooManyRedirects",
    "TransportError",
    "ProxyError",
    "SSLError",
    "CertificateError",
    "NetworkError",
    "DNSError", 
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