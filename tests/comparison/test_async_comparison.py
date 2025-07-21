"""
Asynchronous client comparison tests.
Direct comparison between httpx and faster-http for all asynchronous functionality.
"""

import pytest
import asyncio
import httpx
import faster_http
from ..conftest import assert_response_ok, assert_response_equivalence
from ..helpers.comparison import compare_async_request, compare_async_clients


class TestAsyncRequestComparison:
    """Direct comparison of async request functions."""
    
    @pytest.mark.asyncio
    async def test_async_get_comparison(self, test_urls):
        """Compare async GET requests between httpx and faster-http."""
        result = await compare_async_request('GET', test_urls['get'])
        result.assert_basic_compatibility()
        
        # Both should return JSON with same structure
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        # Check that both have expected keys
        assert 'url' in httpx_json
        assert 'url' in faster_json
        assert 'headers' in httpx_json
        assert 'headers' in faster_json
        assert 'origin' in httpx_json
        assert 'origin' in faster_json
    
    @pytest.mark.asyncio
    async def test_async_post_json_comparison(self, test_urls, sample_json_data):
        """Compare async POST JSON requests between httpx and faster-http."""
        result = await compare_async_request('POST', test_urls['post'], json=sample_json_data)
        result.assert_basic_compatibility()
        
        # Both should echo back the same JSON
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert httpx_json['json'] == sample_json_data
        assert faster_json['json'] == sample_json_data
        assert httpx_json['json'] == faster_json['json']
    
    @pytest.mark.asyncio
    async def test_async_post_form_comparison(self, test_urls, sample_form_data):
        """Compare async POST form data requests between httpx and faster-http."""
        result = await compare_async_request('POST', test_urls['post'], data=sample_form_data)
        result.assert_basic_compatibility()
        
        # Both should echo back the same form data
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert httpx_json['form'] == sample_form_data
        assert faster_json['form'] == sample_form_data
        assert httpx_json['form'] == faster_json['form']
    
    @pytest.mark.asyncio
    async def test_async_put_comparison(self, test_urls, sample_json_data):
        """Compare async PUT requests between httpx and faster-http."""
        result = await compare_async_request('PUT', test_urls['put'], json=sample_json_data)
        result.assert_basic_compatibility()
        
        # Both should handle PUT request identically
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert httpx_json['json'] == sample_json_data
        assert faster_json['json'] == sample_json_data
    
    @pytest.mark.asyncio
    async def test_async_patch_comparison(self, test_urls):
        """Compare async PATCH requests between httpx and faster-http."""
        patch_data = {'patched': 'field', 'value': 'updated'}
        result = await compare_async_request('PATCH', test_urls['patch'], json=patch_data)
        result.assert_basic_compatibility()
        
        # Both should handle PATCH request identically
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert httpx_json['json'] == patch_data
        assert faster_json['json'] == patch_data
    
    @pytest.mark.asyncio
    async def test_async_delete_comparison(self, test_urls):
        """Compare async DELETE requests between httpx and faster-http."""
        result = await compare_async_request('DELETE', test_urls['delete'])
        result.assert_basic_compatibility()
        
        # Both should handle DELETE request identically
        assert result.httpx_result.status_code == 200
        assert result.faster_http_result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_async_head_comparison(self, test_urls):
        """Compare async HEAD requests between httpx and faster-http."""
        result = await compare_async_request('HEAD', test_urls['get'])
        
        # Both should return 200 with no content
        assert result.httpx_result.status_code == 200
        assert result.faster_http_result.status_code == 200
        assert len(result.httpx_result.content) == 0
        assert len(result.faster_http_result.content) == 0
    
    @pytest.mark.asyncio
    async def test_async_options_comparison(self, test_urls):
        """Compare async OPTIONS requests between httpx and faster-http."""
        result = await compare_async_request('OPTIONS', test_urls['get'])
        
        # Both should return 200
        assert result.httpx_result.status_code == 200
        assert result.faster_http_result.status_code == 200


