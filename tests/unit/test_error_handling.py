"""
Comprehensive error handling tests for faster-http.

This module tests that all error types are properly implemented
and that error handling is consistent across the codebase.
"""

import pytest
import faster_http
import httpx
from unittest.mock import Mock, patch


class TestErrorInheritance:
    """Test error class inheritance hierarchy."""
    
    def test_base_error_hierarchy(self):
        """Test that all errors inherit from HTTPError."""
        # Connection errors
        assert issubclass(faster_http.ConnectError, faster_http.HTTPError)
        assert issubclass(faster_http.ConnectTimeout, faster_http.ConnectError)
        
        # Timeout errors
        assert issubclass(faster_http.TimeoutException, faster_http.HTTPError)
        assert issubclass(faster_http.ReadTimeout, faster_http.TimeoutException)
        assert issubclass(faster_http.WriteTimeout, faster_http.TimeoutException)
        assert issubclass(faster_http.PoolTimeout, faster_http.TimeoutException)
        
        # Request errors
        assert issubclass(faster_http.RequestError, faster_http.HTTPError)
        assert issubclass(faster_http.InvalidURL, faster_http.RequestError)
        assert issubclass(faster_http.ReadError, faster_http.RequestError)
        assert issubclass(faster_http.WriteError, faster_http.RequestError)
        assert issubclass(faster_http.UnsupportedProtocol, faster_http.RequestError)
        
        # Protocol errors
        assert issubclass(faster_http.ProtocolError, faster_http.HTTPError)
        assert issubclass(faster_http.LocalProtocolError, faster_http.ProtocolError)
        assert issubclass(faster_http.RemoteProtocolError, faster_http.ProtocolError)
        assert issubclass(faster_http.TooManyRedirects, faster_http.ProtocolError)
        
        # Status and other errors
        assert issubclass(faster_http.HTTPStatusError, faster_http.HTTPError)
        assert issubclass(faster_http.StreamError, faster_http.HTTPError)
        assert issubclass(faster_http.TransportError, faster_http.HTTPError)
    
    def test_error_catching_hierarchy(self):
        """Test that errors can be caught by their parent classes."""
        with pytest.raises(faster_http.HTTPError):
            raise faster_http.ConnectError("Connection failed")
            
        with pytest.raises(faster_http.RequestError):
            raise faster_http.InvalidURL("Invalid URL")
            
        with pytest.raises(faster_http.ConnectError):
            raise faster_http.ConnectTimeout("Connection timeout")
            
        with pytest.raises(faster_http.ProtocolError):
            raise faster_http.TooManyRedirects("Too many redirects")


class TestURLErrors:
    """Test URL validation error handling."""
    
    def test_invalid_url_creation(self):
        """Test that invalid URLs raise InvalidURL."""
        with pytest.raises(faster_http.InvalidURL):
            faster_http.URL("not-a-valid-url")
        
        with pytest.raises(faster_http.InvalidURL):
            faster_http.URL("://missing-scheme")
        
        with pytest.raises(faster_http.InvalidURL):
            faster_http.URL("http://")
    
    def test_url_resolve_reference_success(self):
        """Test URL reference resolution works correctly."""
        url = faster_http.URL("http://example.com")
        
        # Test that valid references work
        result = url.resolve_reference("path/to/resource")
        assert str(result) == "http://example.com/path/to/resource"
        
        # Test absolute reference
        result = url.resolve_reference("http://other.com/path")
        assert str(result) == "http://other.com/path"


class TestModelErrors:
    """Test error handling in model classes."""
    
    def test_headers_key_error(self):
        """Test header access with invalid keys."""
        headers = faster_http.Headers()
        
        with pytest.raises(faster_http.RequestError):
            _ = headers["non-existent-header"]
    
    def test_query_params_key_error(self):
        """Test query parameter access with invalid keys."""
        params = faster_http.QueryParams()
        
        with pytest.raises(faster_http.RequestError):
            _ = params["non-existent-param"]
    
    def test_cookies_key_error(self):
        """Test cookie access with invalid keys."""
        cookies = faster_http.Cookies()
        
        with pytest.raises(faster_http.RequestError):
            _ = cookies["non-existent-cookie"]
    
    def test_timeout_validation_error(self):
        """Test timeout configuration validation."""
        with pytest.raises(faster_http.RequestError):
            # Should raise error when no default or explicit timeouts provided
            faster_http.Timeout()
    
    def test_netrc_file_not_found_error(self):
        """Test .netrc file not found errors."""
        with pytest.raises(faster_http.RequestError):
            faster_http.NetRCAuth("/non/existent/path/.netrc")
        
        with pytest.raises(faster_http.RequestError):
            # Should raise error when no .netrc file found
            faster_http.NetRCAuth()


