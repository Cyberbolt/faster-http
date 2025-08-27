"""Comprehensive tests for Timeout and Limits configuration classes."""

import httpx
import pytest

import faster_http
from tests.utils.httpx_comparison import httpx_compatibility_test


class TestTimeout:
    """Test Timeout configuration class."""

    def test_timeout_with_numeric_value(self):
        """Test creating timeout with a numeric value."""
        timeout = faster_http.Timeout(timeout=5.0)
        assert timeout.connect == 5.0
        assert timeout.read == 5.0
        assert timeout.write == 5.0
        assert timeout.pool == 5.0

        # Test string representation
        assert repr(timeout) == "Timeout(timeout=5.0)"

    def test_timeout_with_none_value(self):
        """Test creating timeout with None (infinite timeout)."""
        timeout = faster_http.Timeout(timeout=None)
        assert timeout.connect is None
        assert timeout.read is None
        assert timeout.write is None
        assert timeout.pool is None

        # Test string representation
        assert repr(timeout) == "Timeout(timeout=None)"

    def test_timeout_with_individual_parameters(self):
        """Test creating timeout with individual parameters."""
        timeout = faster_http.Timeout(connect=10.0, read=30.0, write=20.0, pool=15.0)
        assert timeout.connect == 10.0
        assert timeout.read == 30.0
        assert timeout.write == 20.0
        assert timeout.pool == 15.0

        # Test string representation
        assert repr(timeout) == "Timeout(connect=10.0, read=30.0, write=20.0, pool=15.0)"

    def test_timeout_no_parameters_raises_error(self):
        """Test that creating timeout with no parameters raises error."""
        with pytest.raises(Exception) as exc_info:
            faster_http.Timeout()
        assert "must either include a default, or set all four parameters explicitly" in str(exc_info.value)

    def test_timeout_partial_parameters_raises_error(self):
        """Test that creating timeout with partial parameters raises error."""
        with pytest.raises(Exception) as exc_info:
            faster_http.Timeout(connect=5.0)
        assert "must either include a default, or set all four parameters explicitly" in str(exc_info.value)

        with pytest.raises(Exception) as exc_info:
            faster_http.Timeout(connect=5.0, read=10.0)
        assert "must either include a default, or set all four parameters explicitly" in str(exc_info.value)

    def test_timeout_equality(self):
        """Test timeout equality comparison."""
        t1 = faster_http.Timeout(timeout=5.0)
        t2 = faster_http.Timeout(timeout=5.0)
        t3 = faster_http.Timeout(timeout=10.0)
        t4 = faster_http.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)

        assert t1 == t2
        assert t1 != t3
        assert t1 == t4  # Same values, different construction
        assert t1 != "string"
        assert t1 != 5.0

    def test_timeout_none_equality(self):
        """Test timeout with None values equality."""
        tn1 = faster_http.Timeout(timeout=None)
        tn2 = faster_http.Timeout(timeout=None)
        t1 = faster_http.Timeout(timeout=5.0)

        assert tn1 == tn2
        assert tn1 != t1

    @httpx_compatibility_test
    def test_timeout_httpx_compatibility(self, client_factory):
        """Test timeout compatibility with httpx."""
        # Test basic timeout
        httpx_timeout = httpx.Timeout(timeout=5.0)
        faster_timeout = faster_http.Timeout(timeout=5.0)

        assert repr(httpx_timeout) == repr(faster_timeout)
        assert httpx_timeout.connect == faster_timeout.connect
        assert httpx_timeout.read == faster_timeout.read

        # Test None timeout
        httpx_none = httpx.Timeout(timeout=None)
        faster_none = faster_http.Timeout(timeout=None)

        assert repr(httpx_none) == repr(faster_none)
        assert httpx_none.connect == faster_none.connect

        # Test individual parameters
        httpx_all = httpx.Timeout(connect=10.0, read=30.0, write=20.0, pool=15.0)
        faster_all = faster_http.Timeout(connect=10.0, read=30.0, write=20.0, pool=15.0)

        assert repr(httpx_all) == repr(faster_all)


