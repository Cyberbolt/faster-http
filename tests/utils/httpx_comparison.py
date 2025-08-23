"""
HTTP compatibility testing framework for comparing faster-http with httpx.

This module provides decorators and utilities to automatically test
faster-http implementations against httpx for compatibility verification.
"""

import asyncio
from collections.abc import Callable
import functools
import json
from typing import Any

import httpx
import pytest

import faster_http


class ComparisonResult:
    """Results of comparing httpx and faster-http responses."""

    def __init__(self, httpx_result: Any, faster_http_result: Any, differences: dict[str, Any]):
        self.httpx_result = httpx_result
        self.faster_http_result = faster_http_result
        self.differences = differences
        self.is_compatible = len(differences) == 0


class ClientFactory:
    """Factory for creating HTTP clients for testing."""

    def __init__(self, library: str):
        self.library = library

    def __call__(self, *args, **kwargs):
        """Create a client instance."""
        if self.library == "httpx":
            return httpx.Client(*args, **kwargs)
        elif self.library == "faster_http":
            return faster_http.Client(*args, **kwargs)
        else:
            raise ValueError(f"Unknown library: {self.library}")

    def get(self, url: str, **kwargs):
        """Make GET request using top-level function."""
        if self.library == "httpx":
            return httpx.get(url, **kwargs)
        elif self.library == "faster_http":
            return faster_http.get(url, **kwargs)

    def post(self, url: str, **kwargs):
        """Make POST request using top-level function."""
        if self.library == "httpx":
            return httpx.post(url, **kwargs)
        elif self.library == "faster_http":
            return faster_http.post(url, **kwargs)

    def put(self, url: str, **kwargs):
        """Make PUT request using top-level function."""
        if self.library == "httpx":
            return httpx.put(url, **kwargs)
        elif self.library == "faster_http":
            return faster_http.put(url, **kwargs)

    def patch(self, url: str, **kwargs):
        """Make PATCH request using top-level function."""
        if self.library == "httpx":
            return httpx.patch(url, **kwargs)
        elif self.library == "faster_http":
            return faster_http.patch(url, **kwargs)

    def delete(self, url: str, **kwargs):
        """Make DELETE request using top-level function."""
        if self.library == "httpx":
            return httpx.delete(url, **kwargs)
        elif self.library == "faster_http":
            return faster_http.delete(url, **kwargs)

    def head(self, url: str, **kwargs):
        """Make HEAD request using top-level function."""
        if self.library == "httpx":
            return httpx.head(url, **kwargs)
        elif self.library == "faster_http":
            return faster_http.head(url, **kwargs)

    def options(self, url: str, **kwargs):
        """Make OPTIONS request using top-level function."""
        if self.library == "httpx":
            return httpx.options(url, **kwargs)
        elif self.library == "faster_http":
            return faster_http.options(url, **kwargs)

    def stream(self, method: str, url: str, **kwargs):
        """Make streaming request."""
        if self.library == "httpx":
            return httpx.stream(method, url, **kwargs)
        elif self.library == "faster_http":
            return faster_http.stream(method, url, **kwargs)


class AsyncClientFactory:
    """Factory for creating async HTTP clients for testing."""

    def __init__(self, library: str):
        self.library = library

    def __call__(self, *args, **kwargs):
        """Create an async client instance."""
        if self.library == "httpx":
            return httpx.AsyncClient(*args, **kwargs)
        elif self.library == "faster_http":
            return faster_http.AsyncClient(*args, **kwargs)
        else:
            raise ValueError(f"Unknown library: {self.library}")


def compare_responses(httpx_response, faster_http_response) -> ComparisonResult:
    """
    Compare httpx and faster-http responses for compatibility.

    Args:
        httpx_response: Response from httpx
        faster_http_response: Response from faster-http

    Returns:
        ComparisonResult with differences and compatibility status
    """
    differences = {}

    # Compare status codes
    if httpx_response.status_code != faster_http_response.status_code:
        differences["status_code"] = {
            "httpx": httpx_response.status_code,
            "faster_http": faster_http_response.status_code,
        }

    # Compare response text (with some tolerance for minor differences)
    try:
        httpx_text = httpx_response.text
        faster_http_text = faster_http_response.text

        if httpx_text != faster_http_text:
            # Try parsing as JSON to compare structured data
            try:
                httpx_json = json.loads(httpx_text) if httpx_text else None
                faster_http_json = json.loads(faster_http_text) if faster_http_text else None

                if httpx_json != faster_http_json:
                    differences["content"] = {"httpx": httpx_json, "faster_http": faster_http_json}
            except json.JSONDecodeError:
                # Non-JSON content, compare directly
                if httpx_text != faster_http_text:
                    differences["text"] = {
                        "httpx": httpx_text[:200] + "..." if len(httpx_text) > 200 else httpx_text,
                        "faster_http": faster_http_text[:200] + "..."
                        if len(faster_http_text) > 200
                        else faster_http_text,
                    }
    except Exception as e:
        differences["text_comparison_error"] = str(e)

    # Compare headers (case-insensitive)
    httpx_headers = {k.lower(): v for k, v in httpx_response.headers.items()}
    faster_http_headers = {k.lower(): v for k, v in faster_http_response.headers.items()}

    # Only compare headers that should be the same (exclude server-specific headers)
    ignored_headers = {"date", "server", "connection", "keep-alive", "content-length"}

    for key, value in httpx_headers.items():
        if key not in ignored_headers and key in faster_http_headers and value != faster_http_headers[key]:
            if "headers" not in differences:
                differences["headers"] = {}
            differences["headers"][key] = {"httpx": value, "faster_http": faster_http_headers[key]}

    return ComparisonResult(httpx_response, faster_http_response, differences)


