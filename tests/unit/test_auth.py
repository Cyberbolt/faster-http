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
        import faster_http

        auth = faster_http.BasicAuth("user", "pass")

        response = client_factory.get(f"{self.base_url}/basic-auth/user/pass", auth=auth)
        assert response.status_code == 200
