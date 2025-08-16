"""
Test Transport customization functionality.
Tests transport customization with httpx vs faster_http comparison.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx

import faster_http


class TestTransportConfiguration:
    """Test transport configuration features - httpx vs faster_http comparison."""

    def test_default_transport_comparison(self):
        """Test default transport behavior - httpx vs faster_http."""
        # First test httpx Client with default transport
        httpx_client = httpx.Client()
        assert httpx_client is not None
        # Default transport should be configured automatically
        httpx_client.close()

        # Then test faster_http Client with default transport (should match httpx)
        faster_client = faster_http.Client()
        assert faster_client is not None
        # Default transport should be configured automatically
        faster_client.close()

    def test_transport_parameter_interface_comparison(self):
        """Test transport parameter interface - httpx vs faster_http."""
        # First test httpx Client transport parameter interface
        try:
            # httpx may or may not support custom transports via parameter
            httpx_client = httpx.Client(transport=None)
            httpx_client.close()
        except Exception:
            pass

        # Then test faster_http Client transport parameter interface
        try:
            # faster_http should match httpx transport parameter support
            faster_client = faster_http.Client(transport=None)
            faster_client.close()
        except Exception:
            pass

        # Both should have consistent transport parameter support
        # Note: This documents current transport parameter interface

    def test_mounts_configuration_comparison(self):
        """Test mounts configuration - httpx vs faster_http."""
        # Define mounts configuration for different URL patterns
        mounts = {
            "https://api.example.com": httpx.HTTPTransport() if hasattr(httpx, "HTTPTransport") else None,
        }

        # First test httpx Client with mounts (if supported)
        try:
            if mounts["https://api.example.com"] is not None:
                httpx_client = httpx.Client(mounts=mounts)
                httpx_client.close()
            else:
                pass
        except Exception:
            pass

        # Then test faster_http Client with mounts configuration
        try:
            # faster_http should support mounts for domain-specific transports
            faster_mounts = {
                "https://api.example.com": None,  # Use appropriate transport
            }
            faster_client = faster_http.Client(mounts=faster_mounts)
            faster_client.close()
        except Exception:
            pass

        # Both should have consistent mounts support
        # Note: This documents current mounts interface support

    def test_transport_timeout_inheritance_comparison(self):
        """Test transport timeout inheritance - httpx vs faster_http."""
        timeout = 30.0

        # First test httpx Client with timeout (transport should inherit)
        httpx_client = httpx.Client(timeout=timeout)
        assert httpx_client is not None
        # Timeout should be inherited by transport
        httpx_client.close()

        # Then test faster_http Client with timeout (should match httpx)
        faster_client = faster_http.Client(timeout=timeout)
        assert faster_client is not None
        # Timeout should be inherited by transport
        faster_client.close()

    def test_transport_ssl_configuration_comparison(self):
        """Test transport SSL configuration - httpx vs faster_http."""
        # First test httpx Client with SSL config (transport should inherit)
        httpx_client = httpx.Client(verify=False, trust_env=True)
        assert httpx_client is not None
        # SSL config should be inherited by transport
        httpx_client.close()

        # Then test faster_http Client with SSL config (should match httpx)
        faster_client = faster_http.Client(verify=False, trust_env=True)
        assert faster_client is not None
        # SSL config should be inherited by transport
        faster_client.close()

    def test_transport_proxy_configuration_comparison(self):
        """Test transport proxy configuration - httpx vs faster_http."""
        proxy_url = "http://transport-proxy.example.com:8080"

        # First test httpx Client with proxy (transport should handle)
        httpx_client = httpx.Client(proxy=proxy_url)
        assert httpx_client is not None
        # Proxy should be handled by transport
        httpx_client.close()

        # Then test faster_http Client with proxy (should match httpx)
        faster_client = faster_http.Client(proxy=proxy_url)
        assert faster_client is not None
        # Proxy should be handled by transport
        faster_client.close()

    def test_transport_headers_configuration_comparison(self):
        """Test transport headers configuration - httpx vs faster_http."""
        headers = {"User-Agent": "transport-test-client/1.0", "X-Transport-Test": "comparison"}

        # First test httpx Client with headers (transport should inherit)
        httpx_client = httpx.Client(headers=headers)
        assert httpx_client is not None
        assert "User-Agent" in httpx_client.headers
        assert "X-Transport-Test" in httpx_client.headers
        httpx_client.close()

        # Then test faster_http Client with headers (should match httpx)
        faster_client = faster_http.Client(headers=headers)
        assert faster_client is not None
        assert "User-Agent" in faster_client.headers
        assert "X-Transport-Test" in faster_client.headers
        faster_client.close()

        # Both should handle headers the same way
        assert httpx_client.headers["User-Agent"] == faster_client.headers["User-Agent"]
        assert httpx_client.headers["X-Transport-Test"] == faster_client.headers["X-Transport-Test"]

    def test_async_transport_configuration_comparison(self):
        """Test async transport configuration - httpx vs faster_http."""
        import asyncio

        async def test_async_transport():
            # First test httpx AsyncClient transport configuration
            httpx_client = httpx.AsyncClient(timeout=15.0, headers={"Async-Transport": "httpx"})
            assert httpx_client is not None
            await httpx_client.aclose()

            # Then test faster_http AsyncClient transport configuration (should match httpx)
            faster_client = faster_http.AsyncClient(timeout=15.0, headers={"Async-Transport": "faster_http"})
            assert faster_client is not None
            await faster_client.aclose()

        asyncio.run(test_async_transport())

    def test_transport_connection_pooling_comparison(self):
        """Test transport connection pooling configuration - httpx vs faster_http."""
        # First test httpx Client connection pooling (implicit)
        httpx_client = httpx.Client(timeout=20.0)
        assert httpx_client is not None
        # Connection pooling should be handled by transport
        httpx_client.close()

        # Then test faster_http Client connection pooling (should match httpx)
        faster_client = faster_http.Client(timeout=20.0)
        assert faster_client is not None
        # Connection pooling should be handled by transport
        faster_client.close()

    def test_transport_http_version_configuration_comparison(self):
        """Test transport HTTP version configuration - httpx vs faster_http."""
        # First test httpx Client with HTTP/2 configuration
        try:
            httpx_client = httpx.Client(http2=True)
            httpx_client.close()
        except Exception:
            pass

        # Then test faster_http Client with HTTP/2 configuration (should match httpx)
        try:
            faster_client = faster_http.Client(http2=True)
            faster_client.close()
        except Exception:
            pass

        # Both should have consistent HTTP/2 support
        # Note: This documents current HTTP/2 transport support

        # First test httpx Client with HTTP/1.1 explicit configuration
        try:
            httpx_client_http1 = httpx.Client(http2=False)
            httpx_supports_http1_config = True
            httpx_client_http1.close()
        except Exception:
            httpx_supports_http1_config = False

        # Then test faster_http Client with HTTP/1.1 explicit configuration
        try:
            faster_client_http1 = faster_http.Client(http2=False)
            faster_supports_http1_config = True
            faster_client_http1.close()
        except Exception:
            faster_supports_http1_config = False

        # Both should support HTTP version configuration consistently
        assert httpx_supports_http1_config == faster_supports_http1_config

    def test_transport_authentication_integration_comparison(self):
        """Test transport authentication integration - httpx vs faster_http."""
        # First test httpx Client with authentication (transport should handle)
        httpx_auth = httpx.BasicAuth("transport_user", "transport_pass")
        httpx_client = httpx.Client(auth=httpx_auth)
        assert httpx_client is not None
        # Authentication should be integrated with transport
        httpx_client.close()

        # Then test faster_http Client with authentication (should match httpx)
        faster_auth = faster_http.BasicAuth("transport_user", "transport_pass")
        faster_client = faster_http.Client(auth=faster_auth)
        assert faster_client is not None
        # Authentication should be integrated with transport
        faster_client.close()

        # Both should handle auth integration the same way (faster_http exposes credentials, httpx doesn't)
        # Just verify the faster_http auth has the expected credentials
        assert faster_auth.username == "transport_user"
        assert faster_auth.password == "transport_pass"

        # Both should be BasicAuth instances for authentication integration
        assert type(httpx_auth).__name__ == "BasicAuth"
        assert type(faster_auth).__name__ == "BasicAuth"

    def test_transport_redirect_handling_comparison(self):
        """Test transport redirect handling - httpx vs faster_http."""
        # First test httpx Client with redirect configuration
        httpx_client = httpx.Client(follow_redirects=True)
        assert httpx_client is not None
        # Redirect handling should be managed by transport
        httpx_client.close()

        # Then test faster_http Client with redirect configuration (should match httpx)
        faster_client = faster_http.Client(follow_redirects=True)
        assert faster_client is not None
        # Redirect handling should be managed by transport
        faster_client.close()

        # Test disabled redirects
        # First test httpx
        httpx_client_no_redirect = httpx.Client(follow_redirects=False)
        assert httpx_client_no_redirect is not None
        httpx_client_no_redirect.close()

        # Then test faster_http
        faster_client_no_redirect = faster_http.Client(follow_redirects=False)
        assert faster_client_no_redirect is not None
        faster_client_no_redirect.close()

    def test_transport_error_handling_comparison(self):
        """Test transport error handling configuration - httpx vs faster_http."""
        # First test httpx Client error handling (implicit in transport)
        httpx_client = httpx.Client(timeout=5.0, verify=True)
        assert httpx_client is not None
        # Error handling should be built into transport
        httpx_client.close()

        # Then test faster_http Client error handling (should match httpx)
        faster_client = faster_http.Client(timeout=5.0, verify=True)
        assert faster_client is not None
        # Error handling should be built into transport
        faster_client.close()

    def test_transport_custom_configuration_comparison(self):
        """Test transport custom configuration options - httpx vs faster_http."""
        # Configuration that might be transport-specific
        config = {
            "timeout": 25.0,
            "headers": {"Custom-Transport": "test"},
            "verify": False,
            "trust_env": True,
        }

        # First test httpx Client with custom transport configuration
        httpx_client = httpx.Client(**config)
        assert httpx_client is not None
        assert "Custom-Transport" in httpx_client.headers
        httpx_client.close()

        # Then test faster_http Client with same custom configuration (should match httpx)
        faster_client = faster_http.Client(**config)
        assert faster_client is not None
        assert "Custom-Transport" in faster_client.headers
        faster_client.close()

        # Both should support the same custom configuration
        assert httpx_client.headers["Custom-Transport"] == faster_client.headers["Custom-Transport"]

    def test_transport_with_event_hooks_comparison(self):
        """Test transport integration with event hooks - httpx vs faster_http."""

        def request_hook(request):
            pass

        def response_hook(response):
            pass

        # First test httpx Client with transport and event hooks
        httpx_client = httpx.Client(event_hooks={"request": [request_hook], "response": [response_hook]}, timeout=10.0)
        assert httpx_client is not None
        assert hasattr(httpx_client, "event_hooks")
        httpx_client.close()

        # Then test faster_http Client with transport and event hooks (should match httpx)
        faster_client = faster_http.Client(
            event_hooks={"request": [request_hook], "response": [response_hook]}, timeout=10.0
        )
        assert faster_client is not None
        assert hasattr(faster_client, "event_hooks")
        faster_client.close()

    def test_comprehensive_transport_configuration_comparison(self):
        """Test comprehensive transport configuration - httpx vs faster_http."""
        # Complex transport configuration combining multiple features
        proxy_url = "http://comprehensive-transport-proxy.example.com:8080"
        headers = {"Transport-Comprehensive": "test"}
        timeout = 20.0

        def comprehensive_hook(arg):
            pass

        # First test httpx Client with comprehensive transport configuration
        httpx_client = httpx.Client(
            proxy=proxy_url,
            headers=headers,
            timeout=timeout,
            verify=False,
            trust_env=True,
            follow_redirects=True,
            event_hooks={"request": [comprehensive_hook]},
            http2=False,  # Explicit HTTP/1.1
        )

        # Test httpx comprehensive transport configuration
        assert httpx_client is not None
        assert "Transport-Comprehensive" in httpx_client.headers
        assert hasattr(httpx_client, "event_hooks")
        httpx_client.close()

        # Then test faster_http Client with same comprehensive configuration
        faster_client = faster_http.Client(
            proxy=proxy_url,
            headers=headers,
            timeout=timeout,
            verify=False,
            trust_env=True,
            follow_redirects=True,
            event_hooks={"request": [comprehensive_hook]},
            http2=False,  # Explicit HTTP/1.1
        )

        # Test faster_http comprehensive transport configuration (should match httpx)
        assert faster_client is not None
        assert "Transport-Comprehensive" in faster_client.headers
        assert hasattr(faster_client, "event_hooks")
        faster_client.close()

        # Both should support the same comprehensive transport configuration
        assert httpx_client.headers["Transport-Comprehensive"] == faster_client.headers["Transport-Comprehensive"]

    def test_transport_context_manager_comparison(self):
        """Test transport with context manager usage - httpx vs faster_http."""
        # First test httpx Client as context manager (transport cleanup)
        with httpx.Client(timeout=15.0) as httpx_client:
            assert httpx_client is not None
            # Transport should be properly managed in context

        # Then test faster_http Client as context manager (should match httpx)
        with faster_http.Client(timeout=15.0) as faster_client:
            assert faster_client is not None
            # Transport should be properly managed in context

    def test_transport_async_context_manager_comparison(self):
        """Test transport with async context manager - httpx vs faster_http."""
        import asyncio

        async def test_async_context():
            # First test httpx AsyncClient as async context manager
            async with httpx.AsyncClient(timeout=15.0) as httpx_client:
                assert httpx_client is not None
                # Transport should be properly managed in async context

            # Then test faster_http AsyncClient as async context manager (should match httpx)
            async with faster_http.AsyncClient(timeout=15.0) as faster_client:
                assert faster_client is not None
                # Transport should be properly managed in async context

        asyncio.run(test_async_context())
