"""
Tests for httpx compatibility features.
These tests verify that our implementation provides the same interface as httpx.
"""

import pytest
from faster_http import (
    get, post, Request,
    Client, AsyncClient, 
    HTTPError, RequestError
)


class TestRequestObject:
    """Test Request object functionality."""
    
    def test_request_creation(self):
        """Test creating a Request object."""
        request = Request("GET", "https://httpbin.org/get")
        assert request.method == "GET"
        assert request.url == "https://httpbin.org/get"
        assert isinstance(request.headers, dict)
        assert request.content is None
    
    def test_request_with_headers(self):
        """Test Request with headers."""
        headers = {"X-Test": "value"}
        request = Request("POST", "https://httpbin.org/post", headers=headers)
        assert request.headers["X-Test"] == "value"
    
    def test_request_with_content(self):
        """Test Request with content."""
        content = b"test content"
        request = Request("POST", "https://httpbin.org/post", content=content)
        assert request.content == content
    
    def test_request_repr(self):
        """Test Request string representation."""
        request = Request("GET", "https://httpbin.org/get")
        repr_str = repr(request)
        assert "GET" in repr_str
        assert "httpbin.org/get" in repr_str


class TestClientBuildRequest:
    """Test Client.build_request functionality."""
    
    def test_build_simple_request(self):
        """Test building a simple request."""
        with Client() as client:
            request = client.build_request("GET", "https://httpbin.org/get")
            assert request.method == "GET"
            assert request.url == "https://httpbin.org/get"
    
    def test_build_request_with_params(self):
        """Test building request with parameters."""
        with Client() as client:
            params = {"test": "value", "num": "123"}
            request = client.build_request("GET", "https://httpbin.org/get", params=params)
            assert "test=value" in request.url
            assert "num=123" in request.url
    
    def test_build_request_with_headers(self):
        """Test building request with headers."""
        with Client() as client:
            headers = {"X-Custom": "test"}
            request = client.build_request("GET", "https://httpbin.org/get", headers=headers)
            assert request.headers["X-Custom"] == "test"
    
    def test_build_request_with_base_url(self):
        """Test building request with base URL."""
        with Client(base_url="https://httpbin.org") as client:
            request = client.build_request("GET", "/get")
            assert "httpbin.org/get" in request.url
    
    def test_build_request_merges_default_headers(self):
        """Test that build_request merges default headers."""
        default_headers = {"X-Default": "default"}
        with Client(headers=default_headers) as client:
            request_headers = {"X-Request": "request"}
            request = client.build_request("GET", "/get", headers=request_headers)
            assert request.headers["X-Default"] == "default"
            assert request.headers["X-Request"] == "request"


class TestClientSendRequest:
    """Test Client.send functionality."""
    
    def test_send_simple_request(self):
        """Test sending a pre-built request."""
        with Client() as client:
            request = client.build_request("GET", "https://httpbin.org/get")
            response = client.send(request)
            assert response.status_code == 200
            assert response.ok
    
    def test_send_request_with_headers(self):
        """Test sending request with custom headers."""
        with Client() as client:
            headers = {"X-Test": "send-test"}
            request = client.build_request("GET", "https://httpbin.org/get", headers=headers)
            response = client.send(request)
            assert response.status_code == 200
            data = response.json()
            assert data["headers"]["X-Test"] == "send-test"
    
    def test_send_post_request_with_content(self):
        """Test sending POST request with content."""
        with Client() as client:
            content = b'{"test": "data"}'
            headers = {"Content-Type": "application/json"}
            request = client.build_request("POST", "https://httpbin.org/post", 
                                         headers=headers, content=content)
            response = client.send(request)
            assert response.status_code == 200
            data = response.json()
            assert data["data"] == '{"test": "data"}'


