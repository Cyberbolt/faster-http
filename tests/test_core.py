"""
Core functionality tests for faster_http.
Tests basic HTTP methods, clients, and response handling.
"""

import pytest
import asyncio
from .conftest import assert_response_ok, assert_response_has_basic_attrs, assert_httpx_compatibility

from faster_http import (
    get, post, put, patch, delete, head, options,
    Client, AsyncClient, Response,
    HTTPError, ConnectTimeout, ReadTimeout, RequestError
)


class TestBasicHttpMethods:
    """Test basic HTTP methods."""
    
    def test_get_request(self, test_urls, sample_headers):
        """Test basic GET request."""
        response = get(test_urls['get'])
        assert_response_ok(response)
        assert_response_has_basic_attrs(response)
        
        # Test JSON response
        data = response.json()
        assert isinstance(data, dict)
        assert 'url' in data
    
    def test_get_with_params(self, test_urls):
        """Test GET request with query parameters."""
        params = {'key1': 'value1', 'key2': 'value2'}
        response = get(test_urls['get'], params=params)
        assert_response_ok(response)
        
        data = response.json()
        assert data['args']['key1'] == 'value1'
        assert data['args']['key2'] == 'value2'
    
    def test_get_with_headers(self, test_urls, sample_headers):
        """Test GET request with custom headers."""
        response = get(test_urls['get'], headers=sample_headers)
        assert_response_ok(response)
        
        data = response.json()
        assert data['headers']['User-Agent'] == sample_headers['User-Agent']
        assert data['headers']['X-Test-Header'] == sample_headers['X-Test-Header']
    
    def test_post_json(self, test_urls, sample_json_data):
        """Test POST request with JSON data."""
        response = post(test_urls['post'], json=sample_json_data)
        assert_response_ok(response)
        
        data = response.json()
        assert data['json'] == sample_json_data
    
    def test_post_form_data(self, test_urls, sample_form_data):
        """Test POST request with form data."""
        response = post(test_urls['post'], data=sample_form_data)
        assert_response_ok(response)
        
        data = response.json()
        assert data['form']['username'] == sample_form_data['username']
        assert data['form']['password'] == sample_form_data['password']
    
    def test_put_request(self, test_urls, sample_json_data):
        """Test PUT request."""
        response = put(test_urls['put'], json=sample_json_data)
        assert_response_ok(response)
        
        data = response.json()
        assert data['json'] == sample_json_data
    
    def test_patch_request(self, test_urls):
        """Test PATCH request."""
        patch_data = {'patched': 'field'}
        response = patch(test_urls['patch'], json=patch_data)
        assert_response_ok(response)
        
        data = response.json()
        assert data['json'] == patch_data
    
    def test_delete_request(self, test_urls):
        """Test DELETE request."""
        response = delete(test_urls['delete'])
        assert_response_ok(response)
    
    def test_head_request(self, test_urls):
        """Test HEAD request."""
        response = head(test_urls['get'])
        assert response.status_code == 200
        # HEAD requests should have empty content
        assert len(response.content) == 0
    
    def test_options_request(self, test_urls):
        """Test OPTIONS request."""
        response = options(test_urls['get'])
        assert response.status_code == 200