class TestAsyncParameterComparison:
    """Compare async request parameters between httpx and faster-http."""
    
    @pytest.mark.asyncio
    async def test_async_params_comparison(self, test_urls, sample_params):
        """Compare async query parameters between httpx and faster-http."""
        result = await compare_async_request('GET', test_urls['get'], params=sample_params)
        result.assert_basic_compatibility()
        
        # Both should include same query parameters
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        for key, value in sample_params.items():
            assert httpx_json['args'][key] == value
            assert faster_json['args'][key] == value
    
    @pytest.mark.asyncio
    async def test_async_headers_comparison(self, test_urls, sample_headers):
        """Compare async custom headers between httpx and faster-http."""
        result = await compare_async_request('GET', test_urls['get'], headers=sample_headers)
        result.assert_basic_compatibility()
        
        # Both should include same headers
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        for key, value in sample_headers.items():
            assert httpx_json['headers'][key] == value
            assert faster_json['headers'][key] == value
    
    @pytest.mark.asyncio
    async def test_async_cookies_comparison(self, test_urls, sample_cookies):
        """Compare async cookies between httpx and faster-http."""
        result = await compare_async_request('GET', test_urls['cookies'], cookies=sample_cookies)
        result.assert_basic_compatibility()
        
        # Both should include same cookies
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        for key, value in sample_cookies.items():
            assert httpx_json['cookies'][key] == value
            assert faster_json['cookies'][key] == value
    
    @pytest.mark.asyncio
    async def test_async_files_comparison(self, test_urls, sample_files):
        """Compare async file uploads between httpx and faster-http."""
        result = await compare_async_request('POST', test_urls['post'], files=sample_files)
        result.assert_basic_compatibility()
        
        # Both should handle file uploads
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert 'files' in httpx_json
        assert 'files' in faster_json
        # File content should be uploaded
        for filename in sample_files.keys():
            assert filename in httpx_json['files']
            assert filename in faster_json['files']
    
    @pytest.mark.asyncio
    async def test_async_timeout_comparison(self, test_urls):
        """Compare async timeout parameter between httpx and faster-http."""
        timeout = 30.0
        result = await compare_async_request('GET', test_urls['get'], timeout=timeout)
        result.assert_basic_compatibility()
        
        # Both should complete within timeout
        assert result.httpx_result.elapsed < timeout
        assert result.faster_http_result.elapsed < timeout
    
    @pytest.mark.asyncio
    async def test_async_follow_redirects_comparison(self, test_urls):
        """Compare async redirect following between httpx and faster-http."""
        # Test with redirects followed
        result_follow = await compare_async_request('GET', test_urls['redirect'].format(n=1), follow_redirects=True)
        result_follow.assert_basic_compatibility()
        
        # Both should follow redirect and return 200
        assert result_follow.httpx_result.status_code == 200
        assert result_follow.faster_http_result.status_code == 200
        assert '/get' in result_follow.httpx_result.url
        assert '/get' in result_follow.faster_http_result.url
        
        # Test without redirects
        result_no_follow = await compare_async_request('GET', test_urls['redirect'].format(n=1), follow_redirects=False)
        
        # Both should return redirect status
        assert result_no_follow.httpx_result.status_code in [301, 302, 307, 308]
        assert result_no_follow.faster_http_result.status_code in [301, 302, 307, 308]
        assert result_no_follow.httpx_result.is_redirect
        assert result_no_follow.faster_http_result.is_redirect