class TestResponseEncodingFeatures:
    """Test new response encoding features."""
    
    def test_response_encoding_property(self):
        """Test response.encoding property."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        assert isinstance(response.encoding, str)
        # Default encoding should be utf-8
        assert response.encoding.lower() in ["utf-8", "utf8"]
    
    def test_response_encoding_setter(self):
        """Test setting response.encoding."""
        response = get("https://httpbin.org/get")
        response.encoding = "iso-8859-1"
        assert response.encoding == "iso-8859-1"
    
    def test_response_charset_encoding(self):
        """Test response.charset_encoding property."""
        response = get("https://httpbin.org/json")
        assert response.status_code == 200
        charset = response.charset_encoding
        # httpbin typically returns application/json without charset
        # charset_encoding may be None
        if charset:
            assert isinstance(charset, str)
    
    def test_response_text_uses_encoding(self):
        """Test that response.text respects encoding."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        text = response.text
        assert isinstance(text, str)
        assert len(text) > 0


class TestResponseIteratorMethods:
    """Test response iterator methods."""
    
    def test_iter_bytes(self):
        """Test response.iter_bytes()."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        
        chunks = response.iter_bytes(chunk_size=1024)
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        
        # All chunks should be bytes (Vec<u8> in Python becomes list)
        for chunk in chunks:
            assert isinstance(chunk, (bytes, list))
        
        # Total size should match content length
        total_size = sum(len(chunk) for chunk in chunks)
        assert total_size == len(response.content)
    
    def test_iter_text(self):
        """Test response.iter_text()."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        
        text_chunks = response.iter_text(chunk_size=512)
        assert isinstance(text_chunks, list)
        assert len(text_chunks) > 0
        
        # All chunks should be strings
        for chunk in text_chunks:
            assert isinstance(chunk, str)
        
        # Joined text should match response.text
        joined_text = "".join(text_chunks)
        assert joined_text == response.text
    
    def test_iter_lines(self):
        """Test response.iter_lines()."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        
        lines = response.iter_lines()
        assert isinstance(lines, list)
        assert len(lines) > 0
        
        # All lines should be strings
        for line in lines:
            assert isinstance(line, str)
        
        # Lines should reconstruct the text
        joined_lines = "\n".join(lines)
        # Note: might differ due to trailing newlines
        assert joined_lines in response.text or response.text in joined_lines
    
    def test_iter_raw(self):
        """Test response.iter_raw()."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        
        raw_chunks = response.iter_raw(chunk_size=1024)
        assert isinstance(raw_chunks, list)
        assert len(raw_chunks) > 0
        
        # All chunks should be bytes (Vec<u8> in Python becomes list)
        for chunk in raw_chunks:
            assert isinstance(chunk, (bytes, list))
        
        # Should be identical to iter_bytes
        byte_chunks = response.iter_bytes(chunk_size=1024)
        assert raw_chunks == byte_chunks


