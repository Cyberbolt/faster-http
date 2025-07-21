"""
Unit tests for Client functionality.
Tests the synchronous and asynchronous client implementations by comparing with httpx.
"""

import pytest
import asyncio
import httpx
import faster_http
from ..conftest import assert_response_ok, assert_httpx_compatibility, assert_response_equivalence
from ..helpers.comparison import compare_sync_clients, compare_async_clients


class TestSyncClient:
    """Test synchronous Client functionality by comparing with httpx."""
    
    def test_client_basic_get(self, test_urls):
        """Test basic client GET request - compare httpx vs faster-http."""
        # Test with httpx first
        with httpx.Client() as httpx_client:
            httpx_response = httpx_client.get(test_urls['get'])
            assert_response_ok(httpx_response)
        
        # Test with faster-http second
        with faster_http.Client() as faster_client:
            faster_response = faster_client.get(test_urls['get'])
            assert_response_ok(faster_response)
            assert_httpx_compatibility(faster_response)
        
        # Compare responses
        assert_response_equivalence(httpx_response, faster_response)
    
    def test_client_with_base_url(self, test_urls):
        """Test client with base URL - compare httpx vs faster-http."""
        base_url = test_urls['get'].rsplit('/', 1)[0]  # Use local test server
        
        # Test with httpx first
        with httpx.Client(base_url=base_url) as httpx_client:
            httpx_response = httpx_client.get('/get')
            assert_response_ok(httpx_response)
            assert '/get' in httpx_response.url
        
        # Test with faster-http second
        with faster_http.Client(base_url=base_url) as faster_client:
            faster_response = faster_client.get('/get')
            assert_response_ok(faster_response)
            assert '/get' in faster_response.url
        
        # Compare responses
        assert_response_equivalence(httpx_response, faster_response)
    
    def test_client_with_headers(self, test_urls, sample_headers):
        """Test client with default headers - compare httpx vs faster-http."""
        headers = {'User-Agent': 'test-client/1.0', 'X-Test': 'value'}
        
        # Test with httpx first
        with httpx.Client(headers=headers) as httpx_client:
            httpx_response = httpx_client.get(test_urls['get'])
            assert_response_ok(httpx_response)
            httpx_data = httpx_response.json()
            assert httpx_data['headers']['User-Agent'] == 'test-client/1.0'
            assert httpx_data['headers']['X-Test'] == 'value'
        
        # Test with faster-http second
        with faster_http.Client(headers=headers) as faster_client:
            faster_response = faster_client.get(test_urls['get'])
            assert_response_ok(faster_response)
            faster_data = faster_response.json()
            assert faster_data['headers']['User-Agent'] == 'test-client/1.0'
            assert faster_data['headers']['X-Test'] == 'value'
        
        # Compare JSON responses
        assert httpx_data['headers']['User-Agent'] == faster_data['headers']['User-Agent']
        assert httpx_data['headers']['X-Test'] == faster_data['headers']['X-Test']
    
    def test_client_with_cookies(self, test_urls, sample_cookies):
        """Test client with default cookies - compare httpx vs faster-http."""
        cookies = {'session': 'abc123', 'user': 'testuser'}
        
        # Test with httpx first
        with httpx.Client(cookies=cookies) as httpx_client:
            httpx_response = httpx_client.get(test_urls['cookies'])
            assert_response_ok(httpx_response)
            httpx_data = httpx_response.json()
            assert httpx_data['cookies']['session'] == 'abc123'
            assert httpx_data['cookies']['user'] == 'testuser'
        
        # Test with faster-http second
        with faster_http.Client(cookies=cookies) as faster_client:
            faster_response = faster_client.get(test_urls['cookies'])
            assert_response_ok(faster_response)
            faster_data = faster_response.json()
            assert faster_data['cookies']['session'] == 'abc123'
            assert faster_data['cookies']['user'] == 'testuser'
        
        # Compare cookie data
        assert httpx_data['cookies'] == faster_data['cookies']
    
    def test_client_with_timeout(self, test_urls):
        """Test client with timeout - compare httpx vs faster-http."""
        timeout = 30.0
        
        # Test with httpx first
        with httpx.Client(timeout=timeout) as httpx_client:
            httpx_response = httpx_client.get(test_urls['get'])
            assert_response_ok(httpx_response)
            assert httpx_response.elapsed < timeout
        
        # Test with faster-http second
        with faster_http.Client(timeout=timeout) as faster_client:
            faster_response = faster_client.get(test_urls['get'])
            assert_response_ok(faster_response)
            assert faster_response.elapsed < timeout
        
        # Both should complete within timeout
        assert httpx_response.elapsed < timeout
        assert faster_response.elapsed < timeout
    
    def test_client_build_request(self, test_urls):
        """Test client build_request method - compare httpx vs faster-http."""
        url = test_urls['get']
        
        # Test with httpx first
        with httpx.Client() as httpx_client:
            httpx_request = httpx_client.build_request('GET', url)
            assert httpx_request.method == 'GET'
            assert httpx_request.url == url
        
        # Test with faster-http second
        with faster_http.Client() as faster_client:
            faster_request = faster_client.build_request('GET', url)
            assert faster_request.method == 'GET'
            assert faster_request.url == url
        
        # Compare request objects
        assert httpx_request.method == faster_request.method
        assert httpx_request.url == faster_request.url
    
    def test_client_send_request(self, test_urls):
        """Test client send method - compare httpx vs faster-http."""
        url = test_urls['get']
        
        # Test with httpx first
        with httpx.Client() as httpx_client:
            httpx_request = httpx_client.build_request('GET', url)
            httpx_response = httpx_client.send(httpx_request)
            assert_response_ok(httpx_response)
        
        # Test with faster-http second
        with faster_http.Client() as faster_client:
            faster_request = faster_client.build_request('GET', url)
            faster_response = faster_client.send(faster_request)
            assert_response_ok(faster_response)
        
        # Compare responses
        assert_response_equivalence(httpx_response, faster_response)
    
    def test_client_all_http_methods(self, test_urls, sample_json_data):
        """Test all HTTP methods - compare httpx vs faster-http."""
        # Test each HTTP method
        methods_and_urls = [
            ('GET', test_urls['get']),
            ('POST', test_urls['post']),
            ('PUT', test_urls['put']),
            ('PATCH', test_urls['patch']),
            ('DELETE', test_urls['delete']),
            ('HEAD', test_urls['get']),
            ('OPTIONS', test_urls['get'])
        ]
        
        for method, url in methods_and_urls:
            kwargs = {}
            if method in ('POST', 'PUT', 'PATCH'):
                kwargs['json'] = sample_json_data
            
            # Test with httpx first
            with httpx.Client() as httpx_client:
                httpx_response = httpx_client.request(method, url, **kwargs)
                if method == 'HEAD':
                    assert httpx_response.status_code == 200
                    assert len(httpx_response.content) == 0
                else:
                    assert_response_ok(httpx_response)
            
            # Test with faster-http second
            with faster_http.Client() as faster_client:
                faster_response = faster_client.request(method, url, **kwargs)
                if method == 'HEAD':
                    assert faster_response.status_code == 200
                    assert len(faster_response.content) == 0
                else:
                    assert_response_ok(faster_response)
            
            # Compare responses
            assert httpx_response.status_code == faster_response.status_code


