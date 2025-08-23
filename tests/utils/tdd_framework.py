"""
Simplified TDD framework for faster-http development.

This module provides lightweight testing utilities focused on TDD development
without the complexity of full httpx compatibility testing.
"""

from collections.abc import Callable
import functools

import pytest

import faster_http


def tdd_test(func: Callable | None = None, *, timeout: float = 5.0):
    """
    Simple TDD test decorator for faster-http.

    This decorator focuses on fast, reliable test execution for TDD cycles.
    It only tests faster-http functionality without complex comparisons.

    Args:
        func: The test function to decorate
        timeout: Timeout in seconds for test execution

    Usage:
        @tdd_test
        def test_basic_get(client, test_server):
            response = client.get(f"{test_server.base_url}/get")
            assert response.status_code == 200
    """

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            # Simply run the test function - no complex logic
            return test_func(*args, **kwargs)

        # Mark as TDD test
        wrapper._is_tdd_test = True
        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


class SimpleClientFactory:
    """Simple client factory for TDD testing."""

    def __init__(self, library: str = "faster_http"):
        self.library = library

    def __call__(self, **kwargs):
        """Create a client instance."""
        return faster_http.Client(**kwargs)

    def get(self, url: str, **kwargs):
        """Make GET request."""
        return faster_http.get(url, **kwargs)

    def post(self, url: str, **kwargs):
        """Make POST request."""
        return faster_http.post(url, **kwargs)

    def put(self, url: str, **kwargs):
        """Make PUT request."""
        return faster_http.put(url, **kwargs)

    def patch(self, url: str, **kwargs):
        """Make PATCH request."""
        return faster_http.patch(url, **kwargs)

    def delete(self, url: str, **kwargs):
        """Make DELETE request."""
        return faster_http.delete(url, **kwargs)

    def head(self, url: str, **kwargs):
        """Make HEAD request."""
        return faster_http.head(url, **kwargs)

    def options(self, url: str, **kwargs):
        """Make OPTIONS request."""
        return faster_http.options(url, **kwargs)


class SimpleAsyncClientFactory:
    """Simple async client factory for TDD testing."""

    def __init__(self, library: str = "faster_http"):
        self.library = library

    def __call__(self, **kwargs):
        """Create an async client instance."""
        return faster_http.AsyncClient(**kwargs)


# Pytest fixtures for TDD
@pytest.fixture
def tdd_client():
    """Simple client factory for TDD tests."""
    return SimpleClientFactory()


@pytest.fixture
def tdd_async_client():
    """Simple async client factory for TDD tests."""
    return SimpleAsyncClientFactory()


def is_tdd_ready() -> bool:
    """Check if TDD environment is ready."""
    try:
        import faster_http

        # Try to create a basic client
        faster_http.Client()
        return True
    except Exception:
        return False