class TestAsyncClientComparison:
    """Compare async client functionality between httpx and faster-http."""
    
    @pytest.mark.asyncio
    async def test_async_client_basic_comparison(self, test_urls):
        """Compare basic async client usage between httpx and faster-http."""
        result = await compare_async_clients('GET', test_urls['get'])
        result.assert_basic_compatibility()
        
        # Both should return same JSON structure
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert 'url' in httpx_json
        assert 'url' in faster_json
    
    @pytest.mark.asyncio
    async def test_async_client_base_url_comparison(self, test_urls):
        """Compare async client base URL between httpx and faster-http."""
        base_url = test_urls['get'].rsplit('/', 1)[0]  # Use local test server
        client_kwargs = {'base_url': base_url}
        result = await compare_async_clients('GET', '/get', client_kwargs=client_kwargs)
        result.assert_basic_compatibility()
        
        # Both should resolve relative URL correctly
        assert '/get' in result.httpx_result.url
        assert '/get' in result.faster_http_result.url
    
    @pytest.mark.asyncio
    async def test_async_client_headers_comparison(self, test_urls, sample_headers):
        """Compare async client default headers between httpx and faster-http."""
        headers = {'User-Agent': 'async-test-client/1.0', 'X-Custom': 'async-value'}
        client_kwargs = {'headers': headers}
        result = await compare_async_clients('GET', test_urls['get'], client_kwargs=client_kwargs)
        result.assert_basic_compatibility()
        
        # Both should include default headers
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert httpx_json['headers']['User-Agent'] == 'async-test-client/1.0'
        assert faster_json['headers']['User-Agent'] == 'async-test-client/1.0'
        assert httpx_json['headers']['X-Custom'] == 'async-value'
        assert faster_json['headers']['X-Custom'] == 'async-value'
    
    @pytest.mark.asyncio
    async def test_async_client_cookies_comparison(self, test_urls, sample_cookies):
        """Compare async client default cookies between httpx and faster-http."""
        cookies = {'async_session': 'xyz789', 'async_user': 'asyncuser'}
        client_kwargs = {'cookies': cookies}
        result = await compare_async_clients('GET', test_urls['cookies'], client_kwargs=client_kwargs)
        result.assert_basic_compatibility()
        
        # Both should include default cookies
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert httpx_json['cookies']['async_session'] == 'xyz789'
        assert faster_json['cookies']['async_session'] == 'xyz789'
        assert httpx_json['cookies']['async_user'] == 'asyncuser'
        assert faster_json['cookies']['async_user'] == 'asyncuser'
    
    @pytest.mark.asyncio
    async def test_async_client_timeout_comparison(self, test_urls):
        """Compare async client timeout configuration between httpx and faster-http."""
        timeout = 30.0
        client_kwargs = {'timeout': timeout}
        result = await compare_async_clients('GET', test_urls['get'], client_kwargs=client_kwargs)
        result.assert_basic_compatibility()
        
        # Both should complete within timeout
        assert result.httpx_result.elapsed < timeout
        assert result.faster_http_result.elapsed < timeout
    
    @pytest.mark.asyncio
    async def test_async_client_comprehensive_config_comparison(self, test_urls, sample_headers, sample_cookies):
        """Compare comprehensive async client configuration between httpx and faster-http."""
        base_url = test_urls['get'].rsplit('/', 1)[0]  # Use local test server
        client_kwargs = {
            'base_url': base_url,
            'headers': sample_headers,
            'cookies': sample_cookies,
            'timeout': 30.0,
            'follow_redirects': True
        }
        result = await compare_async_clients('GET', '/get', client_kwargs=client_kwargs)
        result.assert_basic_compatibility()
        
        # Both should handle comprehensive configuration
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        # Check that configuration is applied
        assert '/get' in result.httpx_result.url
        assert '/get' in result.faster_http_result.url
        assert result.httpx_result.elapsed < 30.0
        assert result.faster_http_result.elapsed < 30.0