class TestAsyncClient:
    """Test asynchronous Client functionality by comparing with httpx."""
    
    @pytest.mark.asyncio
    async def test_async_client_basic_get(self, test_urls):
        """Test basic async client GET request - compare httpx vs faster-http."""
        # Test with httpx first
        async with httpx.AsyncClient() as httpx_client:
            httpx_response = await httpx_client.get(test_urls['get'])
            assert_response_ok(httpx_response)
        
        # Test with faster-http second
        async with faster_http.AsyncClient() as faster_client:
            faster_response = await faster_client.get(test_urls['get'])
            assert_response_ok(faster_response)
            assert_httpx_compatibility(faster_response)
        
        # Compare responses
        assert_response_equivalence(httpx_response, faster_response)
    
    @pytest.mark.asyncio
    async def test_async_client_with_base_url(self, test_urls):
        """Test async client with base URL - compare httpx vs faster-http."""
        base_url = test_urls['get'].rsplit('/', 1)[0]  # Use local test server
        
        # Test with httpx first
        async with httpx.AsyncClient(base_url=base_url) as httpx_client:
            httpx_response = await httpx_client.get('/get')
            assert_response_ok(httpx_response)
            assert '/get' in httpx_response.url
        
        # Test with faster-http second
        async with faster_http.AsyncClient(base_url=base_url) as faster_client:
            faster_response = await faster_client.get('/get')
            assert_response_ok(faster_response)
            assert '/get' in faster_response.url
        
        # Compare responses
        assert_response_equivalence(httpx_response, faster_response)
    
    @pytest.mark.asyncio
    async def test_async_client_concurrent_requests(self, test_urls):
        """Test concurrent async requests - compare httpx vs faster-http."""
        urls = [f"{test_urls['get']}?id={i}" for i in range(3)]
        
        # Test with httpx first
        async with httpx.AsyncClient() as httpx_client:
            httpx_tasks = [httpx_client.get(url) for url in urls]
            httpx_responses = await asyncio.gather(*httpx_tasks)
            
            for response in httpx_responses:
                assert_response_ok(response)
        
        # Test with faster-http second
        async with faster_http.AsyncClient() as faster_client:
            faster_tasks = [faster_client.get(url) for url in urls]
            faster_responses = await asyncio.gather(*faster_tasks)
            
            for response in faster_responses:
                assert_response_ok(response)
        
        # Compare response counts
        assert len(httpx_responses) == len(faster_responses)
        for httpx_resp, faster_resp in zip(httpx_responses, faster_responses):
            assert httpx_resp.status_code == faster_resp.status_code
    
    @pytest.mark.asyncio
    async def test_async_client_post_json(self, test_urls, sample_json_data):
        """Test async POST with JSON - compare httpx vs faster-http."""
        # Test with httpx first
        async with httpx.AsyncClient() as httpx_client:
            httpx_response = await httpx_client.post(test_urls['post'], json=sample_json_data)
            assert_response_ok(httpx_response)
            httpx_data = httpx_response.json()
            assert httpx_data['json'] == sample_json_data
        
        # Test with faster-http second
        async with faster_http.AsyncClient() as faster_client:
            faster_response = await faster_client.post(test_urls['post'], json=sample_json_data)
            assert_response_ok(faster_response)
            faster_data = faster_response.json()
            assert faster_data['json'] == sample_json_data
        
        # Compare JSON responses
        assert httpx_data['json'] == faster_data['json']
    
    @pytest.mark.asyncio
    async def test_async_client_all_methods(self, test_urls, sample_json_data):
        """Test all HTTP methods with async client - compare httpx vs faster-http."""
        methods_and_urls = [
            ('GET', test_urls['get']),
            ('POST', test_urls['post']),
            ('PUT', test_urls['put']),
            ('PATCH', test_urls['patch']),
            ('DELETE', test_urls['delete'])
        ]
        
        for method, url in methods_and_urls:
            kwargs = {}
            if method in ('POST', 'PUT', 'PATCH'):
                kwargs['json'] = sample_json_data
            
            # Test with httpx first
            async with httpx.AsyncClient() as httpx_client:
                httpx_response = await httpx_client.request(method, url, **kwargs)
                assert_response_ok(httpx_response)
            
            # Test with faster-http second
            async with faster_http.AsyncClient() as faster_client:
                faster_response = await faster_client.request(method, url, **kwargs)
                assert_response_ok(faster_response)
            
            # Compare responses
            assert httpx_response.status_code == faster_response.status_code


