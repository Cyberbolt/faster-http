"""Tests for authentication classes."""

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test


class TestAuth:
    """Test authentication functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_basic_auth_creation(self, client_factory):
        """Test BasicAuth can be created."""
        # TDD: Red phase - this will fail initially
        import faster_http

        auth = faster_http.BasicAuth("username", "password")
        assert auth is not None

    @httpx_compatibility_test
    def test_basic_auth_request(self, client_factory):
        """Test request with BasicAuth."""
        # TDD: Red phase - this will fail initially

        # Create appropriate auth object based on the client type
        if client_factory.client_type == "httpx":
            import httpx

            auth = httpx.BasicAuth("user", "pass")
        else:
            import faster_http

            auth = faster_http.BasicAuth("user", "pass")

        with client_factory(auth=auth) as client:
            response = client.get(f"{self.base_url}/basic-auth/user/pass")
            assert response.status_code == 200

    @httpx_compatibility_test
    def test_digest_auth_creation(self, client_factory):
        """Test DigestAuth can be created."""
        # TDD: Red phase - this will fail initially
        import faster_http

        auth = faster_http.DigestAuth("username", "password")
        assert auth is not None

    @httpx_compatibility_test
    def test_digest_auth_request(self, client_factory):
        """Test request with DigestAuth."""
        # TDD: Red phase - this will fail initially

        # Create appropriate auth object based on the client type
        if client_factory.client_type == "httpx":
            import httpx

            auth = httpx.DigestAuth("user", "pass")
        else:
            import faster_http

            auth = faster_http.DigestAuth("user", "pass")

        with client_factory(auth=auth) as client:
            response = client.get(f"{self.base_url}/digest-auth/auth/user/pass")
            assert response.status_code == 200

    @httpx_compatibility_test
    def test_netrc_auth_creation(self, client_factory):
        """Test NetRCAuth can be created."""
        # TDD: Red phase - this will fail initially
        import faster_http

        auth = faster_http.NetRCAuth()
        assert auth is not None

    @httpx_compatibility_test
    def test_auth_inheritance(self, client_factory):
        """Test auth can be passed to individual requests."""
        # TDD: Red phase - this will fail initially

        # Create appropriate auth object based on the client type
        if client_factory.client_type == "httpx":
            import httpx

            auth = httpx.BasicAuth("user", "pass")
        else:
            import faster_http

            auth = faster_http.BasicAuth("user", "pass")

        response = client_factory.get(f"{self.base_url}/basic-auth/user/pass", auth=auth)
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_auth_base_class_creation(self, client_factory):
        """Test Auth base class can be created and has correct methods."""
        if client_factory.client_type == "httpx":
            import httpx

            auth = httpx.Auth()
        else:
            import faster_http

            auth = faster_http.Auth()

        # Test basic creation
        assert auth is not None

        # Test required methods exist
        assert hasattr(auth, "auth_flow")
        assert hasattr(auth, "sync_auth_flow")
        assert hasattr(auth, "async_auth_flow")

        # Test required properties exist
        assert hasattr(auth, "requires_request_body")
        assert hasattr(auth, "requires_response_body")

    @httpx_compatibility_test
    def test_auth_base_class_properties(self, client_factory):
        """Test Auth base class properties return correct default values."""
        if client_factory.client_type == "httpx":
            import httpx

            auth = httpx.Auth()
        else:
            import faster_http

            auth = faster_http.Auth()

        # Test property default values match httpx
        assert not auth.requires_request_body
        assert not auth.requires_response_body

    @httpx_compatibility_test
    def test_auth_base_class_methods_raise_not_implemented(self, client_factory):
        """Test Auth base class methods raise NotImplementedError."""
        if client_factory.client_type == "httpx":
            import httpx

            auth = httpx.Auth()
        else:
            import faster_http

            auth = faster_http.Auth()

        # Create a mock request object
        class MockRequest:
            pass

        request = MockRequest()

        # Test auth_flow raises NotImplementedError
        with pytest.raises(NotImplementedError):
            list(auth.auth_flow(request))
