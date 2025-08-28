"""Tests for exception classes."""

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test


def get_exception_class(client_factory, exception_name):
    """
    Get the appropriate exception class based on the client library.

    Args:
        client_factory: The client factory instance
        exception_name: Name of the exception (e.g., 'TimeoutException', 'ConnectError')

    Returns:
        The exception class from the appropriate library
    """
    if client_factory.library == "httpx":
        import httpx

        # Map faster_http exception names to httpx exception names
        exception_mapping = {
            "TimeoutException": "ReadTimeout",  # httpx uses more specific timeout exceptions
            "ConnectError": "ConnectError",
            "HTTPStatusError": "HTTPStatusError",
            "InvalidURL": "UnsupportedProtocol",  # httpx uses different name for URL errors
            "TooManyRedirects": "TooManyRedirects",
        }
        httpx_exception_name = exception_mapping.get(exception_name, exception_name)
        return getattr(httpx, httpx_exception_name)
    else:
        # faster_http
        import faster_http

        return getattr(faster_http, exception_name)


class TestExceptions:
    """Test exception class hierarchy and behavior."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    def test_exception_hierarchy(self):
        """Test exception class hierarchy matches httpx."""
        # TDD: Red phase - this will fail initially
        import faster_http

        # Test base exception
        assert issubclass(faster_http.HTTPError, Exception)

        # Test request errors
        assert issubclass(faster_http.RequestError, faster_http.HTTPError)
        assert issubclass(faster_http.ConnectError, faster_http.RequestError)
        assert issubclass(faster_http.TimeoutException, faster_http.RequestError)

        # Test transport errors
        assert issubclass(faster_http.TransportError, faster_http.RequestError)
        assert issubclass(faster_http.ProtocolError, faster_http.TransportError)

        # Test status errors
        assert issubclass(faster_http.HTTPStatusError, faster_http.HTTPError)

    @httpx_compatibility_test
    def test_connect_error(self, client_factory):
        """Test ConnectError is raised for connection failures."""
        # TDD: Red phase - this will fail initially

        expected_exception = get_exception_class(client_factory, "ConnectError")

        # Use localhost with a closed port for reliable connection refused error
        with pytest.raises(expected_exception):
            client_factory.get("http://127.0.0.1:9999", timeout=2.0)  # Port 9999 should be closed

    @httpx_compatibility_test
    def test_timeout_error(self, client_factory):
        """Test TimeoutException is raised for timeouts."""
        # TDD: Red phase - this will fail initially

        expected_exception = get_exception_class(client_factory, "TimeoutException")

        with pytest.raises(expected_exception):
            client_factory.get(f"{self.base_url}/delay/10", timeout=0.1)

    @httpx_compatibility_test
    def test_http_status_error(self, client_factory):
        """Test HTTPStatusError is raised for error status codes."""
        # TDD: Red phase - this will fail initially

        expected_exception = get_exception_class(client_factory, "HTTPStatusError")

        response = client_factory.get(f"{self.base_url}/status/404")
        with pytest.raises(expected_exception):
            response.raise_for_status()

    @httpx_compatibility_test
    def test_invalid_url_error(self, client_factory):
        """Test InvalidURL is raised for malformed URLs."""
        # TDD: Red phase - this will fail initially

        expected_exception = get_exception_class(client_factory, "InvalidURL")

        with pytest.raises(expected_exception):
            client_factory.get("not-a-valid-url")

    @httpx_compatibility_test
    def test_too_many_redirects_error(self, client_factory):
        """Test TooManyRedirects is raised for redirect loops."""
        # TDD: Red phase - this will fail initially

        expected_exception = get_exception_class(client_factory, "TooManyRedirects")

        # Use more redirects to exceed both httpx and faster_http limits
        with pytest.raises(expected_exception):
            client_factory.get(f"{self.base_url}/redirect/50", follow_redirects=True)

    def test_exception_attributes(self):
        """Test exception attributes match httpx."""
        # TDD: Red phase - this will fail initially
        import faster_http

        # Test HTTPStatusError attributes
        response = faster_http.Response()  # Mock response
        error = faster_http.HTTPStatusError("Test error", request=None, response=response)
        assert error.response == response

        # Test RequestError attributes
        request = faster_http.Request("GET", "http://localhost:8080/test")
        error = faster_http.RequestError("Test error", request=request)
        assert error.request == request