class TestLimits:
    """Test Limits configuration class."""

    def test_limits_default_values(self):
        """Test creating limits with default values."""
        limits = faster_http.Limits()
        assert limits.max_connections is None
        assert limits.max_keepalive_connections is None
        assert limits.keepalive_expiry == 5.0

        # Test string representation
        assert repr(limits) == "Limits(max_connections=None, max_keepalive_connections=None, keepalive_expiry=5.0)"

    def test_limits_with_custom_values(self):
        """Test creating limits with custom values."""
        limits = faster_http.Limits(max_connections=50, max_keepalive_connections=10, keepalive_expiry=20.0)
        assert limits.max_connections == 50
        assert limits.max_keepalive_connections == 10
        assert limits.keepalive_expiry == 20.0

        # Test string representation
        assert repr(limits) == "Limits(max_connections=50, max_keepalive_connections=10, keepalive_expiry=20.0)"

    def test_limits_with_partial_values(self):
        """Test creating limits with some custom values."""
        limits = faster_http.Limits(max_connections=100)
        assert limits.max_connections == 100
        assert limits.max_keepalive_connections is None  # Default
        assert limits.keepalive_expiry == 5.0  # Default

        limits2 = faster_http.Limits(max_keepalive_connections=25, keepalive_expiry=10.0)
        assert limits2.max_connections is None  # Default
        assert limits2.max_keepalive_connections == 25
        assert limits2.keepalive_expiry == 10.0

    def test_limits_equality(self):
        """Test limits equality comparison."""
        l1 = faster_http.Limits()
        l2 = faster_http.Limits()
        l3 = faster_http.Limits(max_connections=50)
        l4 = faster_http.Limits(max_connections=50, max_keepalive_connections=None, keepalive_expiry=5.0)

        assert l1 == l2
        assert l1 != l3
        assert l3 == l4  # Same values
        assert l1 != "string"
        assert l1 != 100

    @httpx_compatibility_test
    def test_limits_httpx_compatibility(self, client_factory):
        """Test limits compatibility with httpx."""
        # Test default limits
        httpx_limits = httpx.Limits()
        faster_limits = faster_http.Limits()

        assert repr(httpx_limits) == repr(faster_limits)
        assert httpx_limits.max_connections == faster_limits.max_connections
        assert httpx_limits.max_keepalive_connections == faster_limits.max_keepalive_connections
        assert httpx_limits.keepalive_expiry == faster_limits.keepalive_expiry

        # Test custom limits
        httpx_custom = httpx.Limits(max_connections=50, max_keepalive_connections=10, keepalive_expiry=20.0)
        faster_custom = faster_http.Limits(max_connections=50, max_keepalive_connections=10, keepalive_expiry=20.0)

        assert repr(httpx_custom) == repr(faster_custom)
        assert httpx_custom.max_connections == faster_custom.max_connections


class TestClientIntegration:
    """Test Client integration with Timeout and Limits."""

    @httpx_compatibility_test
    def test_client_with_timeout_object(self, client_factory):
        """Test creating client with Timeout object."""
        timeout = faster_http.Timeout(timeout=10.0)
        client = client_factory(timeout=timeout)
        assert client is not None

    @httpx_compatibility_test
    def test_client_with_limits_object(self, client_factory):
        """Test creating client with Limits object."""
        limits = faster_http.Limits(max_connections=50, max_keepalive_connections=20)
        client = client_factory(limits=limits)
        assert client is not None

    @httpx_compatibility_test
    def test_client_with_both_timeout_and_limits(self, client_factory):
        """Test creating client with both timeout and limits."""
        timeout = faster_http.Timeout(timeout=15.0)
        limits = faster_http.Limits(max_connections=100)
        client = client_factory(timeout=timeout, limits=limits)
        assert client is not None

    @httpx_compatibility_test
    def test_client_with_numeric_timeout(self, client_factory):
        """Test creating client with numeric timeout (backward compatibility)."""
        client = client_factory(timeout=30.0)
        assert client is not None

    @httpx_compatibility_test
    def test_client_with_none_timeout(self, client_factory):
        """Test creating client with None timeout."""
        timeout = faster_http.Timeout(timeout=None)
        client = client_factory(timeout=timeout)
        assert client is not None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_timeout_with_zero_values(self):
        """Test timeout with zero values."""
        timeout = faster_http.Timeout(timeout=0.0)
        assert timeout.connect == 0.0
        assert timeout.read == 0.0
        assert timeout.write == 0.0
        assert timeout.pool == 0.0

    def test_timeout_with_very_large_values(self):
        """Test timeout with very large values."""
        timeout = faster_http.Timeout(timeout=999999.0)
        assert timeout.connect == 999999.0
        assert timeout.read == 999999.0

    def test_limits_with_zero_values(self):
        """Test limits with zero values."""
        limits = faster_http.Limits(max_connections=0, max_keepalive_connections=0, keepalive_expiry=0.0)
        assert limits.max_connections == 0
        assert limits.max_keepalive_connections == 0
        assert limits.keepalive_expiry == 0.0

    def test_timeout_mixed_none_and_values(self):
        """Test timeout with mixed None and numeric values."""
        # This should work - some parameters can be None when specified individually
        timeout = faster_http.Timeout(connect=None, read=10.0, write=None, pool=5.0)
        assert timeout.connect is None
        assert timeout.read == 10.0
        assert timeout.write is None
        assert timeout.pool == 5.0


if __name__ == "__main__":
    pytest.main([__file__])

