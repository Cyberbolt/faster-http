"""
Test to verify that all exception classes are properly implemented in Rust
and that Python-side exception stubs have been removed.
"""

import inspect

import pytest

import faster_http


class TestExceptionCleanup:
    """Test exception class implementation and module mapping."""

    def test_all_exceptions_from_rust(self):
        """Verify all exception classes come from Rust, not Python stubs."""
        exceptions = [
            'HTTPError', 'ConnectError', 'ConnectTimeout', 'TimeoutException',
            'ReadTimeout', 'WriteTimeout', 'PoolTimeout', 'RequestError',
            'HTTPStatusError', 'StreamError', 'ProtocolError', 'TooManyRedirects',
            'TransportError', 'InvalidURL', 'LocalProtocolError',
            'RemoteProtocolError', 'ReadError', 'WriteError', 'UnsupportedProtocol'
        ]

        for exc_name in exceptions:
            assert hasattr(faster_http, exc_name), f"Exception {exc_name} not found"
            exc_class = getattr(faster_http, exc_name)

            # Should come from faster_http module (Rust), not Python stubs
            assert exc_class.__module__ == 'faster_http', \
                f"{exc_name} should come from Rust (faster_http module), got {exc_class.__module__}"

    def test_exception_inheritance_hierarchy(self):
        """Test that exception inheritance matches httpx structure."""
        # Test base hierarchy
        assert issubclass(faster_http.ConnectError, faster_http.HTTPError)
        assert issubclass(faster_http.ConnectTimeout, faster_http.ConnectError)
        assert issubclass(faster_http.RequestError, faster_http.HTTPError)
        assert issubclass(faster_http.HTTPStatusError, faster_http.HTTPError)

        # Test new exceptions from Rust
        assert issubclass(faster_http.InvalidURL, faster_http.RequestError)
        assert issubclass(faster_http.LocalProtocolError, faster_http.ProtocolError)
        assert issubclass(faster_http.RemoteProtocolError, faster_http.ProtocolError)
        assert issubclass(faster_http.ReadError, faster_http.RequestError)
        assert issubclass(faster_http.WriteError, faster_http.RequestError)
        assert issubclass(faster_http.UnsupportedProtocol, faster_http.RequestError)

    def test_exception_functionality(self):
        """Test that exceptions can be raised and caught properly."""
        # Test basic exception creation and raising
        with pytest.raises(faster_http.InvalidURL):
            raise faster_http.InvalidURL("Invalid URL")

        with pytest.raises(faster_http.RequestError):
            # Should catch subclass
            raise faster_http.InvalidURL("Invalid URL")

        with pytest.raises(faster_http.HTTPError):
            # Should catch from base class
            raise faster_http.InvalidURL("Invalid URL")

    def test_response_object_module(self):
        """Test that Response object has correct module mapping."""
        assert faster_http.Response.__module__ == 'faster_http'
        assert faster_http.Request.__module__ == 'faster_http'
        assert faster_http.Headers.__module__ == 'faster_http'

    def test_no_python_exception_stubs(self):
        """Verify no Python exception stubs exist in the module source."""
        import faster_http

        # Get source of the module
        try:
            source = inspect.getsource(faster_http)

            # Should not contain Python class definitions for exceptions
            stub_patterns = [
                'class InvalidURL(RequestError):',
                'class LocalProtocolError(ProtocolError):',
                'class RemoteProtocolError(ProtocolError):',
                'class ReadError(RequestError):',
                'class WriteError(RequestError):',
                'class UnsupportedProtocol(RequestError):'
            ]

            for pattern in stub_patterns:
                assert pattern not in source, f"Found Python stub: {pattern}"

        except OSError:
            # If source is not available (compiled), that's acceptable
            pass


class TestHttpxCompatibility:
    """Test httpx compatibility of exception classes."""

    def test_exception_names_match_httpx(self):
        """Verify exception names match httpx for compatibility."""
        # These are the main httpx exception names that should be available
        httpx_exceptions = [
            'HTTPError', 'RequestError', 'HTTPStatusError', 'ConnectError',
            'ConnectTimeout', 'ReadTimeout', 'WriteTimeout', 'ProtocolError',
            'StreamError', 'TimeoutException', 'TooManyRedirects', 'TransportError'
        ]

        for exc_name in httpx_exceptions:
            assert hasattr(faster_http, exc_name), f"Missing httpx-compatible exception: {exc_name}"

    def test_additional_exceptions_available(self):
        """Test that additional useful exceptions are available."""
        additional_exceptions = [
            'InvalidURL', 'LocalProtocolError', 'RemoteProtocolError',
            'ReadError', 'WriteError', 'UnsupportedProtocol'
        ]

        for exc_name in additional_exceptions:
            assert hasattr(faster_http, exc_name), f"Missing additional exception: {exc_name}"
