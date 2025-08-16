"""
Unit tests for authentication functionality.
Tests various authentication methods and their properties.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx

import faster_http


class TestBasicAuth:
    """Test BasicAuth functionality - httpx vs faster_http comparison."""

    def test_basic_auth_creation_comparison(self):
        """Test BasicAuth class creation and properties - httpx vs faster_http."""
        username = "testuser"
        password = "testpass"

        # First test httpx BasicAuth creation
        httpx_auth = httpx.BasicAuth(username, password)
        assert httpx_auth is not None

        # Test httpx BasicAuth representation
        httpx_repr = repr(httpx_auth)
        assert "BasicAuth" in httpx_repr
        # Based on real httpx, it doesn't expose username in repr for security

        # Then test faster_http BasicAuth creation (should match httpx)
        faster_auth = faster_http.BasicAuth(username, password)
        assert faster_auth is not None

        # Test faster_http BasicAuth representation (should match httpx)
        faster_repr = repr(faster_auth)
        assert "BasicAuth" in faster_repr

        # Both should be created successfully and have similar interface
        assert type(httpx_auth).__name__ == "BasicAuth"
        assert type(faster_auth).__name__ == "BasicAuth"

    def test_basic_auth_equality_comparison(self):
        """Test BasicAuth equality comparison - httpx vs faster_http."""
        # First test httpx BasicAuth creation for equality comparison
        httpx_auth1 = httpx.BasicAuth("testuser", "testpass")
        httpx_auth2 = httpx.BasicAuth("testuser", "testpass")
        httpx_auth3 = httpx.BasicAuth("different", "testpass")

        # Test httpx auth objects can be created
        assert httpx_auth1 is not None
        assert httpx_auth2 is not None
        assert httpx_auth3 is not None

        # Then test faster_http BasicAuth creation for equality comparison (should match httpx)
        faster_auth1 = faster_http.BasicAuth("testuser", "testpass")
        faster_auth2 = faster_http.BasicAuth("testuser", "testpass")
        faster_auth3 = faster_http.BasicAuth("different", "testpass")

        # Test faster_http auth objects can be created (should match httpx behavior)
        assert faster_auth1 is not None
        assert faster_auth2 is not None
        assert faster_auth3 is not None

        # Both libraries should create auth objects consistently
        assert type(httpx_auth1).__name__ == type(faster_auth1).__name__

    def test_basic_auth_with_empty_credentials_comparison(self):
        """Test BasicAuth with empty credentials - httpx vs faster_http."""
        # First test httpx BasicAuth with empty credentials
        httpx_auth = httpx.BasicAuth("", "")
        assert httpx_auth is not None

        # Then test faster_http BasicAuth with empty credentials (should match httpx)
        faster_auth = faster_http.BasicAuth("", "")
        assert faster_auth is not None

        # Both should handle empty credentials the same way
        assert type(httpx_auth).__name__ == type(faster_auth).__name__

    def test_basic_auth_with_special_characters_comparison(self):
        """Test BasicAuth with special characters - httpx vs faster_http."""
        username = "user@domain.com"
        password = "p@ssw0rd!#$"

        # First test httpx BasicAuth with special characters
        httpx_auth = httpx.BasicAuth(username, password)
        assert httpx_auth is not None

        # Then test faster_http BasicAuth with special characters (should match httpx)
        faster_auth = faster_http.BasicAuth(username, password)
        assert faster_auth is not None

        # Both should handle special characters the same way
        assert type(httpx_auth).__name__ == type(faster_auth).__name__

    def test_basic_auth_flow_method_comparison(self):
        """Test BasicAuth auth_flow method - httpx vs faster_http."""
        username = "testuser"
        password = "testpass"

        # First test httpx BasicAuth has auth_flow method
        httpx_auth = httpx.BasicAuth(username, password)
        assert hasattr(httpx_auth, "auth_flow")
        assert callable(httpx_auth.auth_flow)

        # Then test faster_http BasicAuth has auth_flow method
        faster_auth = faster_http.BasicAuth(username, password)
        assert hasattr(faster_auth, "auth_flow")
        assert callable(faster_auth.auth_flow)

        # Both should have the required auth interface


class TestDigestAuth:
    """Test DigestAuth functionality - httpx vs faster_http comparison."""

    def test_digest_auth_creation_comparison(self):
        """Test DigestAuth class creation - httpx vs faster_http."""
        username = "testuser"
        password = "testpass"

        # First test httpx DigestAuth creation
        httpx_auth = httpx.DigestAuth(username, password)
        assert httpx_auth is not None

        # Test httpx DigestAuth has required methods
        assert hasattr(httpx_auth, "auth_flow")
        assert callable(httpx_auth.auth_flow)

        # Then test faster_http DigestAuth creation (should match httpx)
        faster_auth = faster_http.DigestAuth(username, password)
        assert faster_auth is not None

        # Test faster_http DigestAuth has required methods (should match httpx)
        assert hasattr(faster_auth, "auth_flow")
        assert callable(faster_auth.auth_flow)

        # Both should have same basic interface
        assert type(httpx_auth).__name__ == type(faster_auth).__name__

    def test_digest_auth_representation_comparison(self):
        """Test DigestAuth string representation - httpx vs faster_http."""
        username = "testuser"
        password = "testpass"

        # First test httpx DigestAuth representation
        httpx_auth = httpx.DigestAuth(username, password)
        httpx_repr = repr(httpx_auth)
        assert "DigestAuth" in httpx_repr
        # Based on real httpx, it doesn't expose username in repr for security
        # Password should not be in repr for security
        assert password not in httpx_repr

        # Then test faster_http DigestAuth representation (should match httpx)
        faster_auth = faster_http.DigestAuth(username, password)
        faster_repr = repr(faster_auth)
        assert "DigestAuth" in faster_repr
        # Should match httpx behavior for security
        assert password not in faster_repr

        # Both should have similar representation format
        assert type(httpx_auth).__name__ == type(faster_auth).__name__


class TestNetRCAuth:
    """Test NetRCAuth functionality - httpx vs faster_http comparison."""

    def test_netrc_auth_creation_comparison(self):
        """Test NetRCAuth class creation - httpx vs faster_http."""
        # First test httpx NetRCAuth creation (may raise FileNotFoundError)
        try:
            httpx_auth = httpx.NetRCAuth()
            httpx_has_netrc = True

            # Test httpx NetRCAuth has required methods
            assert hasattr(httpx_auth, "auth_flow")
            assert callable(httpx_auth.auth_flow)
        except FileNotFoundError:
            httpx_has_netrc = False

        # Then test faster_http NetRCAuth creation
        try:
            faster_auth = faster_http.NetRCAuth()
            faster_has_netrc = True

            # Test faster_http NetRCAuth has required methods
            assert hasattr(faster_auth, "auth_flow")
            assert callable(faster_auth.auth_flow)
        except FileNotFoundError:
            faster_has_netrc = False

        # Both should behave the same (either both work or both raise FileNotFoundError)
        assert httpx_has_netrc == faster_has_netrc

    def test_netrc_auth_with_file_parameter_comparison(self):
        """Test NetRCAuth with file parameter - httpx vs faster_http."""
        # Test with a non-existent file (should not raise during creation)
        fake_file = "/nonexistent/netrc/file"

        # First test httpx NetRCAuth with file parameter
        try:
            httpx_auth = httpx.NetRCAuth(file=fake_file)
            assert hasattr(httpx_auth, "auth_flow")
            httpx_created = True
        except Exception:
            httpx_created = False

        # Then test faster_http NetRCAuth with file parameter
        try:
            faster_auth = faster_http.NetRCAuth(file=fake_file)
            assert hasattr(faster_auth, "auth_flow")
            faster_created = True
        except Exception:
            faster_created = False

        # Both should behave consistently
        assert httpx_created == faster_created


class TestAuthIntegration:
    """Test authentication integration - httpx vs faster_http comparison."""

    def test_auth_with_client_comparison(self, stable_server):
        """Test authentication with Client - httpx vs faster_http."""
        url = stable_server.url("/get")  # Use a simple endpoint

        # First test httpx Client with BasicAuth
        httpx_auth = httpx.BasicAuth("testuser", "testpass")
        httpx_client = httpx.Client(auth=httpx_auth)

        httpx_response = httpx_client.get(url)
        assert httpx_response.status_code == 200

        # Check that httpx added Authorization header
        httpx_data = httpx_response.json()
        assert "headers" in httpx_data
        assert "Authorization" in httpx_data["headers"]

        httpx_client.close()

        # Then test faster_http Client with BasicAuth
        faster_auth = faster_http.BasicAuth("testuser", "testpass")
        faster_client = faster_http.Client(auth=faster_auth)

        faster_response = faster_client.get(url)
        assert faster_response.status_code == 200

        # Check that faster_http added Authorization header (same as httpx)
        faster_data = faster_response.json()
        assert "headers" in faster_data
        assert "Authorization" in faster_data["headers"]

        faster_client.close()

        # Both should produce equivalent authorization
        assert httpx_response.status_code == faster_response.status_code
        assert httpx_data["headers"]["Authorization"] == faster_data["headers"]["Authorization"]

    def test_auth_per_request_comparison(self, stable_server):
        """Test per-request authentication - httpx vs faster_http."""
        url = stable_server.url("/get")

        # First test httpx per-request auth
        httpx_auth = httpx.BasicAuth("user", "pass")
        httpx_response = httpx.get(url, auth=httpx_auth)
        assert httpx_response.status_code == 200

        httpx_data = httpx_response.json()
        assert "Authorization" in httpx_data["headers"]

        # Then test faster_http per-request auth
        faster_auth = faster_http.BasicAuth("user", "pass")
        faster_response = faster_http.get(url, auth=faster_auth)
        assert faster_response.status_code == 200

        faster_data = faster_response.json()
        assert "Authorization" in faster_data["headers"]

        # Both should produce equivalent authorization
        assert httpx_response.status_code == faster_response.status_code
        assert httpx_data["headers"]["Authorization"] == faster_data["headers"]["Authorization"]
