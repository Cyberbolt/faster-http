"""Tests for configuration classes."""

from tests.utils.httpx_comparison import httpx_compatibility_test


class TestConfig:
    """Test configuration classes."""

    @httpx_compatibility_test
    def test_timeout_creation(self, client_factory):
        """Test Timeout configuration."""
        # TDD: Red phase - this will fail initially
        import faster_http

        timeout = faster_http.Timeout(5.0)
        assert timeout is not None

    @httpx_compatibility_test
    def test_timeout_with_individual_values(self, client_factory):
        """Test Timeout with individual timeout values."""
        # TDD: Red phase - this will fail initially
        import faster_http

        timeout = faster_http.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
        assert timeout is not None

    @httpx_compatibility_test
    def test_limits_creation(self, client_factory):
        """Test Limits configuration."""
        # TDD: Red phase - this will fail initially
        import faster_http

        limits = faster_http.Limits(max_keepalive_connections=10, max_connections=100)
        assert limits is not None

    @httpx_compatibility_test
    def test_client_with_timeout_config(self, client_factory):
        """Test client with timeout configuration."""
        # TDD: Red phase - this will fail initially
        import faster_http

        timeout = faster_http.Timeout(5.0)
        client = client_factory(timeout=timeout)
        assert client is not None

    @httpx_compatibility_test
    def test_client_with_limits_config(self, client_factory):
        """Test client with limits configuration."""
        # TDD: Red phase - this will fail initially
        import faster_http

        limits = faster_http.Limits(max_connections=50)
        client = client_factory(limits=limits)
        assert client is not None

    @httpx_compatibility_test
    def test_proxy_creation(self, client_factory):
        """Test Proxy configuration."""
        # TDD: Red phase - this will fail initially
        import faster_http

        proxy = faster_http.Proxy("http://localhost:8888")
        assert proxy is not None

    @httpx_compatibility_test
    def test_proxy_with_auth(self, client_factory):
        """Test Proxy with authentication."""
        # TDD: Red phase - this will fail initially
        import faster_http

        proxy = faster_http.Proxy("http://localhost:8888", auth=("username", "password"))
        assert proxy is not None
