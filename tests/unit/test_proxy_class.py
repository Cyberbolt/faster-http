"""
Unit tests for Proxy class functionality.
Tests proxy class constructor and properties.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx

import faster_http


class TestProxyClass:
    """Test Proxy class functionality - httpx vs faster_http comparison."""

    def test_proxy_class_availability_comparison(self):
        """Test that Proxy class can be imported - httpx vs faster_http."""
        # First test httpx Proxy class availability
        assert hasattr(httpx, "Proxy"), "httpx should have Proxy class"
        assert httpx.Proxy is not None

        # Then test faster_http Proxy class availability (should match httpx)
        assert hasattr(faster_http, "Proxy"), "faster_http should have Proxy class like httpx"
        assert faster_http.Proxy is not None

    def test_basic_proxy_creation_comparison(self):
        """Test basic proxy creation - httpx vs faster_http."""
        proxy_url = "http://proxy.example.com:8080"

        # First test httpx Proxy creation
        httpx_proxy = httpx.Proxy(proxy_url)
        assert httpx_proxy is not None

        # Test httpx proxy properties
        assert hasattr(httpx_proxy, "url"), "httpx Proxy should have url property"

        # Then test faster_http Proxy creation (should match httpx interface)
        faster_proxy = faster_http.Proxy(proxy_url)
        assert faster_proxy is not None

        # Test faster_http proxy properties (should match httpx)
        assert hasattr(faster_proxy, "url"), "faster_http Proxy should have url property like httpx"

        # Both should have similar string representation of URL
        assert str(httpx_proxy.url) == str(faster_proxy.url)

    def test_proxy_with_auth_comparison(self):
        """Test proxy creation with authentication - httpx vs faster_http."""
        proxy_url = "http://proxy.example.com:8080"
        auth = ("username", "password")

        # First test httpx Proxy with auth
        try:
            httpx_proxy = httpx.Proxy(proxy_url, auth=auth)
            httpx_supports_auth = True
            httpx_auth = httpx_proxy.auth if hasattr(httpx_proxy, "auth") else None
        except Exception:
            httpx_supports_auth = False
            httpx_auth = None

        # Then test faster_http Proxy with auth (should match httpx support)
        try:
            faster_proxy = faster_http.Proxy(proxy_url, auth=auth)
            faster_supports_auth = True
            faster_auth = faster_proxy.auth if hasattr(faster_proxy, "auth") else None
        except Exception:
            faster_supports_auth = False
            faster_auth = None

        # Both should handle auth consistently
        assert httpx_supports_auth == faster_supports_auth, "Auth support should be consistent"
        if httpx_supports_auth and faster_supports_auth:
            assert httpx_auth == faster_auth, "Auth values should match"

    def test_proxy_with_headers_comparison(self):
        """Test proxy creation with custom headers - httpx vs faster_http."""
        proxy_url = "http://proxy.example.com:8080"
        headers = {"User-Agent": "test-proxy-client", "X-Custom": "value"}

        # First test httpx Proxy with headers
        try:
            httpx_proxy = httpx.Proxy(proxy_url, headers=headers)
            httpx_supports_headers = True
            httpx_headers = httpx_proxy.headers if hasattr(httpx_proxy, "headers") else None
        except Exception:
            httpx_supports_headers = False
            httpx_headers = None

        # Then test faster_http Proxy with headers (should match httpx support)
        try:
            faster_proxy = faster_http.Proxy(proxy_url, headers=headers)
            faster_supports_headers = True
            faster_headers = faster_proxy.headers if hasattr(faster_proxy, "headers") else None
        except Exception:
            faster_supports_headers = False
            faster_headers = None

        # Both should handle headers consistently
        assert httpx_supports_headers == faster_supports_headers, "Headers support should be consistent"
        if httpx_supports_headers and faster_supports_headers and httpx_headers and faster_headers:
            # Check that both have the same header values
            for key, _value in headers.items():
                if key in httpx_headers and key in faster_headers:
                    assert httpx_headers[key] == faster_headers[key], f"Header {key} should match"

    def test_proxy_with_ssl_context_comparison(self):
        """Test proxy creation with SSL context - httpx vs faster_http."""
        import ssl

        proxy_url = "https://secure-proxy.example.com:8080"
        ssl_context = ssl.create_default_context()

        # First test httpx Proxy with SSL context
        try:
            httpx_proxy = httpx.Proxy(proxy_url, ssl_context=ssl_context)
            httpx_supports_ssl = True
            httpx_ssl = httpx_proxy.ssl_context if hasattr(httpx_proxy, "ssl_context") else None
        except Exception:
            httpx_supports_ssl = False
            httpx_ssl = None

        # Then test faster_http Proxy with SSL context (should match httpx support)
        try:
            faster_proxy = faster_http.Proxy(proxy_url, ssl_context=ssl_context)
            faster_supports_ssl = True
            faster_ssl = faster_proxy.ssl_context if hasattr(faster_proxy, "ssl_context") else None
        except Exception:
            faster_supports_ssl = False
            faster_ssl = None

        # Both should handle SSL context consistently
        assert httpx_supports_ssl == faster_supports_ssl, "SSL context support should be consistent"
        if httpx_supports_ssl and faster_supports_ssl:
            assert httpx_ssl is faster_ssl, "SSL context should be the same object"

    def test_proxy_url_property_comparison(self):
        """Test proxy URL property - httpx vs faster_http."""
        proxy_url = "http://proxy.example.com:8080"

        # First test httpx Proxy URL property
        httpx_proxy = httpx.Proxy(proxy_url)
        httpx_url = httpx_proxy.url

        # Test httpx URL properties
        assert httpx_url is not None
        assert str(httpx_url) == proxy_url

        # Then test faster_http Proxy URL property (should match httpx)
        faster_proxy = faster_http.Proxy(proxy_url)
        faster_url = faster_proxy.url

        # Test faster_http URL properties (should match httpx)
        assert faster_url is not None
        assert str(faster_url) == proxy_url

        # Both should have identical URL representation
        assert str(httpx_url) == str(faster_url)

    def test_proxy_representation_comparison(self):
        """Test proxy string representation - httpx vs faster_http."""
        proxy_url = "http://proxy.example.com:8080"

        # First test httpx Proxy representation
        httpx_proxy = httpx.Proxy(proxy_url)
        httpx_repr = repr(httpx_proxy)
        httpx_str = str(httpx_proxy)

        # httpx representation should contain meaningful information
        assert len(httpx_repr) > 0
        assert len(httpx_str) > 0

        # Then test faster_http Proxy representation (should be similar to httpx)
        faster_proxy = faster_http.Proxy(proxy_url)
        faster_repr = repr(faster_proxy)
        faster_str = str(faster_proxy)

        # faster_http representation should also contain meaningful information
        assert len(faster_repr) > 0
        assert len(faster_str) > 0

        # Both should provide informative representations
        # (exact format may differ, but both should be meaningful)

    def test_proxy_equality_comparison(self):
        """Test proxy equality comparison - httpx vs faster_http."""
        proxy_url1 = "http://proxy.example.com:8080"
        proxy_url2 = "http://other.example.com:8080"

        # First test httpx Proxy equality
        httpx_proxy1 = httpx.Proxy(proxy_url1)
        httpx_proxy2 = httpx.Proxy(proxy_url1)  # Same URL
        httpx_proxy3 = httpx.Proxy(proxy_url2)  # Different URL

        # Test httpx proxy equality behavior
        try:
            httpx_eq_same = httpx_proxy1 == httpx_proxy2
            httpx_eq_diff = httpx_proxy1 == httpx_proxy3
            httpx_supports_equality = True
        except Exception:
            httpx_supports_equality = False
            httpx_eq_same = None
            httpx_eq_diff = None

        # Then test faster_http Proxy equality (should match httpx behavior)
        faster_proxy1 = faster_http.Proxy(proxy_url1)
        faster_proxy2 = faster_http.Proxy(proxy_url1)  # Same URL
        faster_proxy3 = faster_http.Proxy(proxy_url2)  # Different URL

        # Test faster_http proxy equality behavior
        try:
            faster_eq_same = faster_proxy1 == faster_proxy2
            faster_eq_diff = faster_proxy1 == faster_proxy3
            faster_supports_equality = True
        except Exception:
            faster_supports_equality = False
            faster_eq_same = None
            faster_eq_diff = None

        # Both should handle equality consistently
        assert httpx_supports_equality == faster_supports_equality, "Equality support should be consistent"
        if httpx_supports_equality and faster_supports_equality:
            assert httpx_eq_same == faster_eq_same, "Same proxy equality should match"
            assert httpx_eq_diff == faster_eq_diff, "Different proxy equality should match"

    def test_proxy_with_complex_url_comparison(self):
        """Test proxy with complex URL - httpx vs faster_http."""
        complex_url = "https://user:pass@proxy.example.com:8443/path?param=value"

        # First test httpx Proxy with complex URL
        try:
            httpx_proxy = httpx.Proxy(complex_url)
            httpx_handles_complex = True
            httpx_url_str = str(httpx_proxy.url)
        except Exception:
            httpx_handles_complex = False
            httpx_url_str = None

        # Then test faster_http Proxy with complex URL (should match httpx behavior)
        try:
            faster_proxy = faster_http.Proxy(complex_url)
            faster_handles_complex = True
            faster_url_str = str(faster_proxy.url)
        except Exception:
            faster_handles_complex = False
            faster_url_str = None

        # Both should handle complex URLs consistently
        assert httpx_handles_complex == faster_handles_complex, "Complex URL support should be consistent"
        if httpx_handles_complex and faster_handles_complex:
            assert httpx_url_str == faster_url_str, "Complex URL should be parsed identically"

    def test_proxy_interface_consistency_comparison(self):
        """Test that faster_http Proxy doesn't have extra interfaces that httpx Proxy doesn't have."""
        proxy_url = "http://proxy.example.com:8080"

        # Create instances for interface comparison
        httpx_proxy = httpx.Proxy(proxy_url)
        faster_proxy = faster_http.Proxy(proxy_url)

        # Get all public attributes/methods from both
        httpx_attrs = {attr for attr in dir(httpx_proxy) if not attr.startswith("_")}
        faster_attrs = {attr for attr in dir(faster_proxy) if not attr.startswith("_")}

        # faster_http should not have attributes that httpx doesn't have
        extra_attrs = faster_attrs - httpx_attrs
        assert len(extra_attrs) == 0, (
            f"faster_http Proxy has extra attributes that httpx Proxy doesn't have: {extra_attrs}"
        )

        # Verify that faster_http has all essential httpx attributes
        essential_attrs = {"url"}  # Core attributes that both should have
        for attr in essential_attrs:
            if hasattr(httpx_proxy, attr):
                assert hasattr(faster_proxy, attr), f"faster_http Proxy missing essential httpx attribute: {attr}"

    def test_proxy_parameter_compatibility_comparison(self):
        """Test that Proxy constructor parameters are compatible - httpx vs faster_http."""
        proxy_url = "http://proxy.example.com:8080"

        # Test all possible parameter combinations that httpx supports
        test_cases = [
            # Basic URL only
            {"args": (proxy_url,), "kwargs": {}},
            # URL with auth (if supported)
            {"args": (proxy_url,), "kwargs": {"auth": ("user", "pass")}},
        ]

        for case in test_cases:
            args = case["args"]
            kwargs = case["kwargs"]

            # First test httpx Proxy with these parameters
            try:
                httpx.Proxy(*args, **kwargs)
                httpx_accepts = True
            except Exception:
                httpx_accepts = False

            # Then test faster_http Proxy with same parameters (should match httpx)
            try:
                faster_http.Proxy(*args, **kwargs)
                faster_accepts = True
            except Exception:
                faster_accepts = False

            # Both should handle the same parameter combinations
            assert httpx_accepts == faster_accepts, f"Parameter compatibility should match for {args}, {kwargs}"