class TestClientErrors:
    """Test client error handling."""
    
    def test_invalid_method_error(self):
        """Test invalid HTTP methods raise appropriate errors."""
        client = faster_http.Client()
        
        # Test with None method should raise TypeError
        with pytest.raises(TypeError):
            client.request(None, "http://example.com")
    
    def test_file_upload_sync_error(self):
        """Test that file uploads in sync mode raise appropriate error."""
        client = faster_http.Client()
        
        with pytest.raises(faster_http.RequestError) as exc_info:
            client.post("http://example.com", files={"file": "content"})
        
        assert "synchronous mode" in str(exc_info.value)
    
    def test_closed_client_error(self):
        """Test operations on closed client raise appropriate errors."""
        client = faster_http.Client()
        client.close()
        
        with pytest.raises(faster_http.RequestError):
            client.get("http://example.com")


class TestNetworkErrors:
    """Test network-related error handling."""
    
    def test_connection_error_simulation(self):
        """Test connection errors are properly mapped."""
        # Note: This would require actual network setup or mocking
        # For now, we test the error types exist and can be raised
        with pytest.raises(faster_http.ConnectError):
            raise faster_http.ConnectError("Connection failed")
    
    def test_timeout_error_simulation(self):
        """Test timeout errors are properly mapped."""
        with pytest.raises(faster_http.ReadTimeout):
            raise faster_http.ReadTimeout("Read timeout")
        
        with pytest.raises(faster_http.ConnectTimeout):
            raise faster_http.ConnectTimeout("Connect timeout")


class TestHttpxCompatibility:
    """Test compatibility with httpx error handling."""
    
    def test_error_name_compatibility(self):
        """Test that error names match httpx for compatibility."""
        # Core httpx errors should be available
        httpx_errors = [
            'HTTPError', 'RequestError', 'HTTPStatusError', 'ConnectError',
            'ConnectTimeout', 'ReadTimeout', 'WriteTimeout', 'ProtocolError',
            'StreamError', 'TimeoutException', 'TooManyRedirects', 'TransportError'
        ]
        
        for error_name in httpx_errors:
            assert hasattr(faster_http, error_name), f"Missing httpx-compatible error: {error_name}"
            assert hasattr(httpx, error_name), f"httpx doesn't have error: {error_name}"
    
    def test_error_inheritance_compatibility(self):
        """Test that our error inheritance matches httpx patterns."""
        # Test basic inheritance patterns that should match httpx
        assert issubclass(faster_http.HTTPStatusError, faster_http.HTTPError)
        assert issubclass(faster_http.ConnectError, faster_http.HTTPError)
        assert issubclass(faster_http.RequestError, faster_http.HTTPError)
        
        # Compare with httpx
        assert issubclass(httpx.HTTPStatusError, httpx.HTTPError)
        assert issubclass(httpx.ConnectError, httpx.HTTPError)
        assert issubclass(httpx.RequestError, httpx.HTTPError)


class TestErrorMessages:
    """Test error message formatting and content."""
    
    def test_error_message_clarity(self):
        """Test that error messages are clear and informative."""
        with pytest.raises(faster_http.InvalidURL) as exc_info:
            faster_http.URL("invalid-url")
        
        error_msg = str(exc_info.value)
        assert "Invalid URL" in error_msg or "invalid" in error_msg.lower()
    
    def test_error_message_consistency(self):
        """Test that similar errors have consistent message formatting."""
        # Test URL errors have consistent prefix
        with pytest.raises(faster_http.InvalidURL) as exc_info:
            faster_http.URL("://no-scheme")
        
        error_msg = str(exc_info.value)
        # Should contain some indication it's a URL error
        assert any(word in error_msg.lower() for word in ['url', 'invalid'])


class TestErrorCreationFunctions:
    """Test error creation utility functions (internal API)."""
    
    def test_exception_can_be_raised_and_caught(self):
        """Test that all exception types can be properly raised and caught."""
        exceptions_to_test = [
            faster_http.HTTPError,
            faster_http.ConnectError,
            faster_http.ConnectTimeout,
            faster_http.RequestError,
            faster_http.InvalidURL,
            faster_http.HTTPStatusError,
            faster_http.ProtocolError,
            faster_http.StreamError,
            faster_http.TransportError,
            faster_http.ReadTimeout,
            faster_http.WriteTimeout,
            faster_http.TimeoutException,
            faster_http.TooManyRedirects,
            faster_http.LocalProtocolError,
            faster_http.RemoteProtocolError,
            faster_http.ReadError,
            faster_http.WriteError,
            faster_http.UnsupportedProtocol,
        ]
        
        for exc_class in exceptions_to_test:
            # Test that each exception can be raised and caught
            with pytest.raises(exc_class):
                raise exc_class("Test error message")
            
            # Test that it can be caught by HTTPError
            with pytest.raises(faster_http.HTTPError):
                raise exc_class("Test error message")


class TestErrorContext:
    """Test error context and additional information."""
    
    def test_http_status_error_with_response(self):
        """Test HTTPStatusError includes response information when available."""
        # This would typically be tested with actual network requests
        # For now, test that the error type exists and can be instantiated
        try:
            raise faster_http.HTTPStatusError("HTTP 404 Error")
        except faster_http.HTTPStatusError as e:
            assert "404" in str(e) or "HTTP" in str(e)
    
    def test_error_repr_and_str(self):
        """Test error string representation."""
        error = faster_http.RequestError("Test error message")
        error_str = str(error)
        assert "Test error message" in error_str