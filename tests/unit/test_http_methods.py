"""Tests for top-level HTTP methods (get, post, etc.)."""

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test


class TestHTTPMethods:
    """Test top-level HTTP method functions."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_get_basic(self, client_factory):
        """Test basic GET request."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/get")
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_post_basic(self, client_factory):
        """Test basic POST request."""
        # TDD: Red phase - this will fail initially
        response = client_factory.post(f"{self.base_url}/post", json={"test": "data"})
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_put_basic(self, client_factory):
        """Test basic PUT request."""
        # TDD: Red phase - this will fail initially
        response = client_factory.put(f"{self.base_url}/put", json={"test": "data"})
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_patch_basic(self, client_factory):
        """Test basic PATCH request."""
        # TDD: Red phase - this will fail initially
        response = client_factory.patch(f"{self.base_url}/patch", json={"test": "data"})
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_delete_basic(self, client_factory):
        """Test basic DELETE request."""
        # TDD: Red phase - this will fail initially
        response = client_factory.delete(f"{self.base_url}/delete")
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_head_basic(self, client_factory):
        """Test basic HEAD request."""
        # TDD: Red phase - this will fail initially
        response = client_factory.head(f"{self.base_url}/head")
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_options_basic(self, client_factory):
        """Test basic OPTIONS request."""
        # TDD: Red phase - this will fail initially
        response = client_factory.options(f"{self.base_url}/options")
        assert response.status_code == 200
