"""Comparison utilities for testing faster-http against httpx."""

import httpx
import faster_http
from typing import Any, Dict, Optional, Callable, Union
import asyncio


class ComparisonResult:
    """Result of a comparison between httpx and faster-http."""
    
    def __init__(self, httpx_result: Any, faster_http_result: Any):
        self.httpx_result = httpx_result
        self.faster_http_result = faster_http_result
    
    def assert_status_equal(self):
        """Assert that status codes are equal."""
        assert self.httpx_result.status_code == self.faster_http_result.status_code, \
            f"Status codes differ: httpx={self.httpx_result.status_code}, " \
            f"faster-http={self.faster_http_result.status_code}"
    
    def assert_headers_compatible(self):
        """Assert that headers are compatible (allowing for minor differences)."""
        # Check that all important headers match
        important_headers = ['content-type', 'content-length', 'server']
        for header in important_headers:
            httpx_val = self.httpx_result.headers.get(header)
            faster_val = self.faster_http_result.headers.get(header)
            if httpx_val is not None and faster_val is not None:
                assert httpx_val.lower() == faster_val.lower(), \
                    f"Header {header} differs: httpx={httpx_val}, faster-http={faster_val}"
    
    def assert_content_equal(self):
        """Assert that response content is equal."""
        assert self.httpx_result.content == self.faster_http_result.content, \
            "Response content differs between httpx and faster-http"
    
    def assert_json_equal(self):
        """Assert that JSON response is equal."""
        httpx_json = self.httpx_result.json()
        faster_json = self.faster_http_result.json()
        assert httpx_json == faster_json, \
            "JSON response differs between httpx and faster-http"
    
    def assert_basic_compatibility(self):
        """Assert basic compatibility between responses."""
        self.assert_status_equal()
        self.assert_headers_compatible()
        if self.httpx_result.status_code == 200:
            self.assert_content_equal()


def compare_sync_request(
    method: str,
    url: str,
    **kwargs
) -> ComparisonResult:
    """Compare a sync request between httpx and faster-http."""
    # Run with httpx first
    httpx_response = httpx.request(method, url, **kwargs)
    
    # Run with faster-http second
    faster_http_response = faster_http.request(method, url, **kwargs)
    
    return ComparisonResult(httpx_response, faster_http_response)


async def compare_async_request(
    method: str,
    url: str,
    **kwargs
) -> ComparisonResult:
    """Compare an async request between httpx and faster-http."""
    # Run with httpx first
    async with httpx.AsyncClient() as httpx_client:
        httpx_response = await httpx_client.request(method, url, **kwargs)
    
    # Run with faster-http second
    async with faster_http.AsyncClient() as faster_client:
        faster_http_response = await faster_client.request(method, url, **kwargs)
    
    return ComparisonResult(httpx_response, faster_http_response)


def compare_sync_clients(
    method: str,
    url: str,
    client_kwargs: Optional[Dict[str, Any]] = None,
    request_kwargs: Optional[Dict[str, Any]] = None
) -> ComparisonResult:
    """Compare sync clients between httpx and faster-http."""
    client_kwargs = client_kwargs or {}
    request_kwargs = request_kwargs or {}
    
    # Run with httpx first
    with httpx.Client(**client_kwargs) as httpx_client:
        httpx_response = httpx_client.request(method, url, **request_kwargs)
    
    # Run with faster-http second
    with faster_http.Client(**client_kwargs) as faster_client:
        faster_http_response = faster_client.request(method, url, **request_kwargs)
    
    return ComparisonResult(httpx_response, faster_http_response)


async def compare_async_clients(
    method: str,
    url: str,
    client_kwargs: Optional[Dict[str, Any]] = None,
    request_kwargs: Optional[Dict[str, Any]] = None
) -> ComparisonResult:
    """Compare async clients between httpx and faster-http."""
    client_kwargs = client_kwargs or {}
    request_kwargs = request_kwargs or {}
    
    # Run with httpx first
    async with httpx.AsyncClient(**client_kwargs) as httpx_client:
        httpx_response = await httpx_client.request(method, url, **request_kwargs)
    
    # Run with faster-http second
    async with faster_http.AsyncClient(**client_kwargs) as faster_client:
        faster_http_response = await faster_client.request(method, url, **request_kwargs)
    
    return ComparisonResult(httpx_response, faster_http_response)


def assert_response_attributes_equal(httpx_response, faster_http_response):
    """Assert that response objects have equivalent attributes."""
    # Check that both have the same basic attributes
    basic_attrs = ['status_code', 'headers', 'url', 'elapsed', 'content']
    
    for attr in basic_attrs:
        assert hasattr(httpx_response, attr), f"httpx response missing {attr}"
        assert hasattr(faster_http_response, attr), f"faster-http response missing {attr}"
    
    # Check boolean properties
    bool_attrs = ['ok', 'is_redirect', 'is_client_error', 'is_server_error']
    for attr in bool_attrs:
        httpx_val = getattr(httpx_response, attr)
        faster_val = getattr(faster_http_response, attr)
        assert httpx_val == faster_val, f"Boolean attribute {attr} differs"
    
    # Check methods exist
    methods = ['json', 'raise_for_status', 'iter_bytes', 'iter_text', 'iter_lines']
    for method in methods:
        assert hasattr(httpx_response, method), f"httpx response missing method {method}"
        assert hasattr(faster_http_response, method), f"faster-http response missing method {method}"
        assert callable(getattr(httpx_response, method)), f"httpx {method} not callable"
        assert callable(getattr(faster_http_response, method)), f"faster-http {method} not callable"