"""
Comprehensive integration tests for faster-http functionality.
Tests feature combinations and ensures httpx compatibility.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx

import faster_http


class TestComprehensiveIntegration:
    """Test comprehensive feature integration - httpx vs faster_http comparison."""

    def test_client_with_multiple_configurations_comparison(self):
        """Test Client with multiple configurations - httpx vs faster_http."""
        # Configuration for complex client setup
        base_url = "https://api.example.com"
        timeout = 30.0
        headers = {"User-Agent": "test-client/1.0", "Accept": "application/json"}
        params = {"api_version": "v1", "format": "json"}

        # First test httpx Client with multiple configurations
        httpx_client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            params=params,
            follow_redirects=True,
            verify=True,
            trust_env=True,
        )

        # Test httpx client properties
        assert str(httpx_client.base_url) == base_url
        assert "User-Agent" in httpx_client.headers
        assert "Accept" in httpx_client.headers
        assert httpx_client.params["api_version"] == "v1"
        assert httpx_client.params["format"] == "json"

        httpx_client.close()

        # Then test faster_http Client with same configurations
        faster_client = faster_http.Client(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            params=params,
            follow_redirects=True,
            verify=True,
            trust_env=True,
        )

        # Test faster_http client properties (should match httpx)
        assert faster_client.base_url == base_url
        assert "User-Agent" in faster_client.headers
        assert "Accept" in faster_client.headers
        assert faster_client.params["api_version"] == "v1"
        assert faster_client.params["format"] == "json"

        faster_client.close()

        # Both should have compatible configurations
        assert str(httpx_client.base_url) == faster_client.base_url
        assert httpx_client.params["api_version"] == faster_client.params["api_version"]

    def test_async_client_with_multiple_configurations_comparison(self):
        """Test AsyncClient with multiple configurations - httpx vs faster_http."""
        base_url = "https://api.example.com"
        timeout = 15.0
        headers = {"Authorization": "Bearer token123", "Content-Type": "application/json"}

        # First test httpx AsyncClient with multiple configurations
        httpx_client = httpx.AsyncClient(base_url=base_url, timeout=timeout, headers=headers, verify=True, http2=True)

        # Test httpx async client properties
        assert str(httpx_client.base_url) == base_url
        assert "Authorization" in httpx_client.headers
        assert "Content-Type" in httpx_client.headers

        # Then test faster_http AsyncClient with same configurations
        faster_client = faster_http.AsyncClient(
            base_url=base_url, timeout=timeout, headers=headers, verify=True, http2=True
        )

        # Test faster_http async client properties (should match httpx)
        assert faster_client.base_url == base_url
        assert "Authorization" in faster_client.headers
        assert "Content-Type" in faster_client.headers

        # Both should have compatible configurations
        assert str(httpx_client.base_url) == faster_client.base_url

    def test_ssl_configuration_comparison(self):
        """Test SSL configuration options - httpx vs faster_http."""
        # First test httpx Client with SSL configuration
        httpx_client = httpx.Client(
            verify=True,
            cert=None,  # No client certificate
            trust_env=True,
        )

        # Test httpx SSL configuration attributes
        assert hasattr(httpx_client, "_transport") or hasattr(httpx_client, "transport")

        httpx_client.close()

        # Then test faster_http Client with same SSL configuration
        faster_client = faster_http.Client(
            verify=True,
            cert=None,  # No client certificate
            trust_env=True,
        )

        # Test faster_http SSL configuration (should work like httpx)
        assert faster_client is not None

        faster_client.close()

    def test_event_hooks_with_multiple_clients_comparison(self):
        """Test event hooks with different client types - httpx vs faster_http."""
        hook_calls = {"httpx": 0, "faster": 0}

        def httpx_request_hook(request):
            hook_calls["httpx"] += 1

        def faster_request_hook(request):
            hook_calls["faster"] += 1

        # First test httpx Client with event hooks
        httpx_client = httpx.Client(event_hooks={"request": [httpx_request_hook]})

        # Test httpx event hooks configuration
        assert httpx_client is not None
        assert hasattr(httpx_client, "event_hooks")
        assert "request" in httpx_client.event_hooks

        httpx_client.close()

        # Then test faster_http Client with event hooks
        faster_client = faster_http.Client(event_hooks={"request": [faster_request_hook]})

        # Test faster_http event hooks configuration (should match httpx)
        assert faster_client is not None
        assert hasattr(faster_client, "event_hooks")
        assert "request" in faster_client.event_hooks

        faster_client.close()

    def test_complex_configuration_integration_comparison(self):
        """Test complex configuration with multiple features - httpx vs faster_http."""
        base_url = "https://api.example.com"
        timeout = 30.0
        headers = {"User-Agent": "integration-test/1.0"}

        def request_hook(request):
            pass

        def response_hook(response):
            pass

        # First test httpx Client with complex configuration
        httpx_client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            follow_redirects=True,
            verify=True,
            trust_env=True,
            event_hooks={"request": [request_hook], "response": [response_hook]},
        )

        # Test httpx complex configuration
        assert str(httpx_client.base_url) == base_url
        assert "User-Agent" in httpx_client.headers
        assert hasattr(httpx_client, "event_hooks")

        httpx_client.close()

        # Then test faster_http Client with same complex configuration
        faster_client = faster_http.Client(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            follow_redirects=True,
            verify=True,
            trust_env=True,
            event_hooks={"request": [request_hook], "response": [response_hook]},
        )

        # Test faster_http complex configuration (should match httpx)
        assert faster_client.base_url == base_url
        assert "User-Agent" in faster_client.headers
        assert hasattr(faster_client, "event_hooks")

        faster_client.close()

        # Both should have compatible complex configurations
        assert str(httpx_client.base_url) == faster_client.base_url

    def test_error_handling_consistency_comparison(self):
        """Test error handling consistency - httpx vs faster_http."""
        # Test invalid timeout values

        # First test httpx error handling for invalid timeout
        try:
            httpx_client = httpx.Client(timeout=-1.0)
            httpx_accepts_negative = True
        except (ValueError, TypeError):
            httpx_accepts_negative = False

        # Then test faster_http error handling for invalid timeout
        try:
            faster_client = faster_http.Client(timeout=-1.0)
            faster_accepts_negative = True
        except (ValueError, TypeError):
            faster_accepts_negative = False

        # Both should handle invalid timeout the same way
        assert httpx_accepts_negative == faster_accepts_negative

        # Test valid configuration (should work for both)
        httpx_client = httpx.Client(base_url="https://example.com")
        assert httpx_client is not None
        httpx_client.close()

        faster_client = faster_http.Client(base_url="https://example.com")
        assert faster_client is not None
        faster_client.close()

    def test_authentication_integration_comparison(self):
        """Test authentication integration with client configurations - httpx vs faster_http."""
        username = "testuser"
        password = "testpass"

        # First test httpx Client with authentication
        httpx_auth = httpx.BasicAuth(username, password)
        httpx_client = httpx.Client(auth=httpx_auth, timeout=10.0, verify=True)

        # Test httpx client with auth
        assert httpx_client is not None
        assert hasattr(httpx_client, "auth") or hasattr(httpx_client, "_auth")

        httpx_client.close()

        # Then test faster_http Client with same authentication
        faster_auth = faster_http.BasicAuth(username, password)
        faster_client = faster_http.Client(auth=faster_auth, timeout=10.0, verify=True)

        # Test faster_http client with auth (should match httpx)
        assert faster_client is not None

        faster_client.close()

        # Both auth objects should work for authentication
        # (faster_http has username/password, httpx doesn't expose them)
        # Just verify the faster_http auth has the expected credentials since it exposes them
        assert faster_auth.username == username
        assert faster_auth.password == password

        # Both should be BasicAuth instances
        assert type(httpx_auth).__name__ == "BasicAuth"
        assert type(faster_auth).__name__ == "BasicAuth"

    def test_comprehensive_httpx_compatibility_comparison(self):
        """Test comprehensive httpx compatibility across all features - httpx vs faster_http."""
        # Configuration test cases for compatibility
        test_configs = [
            # Basic configuration
            {
                "name": "basic_config",
                "config": {
                    "timeout": 10.0,
                    "headers": {"User-Agent": "test-client"},
                    "follow_redirects": False,
                },
            },
            # SSL configuration
            {
                "name": "ssl_config",
                "config": {
                    "verify": True,
                    "trust_env": True,
                },
            },
            # Authentication configuration
            {
                "name": "auth_config",
                "config": {
                    "auth": httpx.BasicAuth("user", "pass"),
                },
            },
        ]

        for test_case in test_configs:
            config = test_case["config"]

            # First test httpx Client with configuration
            httpx_client = httpx.Client(**config)
            assert httpx_client is not None
            httpx_client.close()

            # Then test faster_http Client with same configuration
            # Convert httpx.BasicAuth to faster_http.BasicAuth if needed
            if "auth" in config and isinstance(config["auth"], httpx.BasicAuth):
                # httpx.BasicAuth doesn't expose username/password, so use the known values
                config["auth"] = faster_http.BasicAuth("user", "pass")

            faster_client = faster_http.Client(**config)
            assert faster_client is not None
            faster_client.close()

            # Both should create successfully with same configuration

    def test_async_comprehensive_integration_comparison(self):
        """Test async comprehensive integration - httpx vs faster_http."""
        base_url = "https://async-api.example.com"
        timeout = 15.0
        headers = {"Content-Type": "application/json"}

        # First test httpx AsyncClient comprehensive configuration
        httpx_client = httpx.AsyncClient(base_url=base_url, timeout=timeout, headers=headers, verify=True, http2=True)

        # Test httpx async client comprehensive properties
        assert str(httpx_client.base_url) == base_url
        assert "Content-Type" in httpx_client.headers

        # Then test faster_http AsyncClient comprehensive configuration
        faster_client = faster_http.AsyncClient(
            base_url=base_url, timeout=timeout, headers=headers, verify=True, http2=True
        )

        # Test faster_http async client comprehensive properties (should match httpx)
        assert faster_client.base_url == base_url
        assert "Content-Type" in faster_client.headers

        # Both should have compatible comprehensive configurations
        assert str(httpx_client.base_url) == faster_client.base_url

    def test_timeout_configuration_comprehensive_comparison(self):
        """Test comprehensive timeout configuration - httpx vs faster_http."""
        # Test various timeout configurations

        # First test httpx Timeout object creation
        httpx_timeout = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
        assert httpx_timeout.connect == 5.0
        assert httpx_timeout.read == 30.0

        # Test httpx Client with Timeout object
        httpx_client = httpx.Client(timeout=httpx_timeout)
        assert httpx_client is not None
        httpx_client.close()

        # Then test faster_http Timeout object creation
        faster_timeout = faster_http.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
        assert faster_timeout.connect == 5.0
        assert faster_timeout.read == 30.0

        # Test faster_http Client with Timeout object (should match httpx)
        faster_client = faster_http.Client(timeout=faster_timeout)
        assert faster_client is not None
        faster_client.close()

        # Both timeout objects should have same values
        assert httpx_timeout.connect == faster_timeout.connect
        assert httpx_timeout.read == faster_timeout.read

    def test_headers_and_params_comprehensive_comparison(self):
        """Test comprehensive headers and params handling - httpx vs faster_http."""
        headers = {
            "User-Agent": "comprehensive-test/1.0",
            "Accept": "application/json",
            "Authorization": "Bearer test-token",
        }
        params = {"version": "v1", "format": "json", "limit": "100"}

        # First test httpx Client with headers and params
        httpx_client = httpx.Client(headers=headers, params=params)

        # Test httpx headers and params
        for key, value in headers.items():
            assert httpx_client.headers[key] == value

        for key, value in params.items():
            assert httpx_client.params[key] == value

        httpx_client.close()

        # Then test faster_http Client with same headers and params
        faster_client = faster_http.Client(headers=headers, params=params)

        # Test faster_http headers and params (should match httpx)
        for key, value in headers.items():
            assert faster_client.headers[key] == value

        for key, value in params.items():
            assert faster_client.params[key] == value

        faster_client.close()

        # Both should handle headers and params identically
        for key in headers:
            assert httpx_client.headers[key] == faster_client.headers[key]

        for key in params:
            assert httpx_client.params[key] == faster_client.params[key]