class TestAsyncConcurrencyComparison:
    """Compare async concurrency between httpx and faster-http."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_comparison(self, test_urls):
        """Compare concurrent requests between httpx and faster-http."""
        urls = [f"{test_urls['get']}?id={i}" for i in range(5)]
        
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
        
        # Compare response counts and status codes
        assert len(httpx_responses) == len(faster_responses)
        for httpx_resp, faster_resp in zip(httpx_responses, faster_responses):
            assert httpx_resp.status_code == faster_resp.status_code
    
    @pytest.mark.asyncio
    async def test_concurrent_mixed_methods_comparison(self, test_urls, sample_json_data):
        """Compare concurrent mixed HTTP methods between httpx and faster-http."""
        # Define mixed requests
        requests = [
            ('GET', test_urls['get']),
            ('POST', test_urls['post'], {'json': sample_json_data}),
            ('PUT', test_urls['put'], {'json': sample_json_data}),
            ('PATCH', test_urls['patch'], {'json': sample_json_data}),
            ('DELETE', test_urls['delete'])
        ]
        
        # Test with httpx first
        async with httpx.AsyncClient() as httpx_client:
            httpx_tasks = []
            for method, url, *args in requests:
                kwargs = args[0] if args else {}
                httpx_tasks.append(httpx_client.request(method, url, **kwargs))
            
            httpx_responses = await asyncio.gather(*httpx_tasks)
            
            for response in httpx_responses:
                assert_response_ok(response)
        
        # Test with faster-http second
        async with faster_http.AsyncClient() as faster_client:
            faster_tasks = []
            for method, url, *args in requests:
                kwargs = args[0] if args else {}
                faster_tasks.append(faster_client.request(method, url, **kwargs))
            
            faster_responses = await asyncio.gather(*faster_tasks)
            
            for response in faster_responses:
                assert_response_ok(response)
        
        # Compare response counts and status codes
        assert len(httpx_responses) == len(faster_responses)
        for httpx_resp, faster_resp in zip(httpx_responses, faster_responses):
            assert httpx_resp.status_code == faster_resp.status_code
    
    @pytest.mark.asyncio
    async def test_semaphore_limited_concurrency_comparison(self, test_urls):
        """Compare semaphore-limited concurrency between httpx and faster-http."""
        urls = [f"{test_urls['get']}?id={i}" for i in range(10)]
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent requests
        
        async def limited_request_httpx(url):
            async with semaphore:
                async with httpx.AsyncClient() as client:
                    return await client.get(url)
        
        async def limited_request_faster(url):
            async with semaphore:
                async with faster_http.AsyncClient() as client:
                    return await client.get(url)
        
        # Test with httpx first
        httpx_tasks = [limited_request_httpx(url) for url in urls]
        httpx_responses = await asyncio.gather(*httpx_tasks)
        
        for response in httpx_responses:
            assert_response_ok(response)
        
        # Test with faster-http second
        faster_tasks = [limited_request_faster(url) for url in urls]
        faster_responses = await asyncio.gather(*faster_tasks)
        
        for response in faster_responses:
            assert_response_ok(response)
        
        # Compare response counts and status codes
        assert len(httpx_responses) == len(faster_responses)
        for httpx_resp, faster_resp in zip(httpx_responses, faster_responses):
            assert httpx_resp.status_code == faster_resp.status_code


class TestAsyncErrorHandlingComparison:
    """Compare async error handling between httpx and faster-http."""
    
    @pytest.mark.asyncio
    async def test_async_http_error_comparison(self, test_urls):
        """Compare async HTTP error handling between httpx and faster-http."""
        # Test 404 error
        result = await compare_async_request('GET', test_urls['status'].format(code=404))
        
        # Both should return 404
        assert result.httpx_result.status_code == 404
        assert result.faster_http_result.status_code == 404
        assert not result.httpx_result.ok
        assert not result.faster_http_result.ok
        assert result.httpx_result.is_client_error
        assert result.faster_http_result.is_client_error
        
        # Test 500 error
        result = await compare_async_request('GET', test_urls['status'].format(code=500))
        
        # Both should return 500
        assert result.httpx_result.status_code == 500
        assert result.faster_http_result.status_code == 500
        assert not result.httpx_result.ok
        assert not result.faster_http_result.ok
        assert result.httpx_result.is_server_error
        assert result.faster_http_result.is_server_error
    
    @pytest.mark.asyncio
    async def test_async_raise_for_status_comparison(self, test_urls):
        """Compare async raise_for_status behavior between httpx and faster-http."""
        # Test successful response
        result = await compare_async_request('GET', test_urls['get'])
        result.assert_basic_compatibility()
        
        # Both should not raise
        result.httpx_result.raise_for_status()
        result.faster_http_result.raise_for_status()
        
        # Test error response
        result = await compare_async_request('GET', test_urls['status'].format(code=404))
        
        # Both should raise
        with pytest.raises(httpx.HTTPStatusError):
            result.httpx_result.raise_for_status()
        
        with pytest.raises(faster_http.HTTPError):
            result.faster_http_result.raise_for_status()
    
    @pytest.mark.asyncio
    async def test_async_connection_error_comparison(self):
        """Compare async connection error handling between httpx and faster-http."""
        # Test connection to non-existent server
        invalid_url = 'http://127.0.0.1:99999'
        timeout = 1.0
        
        # Both should raise connection errors
        with pytest.raises((httpx.ConnectError, httpx.RequestError)):
            async with httpx.AsyncClient() as client:
                await client.get(invalid_url, timeout=timeout)
        
        with pytest.raises((faster_http.ConnectTimeout, faster_http.RequestError)):
            async with faster_http.AsyncClient() as client:
                await client.get(invalid_url, timeout=timeout)
    
    @pytest.mark.asyncio
    async def test_async_timeout_error_comparison(self, test_urls):
        """Compare async timeout error handling between httpx and faster-http."""
        # Test timeout with slow endpoint
        timeout = 1.0
        
        # Both should raise timeout errors
        with pytest.raises((httpx.ReadTimeout, httpx.TimeoutException)):
            async with httpx.AsyncClient() as client:
                await client.get(test_urls['delay'].format(seconds=5), timeout=timeout)
        
        with pytest.raises((faster_http.ReadTimeout, faster_http.RequestError)):
            async with faster_http.AsyncClient() as client:
                await client.get(test_urls['delay'].format(seconds=5), timeout=timeout)
    
    @pytest.mark.asyncio
    async def test_async_cancelled_request_comparison(self, test_urls):
        """Compare async cancelled request handling between httpx and faster-http."""
        # Test with httpx first
        async with httpx.AsyncClient() as httpx_client:
            task = asyncio.create_task(httpx_client.get(test_urls['delay'].format(seconds=5)))
            await asyncio.sleep(0.1)  # Let the request start
            task.cancel()
            
            with pytest.raises(asyncio.CancelledError):
                await task
        
        # Test with faster-http second
        async with faster_http.AsyncClient() as faster_client:
            task = asyncio.create_task(faster_client.get(test_urls['delay'].format(seconds=5)))
            await asyncio.sleep(0.1)  # Let the request start
            task.cancel()
            
            with pytest.raises(asyncio.CancelledError):
                await task