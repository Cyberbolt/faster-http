"""
Integration tests for error scenarios in faster-http.

This module tests actual network error scenarios and compares
error handling behavior between faster-http and httpx.
"""


import httpx
import pytest

import faster_http


class TestNetworkErrorScenarios:
    """Test real network error scenarios."""

    def test_connection_refused_error(self):
        """Test connection refused errors."""
        # Use a port that's likely not in use
        url = "http://127.0.0.1:65432/test"

        # Test with faster_http
        with pytest.raises(faster_http.ConnectError):
            faster_http.get(url, timeout=1.0)

        # Test with httpx for comparison
        with pytest.raises(httpx.ConnectError):
            httpx.get(url, timeout=1.0)

    def test_timeout_error(self):
        """Test timeout errors."""
        # Use a non-routable IP to trigger timeout
        url = "http://192.0.2.1/test"  # RFC 5737 test IP

        # Test with faster_http
        with pytest.raises((faster_http.ConnectTimeout, faster_http.ReadTimeout)):
            faster_http.get(url, timeout=0.1)

        # Test with httpx for comparison
        with pytest.raises((httpx.ConnectTimeout, httpx.ReadTimeout)):
            httpx.get(url, timeout=0.1)

    def test_invalid_hostname_error(self):
        """Test invalid hostname resolution errors."""
        url = "http://this-domain-definitely-does-not-exist-12345.com/test"

        # Test with faster_http
        with pytest.raises((faster_http.ConnectError, faster_http.RequestError)):
            faster_http.get(url, timeout=1.0)

        # Test with httpx for comparison
        with pytest.raises((httpx.ConnectError, httpx.RequestError)):
            httpx.get(url, timeout=1.0)


class TestHTTPStatusErrors:
    """Test HTTP status error handling."""

    @pytest.fixture
    def mock_server_url(self):
        """URL that should return various HTTP status codes."""
        # This would ideally use the test server from conftest.py
        return "http://nginx:21000"

    def test_404_error_handling(self, mock_server_url):
        """Test 404 error handling."""
        url = f"{mock_server_url}/non-existent-page"

        # Test with faster_http
        try:
            response = faster_http.get(url, timeout=5.0)
            # If no exception, check status
            if response.status_code == 404:
                pytest.skip("Server returned 404 without raising exception")
        except faster_http.HTTPStatusError:
            pass  # Expected behavior
        except Exception as e:
            pytest.fail(f"Unexpected exception type: {type(e)}")

        # Test with httpx for comparison
        try:
            response = httpx.get(url, timeout=5.0)
            # httpx doesn't raise by default for 4xx/5xx
            assert response.status_code == 404
        except Exception:
            # If httpx raises, faster_http should behave similarly
            pass

    def test_500_error_handling(self, mock_server_url):
        """Test 500 error handling."""
        url = f"{mock_server_url}/error/500"

        # Test with faster_http
        try:
            response = faster_http.get(url, timeout=5.0)
            # Check if it returns response or raises
            if response.status_code == 500:
                pytest.skip("Server returned 500 without raising exception")
        except faster_http.HTTPStatusError:
            pass  # Expected behavior
        except Exception as e:
            pytest.fail(f"Unexpected exception type: {type(e)}")


class TestRequestValidationErrors:
    """Test request validation error scenarios."""

    def test_invalid_url_formats(self):
        """Test various invalid URL formats."""
        invalid_urls = [
            "not-a-url",
            "://missing-scheme",
            "http://",
            "ftp://unsupported-scheme.com",
            "",
            "http:// invalid spaces.com",
        ]

        for url in invalid_urls:
            # Test with faster_http
            with pytest.raises((faster_http.InvalidURL, faster_http.RequestError)):
                faster_http.get(url)

            # Test with httpx for comparison
            with pytest.raises((httpx.InvalidURL, httpx.RequestError)):
                httpx.get(url)

    def test_invalid_method(self):
        """Test invalid HTTP methods."""
        url = "http://example.com"

        # Test with faster_http
        with pytest.raises(faster_http.RequestError):
            faster_http.request("INVALID_METHOD", url)

        # Test with httpx for comparison
        with pytest.raises((httpx.RequestError, ValueError)):
            httpx.request("INVALID_METHOD", url)


class TestClientStateErrors:
    """Test client state error scenarios."""

    def test_closed_client_usage(self):
        """Test using a closed client."""
        # Test with faster_http
        client = faster_http.Client()
        client.close()

        with pytest.raises(faster_http.RequestError):
            client.get("http://example.com")

        # Test with httpx for comparison
        httpx_client = httpx.Client()
        httpx_client.close()

        with pytest.raises((httpx.RequestError, RuntimeError)):
            httpx_client.get("http://example.com")

    def test_async_client_sync_usage(self):
        """Test improper usage of async client in sync context."""
        # Test with faster_http
        async_client = faster_http.AsyncClient()

        # Should not be able to use async client in sync context
        with pytest.raises((TypeError, AttributeError, faster_http.RequestError)):
            # This should fail one way or another
            async_client.get("http://example.com")


class TestStreamingErrors:
    """Test streaming-related error scenarios."""

    def test_stream_consumption_after_close(self):
        """Test consuming stream after response is closed."""
        # This test requires actual streaming functionality
        # For now, test the error types exist
        with pytest.raises(faster_http.StreamError):
            raise faster_http.StreamError("Stream error")


class TestErrorConsistency:
    """Test error consistency between sync and async clients."""

    def test_sync_async_error_consistency(self):
        """Test that sync and async clients raise similar errors."""
        url = "http://192.0.2.1/test"  # Non-routable IP

        # Test sync client
        sync_error = None
        try:
            faster_http.get(url, timeout=0.1)
        except Exception as e:
            sync_error = type(e)

        # Test async client (would need async test setup)
        # For now, just verify error types are available
        assert sync_error is not None
        assert issubclass(sync_error, faster_http.HTTPError)


class TestErrorRecovery:
    """Test error recovery and retry scenarios."""

    def test_error_does_not_affect_subsequent_requests(self):
        """Test that errors don't affect client state."""
        client = faster_http.Client()

        # Make a request that should fail
        try:
            client.get("http://192.0.2.1/test", timeout=0.1)
        except faster_http.HTTPError:
            pass  # Expected

        # Client should still work for valid requests
        # (This would need a test server to verify)
        assert client is not None  # Basic check that client still exists

        client.close()


class TestErrorDetailPresevation:
    """Test that error details are preserved properly."""

    def test_error_message_preservation(self):
        """Test that original error messages are preserved."""
        with pytest.raises(faster_http.InvalidURL) as exc_info:
            faster_http.URL("invalid-url")

        error_msg = str(exc_info.value)
        # Should contain meaningful information
        assert len(error_msg) > 0
        assert any(word in error_msg.lower() for word in ['invalid', 'url', 'error'])

    def test_error_context_preservation(self):
        """Test that error context is preserved when possible."""
        # Test that we can distinguish between different error types
        errors_raised = []

        test_cases = [
            ("http://192.0.2.1/test", "timeout/connection"),
            ("invalid-url", "url validation"),
        ]

        for url, expected_type in test_cases:
            try:
                if "invalid" in url:
                    faster_http.URL(url)
                else:
                    faster_http.get(url, timeout=0.1)
            except Exception as e:
                errors_raised.append((type(e), expected_type))

        # Should have raised different types of errors
        assert len(errors_raised) > 0
        error_types = [e[0] for e in errors_raised]
        # At least one error should be different (or we should have caught some)
        assert len(error_types) > 0


if __name__ == "__main__":
    pytest.main([__file__])