class TestSyncClient:
    """Test synchronous Client functionality."""
    
    def test_client_basic(self, test_urls):
        """Test basic client usage."""
        with Client() as client:
            response = client.get(test_urls['get'])
            assert_response_ok(response)
    
    def test_client_with_base_url(self):
        """Test client with base URL."""
        with Client(base_url='https://httpbin.org') as client:
            response = client.get('/get')
            assert_response_ok(response)
            assert 'httpbin.org' in response.url
    
    def test_client_with_headers(self, test_urls, sample_headers):
        """Test client with default headers."""
        with Client(headers=sample_headers) as client:
            response = client.get(test_urls['get'])
            assert_response_ok(response)
            
            data = response.json()
            assert data['headers']['User-Agent'] == sample_headers['User-Agent']
    
    def test_client_timeout(self, test_urls):
        """Test client with timeout."""
        with Client(timeout=10.0) as client:
            response = client.get(test_urls['get'])
            assert_response_ok(response)
            assert response.elapsed < 10.0
    
    def test_client_build_request(self, test_urls):
        """Test client build_request method."""
        with Client() as client:
            request = client.build_request('GET', test_urls['get'])
            assert request.method == 'GET'
            assert request.url == test_urls['get']
    
    def test_client_send_request(self, test_urls):
        """Test client send method."""
        with Client() as client:
            request = client.build_request('GET', test_urls['get'])
            response = client.send(request)
            assert_response_ok(response)


class TestAsyncClient:
    """Test asynchronous Client functionality."""
    
    @pytest.mark.asyncio
    async def test_async_client_basic(self, test_urls):
        """Test basic async client usage."""
        async with AsyncClient() as client:
            response = await client.get(test_urls['get'])
            assert_response_ok(response)
    
    @pytest.mark.asyncio
    async def test_async_client_with_base_url(self):
        """Test async client with base URL."""
        async with AsyncClient(base_url='https://httpbin.org') as client:
            response = await client.get('/get')
            assert_response_ok(response)
            assert 'httpbin.org' in response.url
    
    @pytest.mark.asyncio
    async def test_async_post_json(self, test_urls, sample_json_data):
        """Test async POST request with JSON."""
        async with AsyncClient() as client:
            response = await client.post(test_urls['post'], json=sample_json_data)
            assert_response_ok(response)
            
            data = response.json()
            assert data['json'] == sample_json_data
    
    @pytest.mark.asyncio
    async def test_async_concurrent_requests(self, test_urls):
        """Test concurrent async requests."""
        urls = [f"{test_urls['get']}?id={i}" for i in range(3)]
        
        async with AsyncClient() as client:
            tasks = [client.get(url) for url in urls]
            responses = await asyncio.gather(*tasks)
            
            for response in responses:
                assert_response_ok(response)


class TestResponse:
    """Test Response object functionality."""
    
    def test_response_properties(self, test_urls):
        """Test response properties."""
        response = get(test_urls['get'])
        
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
        assert isinstance(response.http_version, str)
        assert isinstance(response.cookies, dict)
    
    def test_response_json(self, test_urls):
        """Test JSON response parsing."""
        response = get(test_urls['json'])
        assert_response_ok(response)
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_response_repr(self, test_urls):
        """Test response string representation."""
        response = get(test_urls['get'])
        repr_str = repr(response)
        assert 'Response' in repr_str
        assert '200' in repr_str
    
    def test_raise_for_status_success(self, test_urls):
        """Test raise_for_status with successful response."""
        response = get(test_urls['get'])
        # Should not raise any exception
        response.raise_for_status()
    
    def test_raise_for_status_error(self, test_urls):
        """Test raise_for_status with error response."""
        response = get(test_urls['status'].format(code=404))
        assert response.status_code == 404
        assert not response.ok
        assert response.is_client_error
        
        with pytest.raises(HTTPError):
            response.raise_for_status()
    
    def test_response_status_checks(self, test_urls):
        """Test response status checking properties."""
        # Test successful response
        response = get(test_urls['status'].format(code=200))
        assert response.ok
        assert not response.is_redirect
        assert not response.is_client_error
        assert not response.is_server_error
        
        # Test client error
        response = get(test_urls['status'].format(code=404))
        assert not response.ok
        assert response.is_client_error
        assert not response.is_server_error
        
        # Test server error
        response = get(test_urls['status'].format(code=500))
        assert not response.ok
        assert not response.is_client_error
        assert response.is_server_error


