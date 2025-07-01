"""
Basic tests for faster_http functionality.
"""

import pytest
import asyncio
import json
from faster_http import (
    get, post, put, patch, delete, head, options,
    Client, AsyncClient, Response,
    HTTPError, ConnectTimeout, ReadTimeout, RequestError
)


class TestTopLevelFunctions:
    """Test top-level convenience functions."""
    
    def test_get_request(self):
        """Test basic GET request."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        assert response.ok
        assert "httpbin.org" in response.url
        
        # Test JSON response
        data = response.json()
        assert isinstance(data, dict)
        assert "url" in data
    
    def test_get_with_params(self):
        """Test GET request with query parameters."""
        params = {"key1": "value1", "key2": "value2"}
        response = get("https://httpbin.org/get", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["args"]["key1"] == "value1"
        assert data["args"]["key2"] == "value2"
    
    def test_get_with_headers(self):
        """Test GET request with custom headers."""
        headers = {"User-Agent": "faster-http-test", "X-Custom": "test-value"}
        response = get("https://httpbin.org/get", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["headers"]["User-Agent"] == "faster-http-test"
        assert data["headers"]["X-Custom"] == "test-value"
    
    def test_post_json(self):
        """Test POST request with JSON data."""
        json_data = {"key": "value", "number": 42}
        response = post("https://httpbin.org/post", json=json_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["json"] == json_data
    
    def test_post_form_data(self):
        """Test POST request with form data."""
        form_data = {"key": "value", "another": "data"}
        response = post("https://httpbin.org/post", data=form_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["form"]["key"] == "value"
        assert data["form"]["another"] == "data"
    
    def test_put_request(self):
        """Test PUT request."""
        json_data = {"updated": "data"}
        response = put("https://httpbin.org/put", json=json_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["json"] == json_data
    
    def test_patch_request(self):
        """Test PATCH request."""
        json_data = {"patched": "field"}
        response = patch("https://httpbin.org/patch", json=json_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["json"] == json_data
    
    def test_delete_request(self):
        """Test DELETE request."""
        response = delete("https://httpbin.org/delete")
        assert response.status_code == 200
    
    def test_head_request(self):
        """Test HEAD request."""
        response = head("https://httpbin.org/get")
        assert response.status_code == 200
        # HEAD requests should have empty content
        assert len(response.content) == 0
    
    def test_options_request(self):
        """Test OPTIONS request."""
        response = options("https://httpbin.org/get")
        assert response.status_code == 200


class TestClient:
    """Test Client class functionality."""
    
    def test_client_basic(self):
        """Test basic client usage."""
        with Client() as client:
            response = client.get("https://httpbin.org/get")
            assert response.status_code == 200
    
    def test_client_with_base_url(self):
        """Test client with base URL."""
        with Client(base_url="https://httpbin.org") as client:
            response = client.get("/get")
            assert response.status_code == 200
            assert "httpbin.org" in response.url
    
    def test_client_with_headers(self):
        """Test client with default headers."""
        headers = {"User-Agent": "faster-http-client"}
        with Client(headers=headers) as client:
            response = client.get("https://httpbin.org/get")
            assert response.status_code == 200
            
            data = response.json()
            assert data["headers"]["User-Agent"] == "faster-http-client"
    
    def test_client_timeout(self):
        """Test client with timeout."""
        with Client(timeout=10.0) as client:
            response = client.get("https://httpbin.org/get")
            assert response.status_code == 200
            assert response.elapsed < 10.0


class TestAsyncClient:
    """Test AsyncClient class functionality."""
    
    @pytest.mark.asyncio
    async def test_async_client_basic(self):
        """Test basic async client usage."""
        async with AsyncClient() as client:
            response = await client.get("https://httpbin.org/get")
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_async_client_with_base_url(self):
        """Test async client with base URL."""
        async with AsyncClient(base_url="https://httpbin.org") as client:
            response = await client.get("/get")
            assert response.status_code == 200
            assert "httpbin.org" in response.url
    
    @pytest.mark.asyncio
    async def test_async_post_json(self):
        """Test async POST request with JSON."""
        json_data = {"async": "test", "value": 123}
        async with AsyncClient() as client:
            response = await client.post("https://httpbin.org/post", json=json_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["json"] == json_data


class TestResponse:
    """Test Response object functionality."""
    
    def test_response_properties(self):
        """Test response properties."""
        response = get("https://httpbin.org/get")
        
        # Status properties
        assert isinstance(response.status_code, int)
        assert response.ok
        assert not response.is_client_error
        assert not response.is_server_error
        
        # Content properties
        assert isinstance(response.content, bytes)
        assert isinstance(response.text, str)
        assert isinstance(response.headers, dict)
        assert isinstance(response.url, str)
        assert isinstance(response.elapsed, float)
    
    def test_response_json(self):
        """Test JSON response parsing."""
        response = get("https://httpbin.org/json")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_response_text(self):
        """Test text response."""
        response = get("https://httpbin.org/html")
        assert response.status_code == 200
        
        text = response.text
        assert isinstance(text, str)
        assert "html" in text.lower()
    
    def test_response_repr(self):
        """Test response string representation."""
        response = get("https://httpbin.org/get")
        repr_str = repr(response)
        assert "Response" in repr_str
        assert "200" in repr_str
    
    def test_raise_for_status_success(self):
        """Test raise_for_status with successful response."""
        response = get("https://httpbin.org/get")
        # Should not raise any exception
        response.raise_for_status()
    
    def test_raise_for_status_error(self):
        """Test raise_for_status with error response."""
        response = get("https://httpbin.org/status/404")
        assert response.status_code == 404
        assert not response.ok
        assert response.is_client_error
        
        with pytest.raises(HTTPError):
            response.raise_for_status()


class TestErrorHandling:
    """Test error handling."""
    
    def test_invalid_url(self):
        """Test handling of invalid URLs."""
        with pytest.raises(Exception):  # Should raise some kind of error
            get("not-a-valid-url")
    
    def test_connection_error(self):
        """Test handling of connection errors."""
        with pytest.raises((ConnectTimeout, RequestError, Exception)):
            get("http://127.0.0.1:9999", timeout=1.0)  # Port that should be closed


if __name__ == "__main__":
    pytest.main([__file__]) 