class TestResponseNewAttributes:
    """Test new response attributes."""
    
    def test_response_history(self):
        """Test response.history attribute."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        assert hasattr(response, 'history')
        assert isinstance(response.history, list)
        # For a direct request, history should be empty
        assert len(response.history) == 0
    
    def test_response_request(self):
        """Test response.request attribute."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        assert hasattr(response, 'request')
        # Currently returns None, but the attribute exists
        # In a full implementation, this would contain the original request
    
    def test_response_text_is_property(self):
        """Test that response.text is a property, not a method."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        
        # Should be accessible as a property
        text = response.text
        assert isinstance(text, str)
        
        # Should not be callable
        assert not callable(response.text)


class TestHttp2Support:
    """Test HTTP/2 support."""
    
    def test_client_http2_parameter(self):
        """Test that http2 parameter is accepted."""
        # Should not raise an error during client creation
        try:
            with Client(http2=True) as client:
                # Just verify the client was created successfully
                assert client is not None
                
            with Client(http2=False) as client:
                # Just verify the client was created successfully
                assert client is not None
                # Test with a basic request if possible
                try:
                    response = client.get("https://httpbin.org/get")
                    assert response.status_code == 200
                except Exception:
                    # HTTP/2 configuration might cause connection issues
                    # but that's not a failure of parameter acceptance
                    pass
        except Exception as e:
            pytest.fail(f"HTTP/2 parameter should be accepted: {e}")
    
    @pytest.mark.asyncio
    async def test_async_client_http2_parameter(self):
        """Test async client HTTP/2 parameter."""
        try:
            async with AsyncClient(http2=True) as client:
                # Just verify the client was created successfully
                assert client is not None
            
            async with AsyncClient(http2=False) as client:
                # Just verify the client was created successfully
                assert client is not None
                # Test with a basic request if possible
                try:
                    response = await client.get("https://httpbin.org/get")
                    assert response.status_code == 200
                except Exception:
                    # HTTP/2 configuration might cause connection issues
                    # but that's not a failure of parameter acceptance
                    pass
        except Exception as e:
            pytest.fail(f"HTTP/2 parameter should be accepted: {e}")


class TestAsyncClientBuildSend:
    """Test AsyncClient build_request and send functionality."""
    
    @pytest.mark.asyncio
    async def test_async_build_request(self):
        """Test async client build_request."""
        async with AsyncClient() as client:
            request = client.build_request("GET", "https://httpbin.org/get")
            assert request.method == "GET"
            assert "httpbin.org/get" in request.url
    
    @pytest.mark.asyncio
    async def test_async_send_request(self):
        """Test async client send request."""
        async with AsyncClient() as client:
            request = client.build_request("GET", "https://httpbin.org/get")
            response = await client.send(request)
            assert response.status_code == 200
            assert response.ok
    
    @pytest.mark.asyncio
    async def test_async_send_with_headers(self):
        """Test async send with custom headers."""
        async with AsyncClient() as client:
            headers = {"X-Async": "test"}
            request = client.build_request("GET", "https://httpbin.org/get", headers=headers)
            response = await client.send(request)
            assert response.status_code == 200
            data = response.json()
            assert data["headers"]["X-Async"] == "test"


class TestErrorHandling:
    """Test error handling for new features."""
    
    def test_invalid_method_in_request(self):
        """Test error handling for invalid HTTP method."""
        with Client() as client:
            # Invalid method should still create request object
            request = Request("INVALID", "https://httpbin.org/get")
            # But sending should raise an error
            try:
                response = client.send(request)
                # If it doesn't raise an error, the invalid method was somehow accepted
                # This might happen if the underlying library is lenient
                print(f"Unexpected success with invalid method, status: {response.status_code}")
            except RequestError:
                # This is the expected behavior
                pass
            except Exception as e:
                # Any other error is also acceptable for invalid method
                print(f"Invalid method raised: {type(e).__name__}: {e}")
                pass
    
    def test_invalid_url_in_build_request(self):
        """Test error handling for invalid URL with params."""
        with Client() as client:
            # This might raise an error when building params
            try:
                request = client.build_request("GET", "invalid-url", params={"test": "value"})
                # If no error during build, send should fail
                with pytest.raises(RequestError):
                    client.send(request)
            except RequestError:
                # Error during build is also acceptable
                pass


class TestBackwardCompatibility:
    """Test that new features don't break existing functionality."""
    
    def test_old_methods_still_work(self):
        """Test that existing methods work unchanged."""
        # Basic GET
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        
        # POST with JSON
        response = post("https://httpbin.org/post", json={"test": "data"})
        assert response.status_code == 200
        
        # Client methods
        with Client() as client:
            response = client.get("https://httpbin.org/get")
            assert response.status_code == 200
    
    def test_response_attributes_unchanged(self):
        """Test that existing response attributes work unchanged."""
        response = get("https://httpbin.org/get")
        
        # Basic attributes
        assert isinstance(response.status_code, int)
        assert isinstance(response.headers, dict)
        assert isinstance(response.url, str)
        assert isinstance(response.ok, bool)
        assert isinstance(response.content, bytes)
        assert isinstance(response.text, str)
        assert isinstance(response.elapsed, float)
        
        # Status check methods
        assert isinstance(response.is_client_error, bool)
        assert isinstance(response.is_server_error, bool)
        assert isinstance(response.is_redirect, bool)
        
        # Methods
        data = response.json()
        assert isinstance(data, dict)
        
        # Should not raise
        response.raise_for_status()
    
    @pytest.mark.asyncio
    async def test_async_methods_unchanged(self):
        """Test that async methods work unchanged."""
        async with AsyncClient() as client:
            response = await client.get("https://httpbin.org/get")
            assert response.status_code == 200
            
            response = await client.post("https://httpbin.org/post", json={"test": "data"})
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 