def compare_exceptions(httpx_exception, faster_http_exception) -> ComparisonResult:
    """
    Compare exceptions raised by httpx and faster-http.

    Args:
        httpx_exception: Exception from httpx
        faster_http_exception: Exception from faster-http

    Returns:
        ComparisonResult with differences and compatibility status
    """
    differences = {}

    # Compare exception types
    if type(httpx_exception).__name__ != type(faster_http_exception).__name__:
        differences["exception_type"] = {
            "httpx": type(httpx_exception).__name__,
            "faster_http": type(faster_http_exception).__name__,
        }

    # Compare exception messages (with some tolerance)
    httpx_msg = str(httpx_exception)
    faster_http_msg = str(faster_http_exception)

    # Basic message comparison (ignore minor differences)
    if httpx_msg != faster_http_msg:
        differences["exception_message"] = {"httpx": httpx_msg, "faster_http": faster_http_msg}

    return ComparisonResult(httpx_exception, faster_http_exception, differences)


def httpx_compatibility_test(
    func: Callable | None = None,
    *,
    strict: bool = False,
    ignore_differences: list | None = None,
    skip_httpx: bool = False,
    timeout: float = 5.0,
):
    """
    Decorator for testing httpx compatibility.

    This decorator runs the same test function with both httpx and faster-http,
    comparing the results to ensure compatibility.

    Args:
        func: The test function to decorate
        strict: If True, any difference fails the test
        ignore_differences: List of difference types to ignore
        skip_httpx: If True, skip httpx execution (for development speed)
        timeout: Timeout in seconds for each test execution

    Usage:
        @httpx_compatibility_test
        def test_get_request(client_factory, test_server):
            response = client_factory.get(f"{test_server.base_url}/get")
            assert response.status_code == 200
    """
    if ignore_differences is None:
        ignore_differences = []

    def decorator(test_func):
        @functools.wraps(test_func)
        def sync_wrapper(*args, **kwargs):
            import os
            import signal

            # Check if we should skip httpx comparison for speed
            skip_httpx_comparison = skip_httpx or os.getenv("SKIP_HTTPX_COMPARISON", "false").lower() == "true"

            httpx_result = None
            httpx_exception = None

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Test execution exceeded {timeout} seconds")

            # Run test with httpx first (if not skipped)
            if not skip_httpx_comparison:
                httpx_factory = ClientFactory("httpx")
                httpx_async_factory = AsyncClientFactory("httpx")

                try:
                    # Set timeout
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(int(timeout))

                    # Replace client_factory in kwargs for httpx
                    httpx_kwargs = kwargs.copy()
                    if "client_factory" in httpx_kwargs:
                        httpx_kwargs["client_factory"] = httpx_factory
                    if "async_client_factory" in httpx_kwargs:
                        httpx_kwargs["async_client_factory"] = httpx_async_factory

                    httpx_result = test_func(*args, **httpx_kwargs)
                except Exception as e:
                    httpx_exception = e
                finally:
                    signal.alarm(0)  # Cancel the alarm

            # Run test with faster-http
            faster_http_factory = ClientFactory("faster_http")
            faster_http_async_factory = AsyncClientFactory("faster_http")

            faster_http_result = None
            faster_http_exception = None

            try:
                # Set timeout
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(timeout))

                # Replace client_factory in kwargs for faster-http
                faster_http_kwargs = kwargs.copy()
                if "client_factory" in faster_http_kwargs:
                    faster_http_kwargs["client_factory"] = faster_http_factory
                if "async_client_factory" in faster_http_kwargs:
                    faster_http_kwargs["async_client_factory"] = faster_http_async_factory

                faster_http_result = test_func(*args, **faster_http_kwargs)
            except Exception as e:
                faster_http_exception = e
            finally:
                signal.alarm(0)  # Cancel the alarm

            # Only compare if we ran both tests
            if not skip_httpx_comparison:
                # Compare results
                if httpx_exception and faster_http_exception:
                    # Both raised exceptions - compare exceptions
                    comparison = compare_exceptions(httpx_exception, faster_http_exception)
                    if not comparison.is_compatible and strict:
                        raise AssertionError(f"Exception compatibility mismatch: {comparison.differences}")
                elif httpx_exception:
                    # Only httpx raised exception
                    raise AssertionError(f"httpx raised exception but faster-http didn't: {httpx_exception}")
                elif faster_http_exception:
                    # Only faster-http raised exception
                    raise AssertionError(f"faster-http raised exception but httpx didn't: {faster_http_exception}")
                else:
                    # Both succeeded - compare results if they are responses
                    if hasattr(httpx_result, "status_code") and hasattr(faster_http_result, "status_code"):
                        comparison = compare_responses(httpx_result, faster_http_result)
                        if not comparison.is_compatible and strict:
                            # Filter out ignored differences
                            filtered_differences = {
                                k: v for k, v in comparison.differences.items() if k not in ignore_differences
                            }
                            if filtered_differences:
                                raise AssertionError(f"Response compatibility mismatch: {filtered_differences}")
            else:
                # If we skipped httpx, just check that faster-http didn't fail
                if faster_http_exception:
                    raise faster_http_exception

            # Return the faster-http result for the test
            return faster_http_result

        @functools.wraps(test_func)
        async def async_wrapper(*args, **kwargs):
            import asyncio
            import os

            # Check if we should skip httpx comparison for speed
            skip_httpx_comparison = skip_httpx or os.getenv("SKIP_HTTPX_COMPARISON", "false").lower() == "true"

            httpx_result = None
            httpx_exception = None

            # Run test with httpx first (if not skipped)
            if not skip_httpx_comparison:
                httpx_factory = ClientFactory("httpx")
                httpx_async_factory = AsyncClientFactory("httpx")

                try:
                    # Replace client_factory in kwargs for httpx
                    httpx_kwargs = kwargs.copy()
                    if "client_factory" in httpx_kwargs:
                        httpx_kwargs["client_factory"] = httpx_factory
                    if "async_client_factory" in httpx_kwargs:
                        httpx_kwargs["async_client_factory"] = httpx_async_factory

                    # Run with timeout
                    httpx_result = await asyncio.wait_for(test_func(*args, **httpx_kwargs), timeout=timeout)
                except Exception as e:
                    httpx_exception = e

            # Run test with faster-http
            faster_http_factory = ClientFactory("faster_http")
            faster_http_async_factory = AsyncClientFactory("faster_http")

            faster_http_result = None
            faster_http_exception = None

            try:
                # Replace client_factory in kwargs for faster-http
                faster_http_kwargs = kwargs.copy()
                if "client_factory" in faster_http_kwargs:
                    faster_http_kwargs["client_factory"] = faster_http_factory
                if "async_client_factory" in faster_http_kwargs:
                    faster_http_kwargs["async_client_factory"] = faster_http_async_factory

                # Run with timeout
                faster_http_result = await asyncio.wait_for(test_func(*args, **faster_http_kwargs), timeout=timeout)
            except Exception as e:
                faster_http_exception = e

            # Only compare if we ran both tests
            if not skip_httpx_comparison:
                # Compare results (same logic as sync version)
                if httpx_exception and faster_http_exception:
                    comparison = compare_exceptions(httpx_exception, faster_http_exception)
                    if not comparison.is_compatible and strict:
                        raise AssertionError(f"Exception compatibility mismatch: {comparison.differences}")
                elif httpx_exception:
                    raise AssertionError(f"httpx raised exception but faster-http didn't: {httpx_exception}")
                elif faster_http_exception:
                    raise AssertionError(f"faster-http raised exception but httpx didn't: {faster_http_exception}")
                else:
                    if hasattr(httpx_result, "status_code") and hasattr(faster_http_result, "status_code"):
                        comparison = compare_responses(httpx_result, faster_http_result)
                        if not comparison.is_compatible and strict:
                            filtered_differences = {
                                k: v for k, v in comparison.differences.items() if k not in ignore_differences
                            }
                            if filtered_differences:
                                raise AssertionError(f"Response compatibility mismatch: {filtered_differences}")
            else:
                # If we skipped httpx, just check that faster-http didn't fail
                if faster_http_exception:
                    raise faster_http_exception

            return faster_http_result

        # Return appropriate wrapper based on whether the test function is async
        if asyncio.iscoroutinefunction(test_func):
            return async_wrapper
        else:
            return sync_wrapper

    # Handle decorator with or without arguments
    if func is None:
        return decorator
    else:
        return decorator(func)


# Pytest fixtures for client factories
@pytest.fixture
def client_factory():
    """Fixture providing a client factory for the current library being tested."""
    return ClientFactory("faster_http")


@pytest.fixture
def async_client_factory():
    """Fixture providing an async client factory for the current library being tested."""
    return AsyncClientFactory("faster_http")


@pytest.fixture
def httpx_client_factory():
    """Fixture providing httpx client factory for comparison tests."""
    return ClientFactory("httpx")


@pytest.fixture
def httpx_async_client_factory():
    """Fixture providing httpx async client factory for comparison tests."""
    return AsyncClientFactory("httpx")