class TestFileUpload:
    """Test file upload functionality."""
    
    def test_file_upload_bytes(self, test_urls):
        """Test file upload with bytes."""
        files = {'test_file': b'Hello, World!'}
        response = post(test_urls['post'], files=files)
        assert_response_ok(response)
    
    def test_file_upload_with_client(self, test_urls):
        """Test file upload with client."""
        with Client() as client:
            files = {'test_file': b'Client upload test'}
            response = client.post(test_urls['post'], files=files)
            assert_response_ok(response)
    
    def test_multipart_mixed_upload(self, test_urls):
        """Test mixed multipart upload (files + form data)."""
        files = {'upload_file': b'File content'}
        data = {'field1': 'value1', 'field2': 'value2'}
        response = post(test_urls['post'], files=files, data=data)
        assert_response_ok(response)
    
    @pytest.mark.asyncio
    async def test_async_file_upload(self, test_urls):
        """Test async file upload."""
        async with AsyncClient() as client:
            files = {'async_file': b'Async upload test'}
            response = await client.post(test_urls['post'], files=files)
            assert_response_ok(response)


class TestHttpxCompatibility:
    """Test httpx compatibility features."""
    
    def test_httpx_replacement(self, test_urls):
        """Test using faster_http as httpx replacement."""
        import faster_http as httpx  # Simulate httpx replacement
        
        response = httpx.get(test_urls['get'])
        assert_response_ok(response)
        
        with httpx.Client() as client:
            response = client.get(test_urls['get'])
            assert_response_ok(response)
    
    def test_response_httpx_compatibility(self, test_urls):
        """Test response object httpx compatibility."""
        response = get(test_urls['get'])
        assert_httpx_compatibility(response)
    
    def test_iterator_methods(self, test_urls):
        """Test response iterator methods."""
        response = get(test_urls['get'])
        
        # Test iter_bytes
        byte_chunks = response.iter_bytes(chunk_size=100)
        assert isinstance(byte_chunks, list)
        assert len(byte_chunks) > 0
        
        # Test iter_text
        text_chunks = response.iter_text(chunk_size=100)
        assert isinstance(text_chunks, list)
        assert len(text_chunks) > 0
        
        # Test iter_lines
        lines = response.iter_lines()
        assert isinstance(lines, list)
        assert len(lines) > 0


class TestErrorHandling:
    """Test error handling."""
    
    def test_invalid_url(self):
        """Test handling of invalid URLs."""
        with pytest.raises(Exception):
            get('not-a-valid-url')
    
    def test_connection_error(self):
        """Test handling of connection errors."""
        with pytest.raises((ConnectTimeout, RequestError, Exception)):
            get('http://127.0.0.1:9999', timeout=1.0)
    
    def test_timeout_error(self, test_urls):
        """Test timeout handling."""
        with pytest.raises((ReadTimeout, Exception)):
            get(test_urls['delay'].format(seconds=5), timeout=1.0)


class TestParameterCombinations:
    """Test various parameter combinations."""
    
    def test_all_parameters_combined(self, test_urls, sample_headers, sample_cookies):
        """Test combining all parameters."""
        params = {'test_param': 'test_value'}
        
        response = get(
            test_urls['get'],
            params=params,
            headers=sample_headers,
            cookies=sample_cookies,
            timeout=30,
            follow_redirects=True
        )
        assert_response_ok(response)
        
        data = response.json()
        assert data['args']['test_param'] == 'test_value'
        assert data['headers']['X-Test-Header'] == sample_headers['X-Test-Header']
    
    @pytest.mark.asyncio
    async def test_async_all_parameters(self, test_urls, sample_headers, sample_cookies):
        """Test async client with all parameters."""
        async with AsyncClient(
            headers=sample_headers,
            cookies=sample_cookies,
            timeout=30
        ) as client:
            response = await client.get(test_urls['get'])
            assert_response_ok(response)
            
            data = response.json()
            assert data['headers']['X-Test-Header'] == sample_headers['X-Test-Header'] 