class TestClientConfiguration:
    """Test client configuration options by comparing with httpx."""
    
    def test_client_comprehensive_config(self, test_urls, sample_headers, sample_cookies):
        """Test client with comprehensive configuration - compare httpx vs faster-http."""
        base_url = test_urls['get'].rsplit('/', 1)[0]  # Use local test server
        config = {
            'base_url': base_url,
            'headers': sample_headers,
            'cookies': sample_cookies,
            'timeout': 30.0,
            'follow_redirects': True
        }
        
        # Test with httpx first
        with httpx.Client(**config) as httpx_client:
            httpx_response = httpx_client.get('/get')
            assert_response_ok(httpx_response)
        
        # Test with faster-http second
        with faster_http.Client(**config) as faster_client:
            faster_response = faster_client.get('/get')
            assert_response_ok(faster_response)
        
        # Compare responses
        assert_response_equivalence(httpx_response, faster_response)
    
    @pytest.mark.asyncio
    async def test_async_client_comprehensive_config(self, test_urls, sample_headers, sample_cookies):
        """Test async client with comprehensive configuration - compare httpx vs faster-http."""
        base_url = test_urls['get'].rsplit('/', 1)[0]  # Use local test server
        config = {
            'base_url': base_url,
            'headers': sample_headers,
            'cookies': sample_cookies,
            'timeout': 30.0,
            'follow_redirects': True
        }
        
        # Test with httpx first
        async with httpx.AsyncClient(**config) as httpx_client:
            httpx_response = await httpx_client.get('/get')
            assert_response_ok(httpx_response)
        
        # Test with faster-http second
        async with faster_http.AsyncClient(**config) as faster_client:
            faster_response = await faster_client.get('/get')
            assert_response_ok(faster_response)
        
        # Compare responses
        assert_response_equivalence(httpx_response, faster_response)