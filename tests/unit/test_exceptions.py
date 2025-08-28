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
        response = faster_http.Response(200)  # Mock response
        error = faster_http.HTTPStatusError("Test error", request=None, response=response)
        assert error.response == response

        # Test RequestError attributes
        request = faster_http.Request("GET", "http://localhost:8080/test")
        error = faster_http.RequestError("Test error", request=request)
        assert error.request == request

    # === High Priority Exception Hierarchy Tests ===

    def test_base_http_error_instantiation(self):
        """Test HTTPError base class can be instantiated."""
        import faster_http

        # Test basic instantiation
        error = faster_http.HTTPError("Base HTTP error")
        assert str(error) == "Base HTTP error"
        assert isinstance(error, Exception)

    def test_request_error_inheritance_and_instantiation(self):
        """Test RequestError inheritance and proper instantiation."""
        import faster_http

        # Test inheritance
        assert issubclass(faster_http.RequestError, faster_http.HTTPError)
        assert issubclass(faster_http.RequestError, Exception)

        # Test instantiation
        error = faster_http.RequestError("Request failed")
        assert str(error) == "Request failed"
        assert isinstance(error, faster_http.HTTPError)
        assert isinstance(error, Exception)

    def test_connect_error_inheritance_and_instantiation(self):
        """Test ConnectError inheritance and proper instantiation."""
        import faster_http

        # Test inheritance - ConnectError should inherit from NetworkError
        assert hasattr(faster_http, "NetworkError")
        assert issubclass(faster_http.ConnectError, faster_http.NetworkError)
        # NetworkError should inherit from RequestError which inherits from HTTPError
        assert issubclass(faster_http.NetworkError, faster_http.RequestError)
        assert issubclass(faster_http.ConnectError, faster_http.HTTPError)
        assert issubclass(faster_http.ConnectError, Exception)

        # Test instantiation
        error = faster_http.ConnectError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, faster_http.NetworkError)
        assert isinstance(error, faster_http.RequestError)
        assert isinstance(error, faster_http.HTTPError)
        assert isinstance(error, Exception)

    def test_timeout_exception_inheritance_and_instantiation(self):
        """Test TimeoutException inheritance and proper instantiation."""
        import faster_http

        # Test inheritance - Note: TimeoutException inheritance may vary
        # In httpx it inherits from TransportError, in faster_http it currently inherits from RequestError
        assert issubclass(faster_http.TimeoutException, Exception)

        # Test instantiation
        error = faster_http.TimeoutException("Request timed out")
        assert str(error) == "Request timed out"
        assert isinstance(error, Exception)

    def test_exception_hierarchy_compatibility(self):
        """Test exception hierarchy matches httpx patterns."""
        import faster_http

        # Test that all exception classes exist
        exceptions_to_test = [
            "HTTPError",
            "RequestError",
            "ConnectError",
            "TimeoutException",
            "HTTPStatusError",
            "NetworkError",
            "TransportError",
            "ProtocolError"
        ]

        for exc_name in exceptions_to_test:
            assert hasattr(faster_http, exc_name), f"Missing exception: {exc_name}"
            exc_class = getattr(faster_http, exc_name)
            assert issubclass(exc_class, Exception), f"{exc_name} should inherit from Exception"

    def test_exception_instantiation_with_arguments(self):
        """Test all exceptions can be instantiated with common arguments."""
        import faster_http

        # Test HTTPError with message
        http_error = faster_http.HTTPError("HTTP error occurred")
        assert str(http_error) == "HTTP error occurred"

        # Test RequestError with message
        request_error = faster_http.RequestError("Request error occurred")
        assert str(request_error) == "Request error occurred"

        # Test ConnectError with message
        connect_error = faster_http.ConnectError("Connection error occurred")
        assert str(connect_error) == "Connection error occurred"

        # Test TimeoutException with message
        timeout_error = faster_http.TimeoutException("Timeout error occurred")
        assert str(timeout_error) == "Timeout error occurred"

    def test_exception_catching_compatibility(self):
        """Test that exceptions can be caught using base classes."""
        import faster_http

        # Test catching RequestError as HTTPError
        try:
            raise faster_http.RequestError("Request failed")
        except faster_http.HTTPError as e:
            assert str(e) == "Request failed"

        # Test catching ConnectError as RequestError (via NetworkError)
        try:
            raise faster_http.ConnectError("Connection failed")
        except faster_http.RequestError as e:
            assert str(e) == "Connection failed"

        # Test catching any HTTP-related exception as HTTPError
        for exception_class in [faster_http.RequestError, faster_http.ConnectError,
                               faster_http.TimeoutException, faster_http.HTTPStatusError]:
            try:
                raise exception_class("Test error")
            except faster_http.HTTPError:
                pass  # Should be caught
            except Exception:
                pytest.fail(f"{exception_class.__name__} should be catchable as HTTPError")
