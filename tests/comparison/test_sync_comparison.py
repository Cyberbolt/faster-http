"""
Synchronous client comparison tests.
Direct comparison between httpx and faster-http for all synchronous functionality.
"""

import pytest
import httpx
import faster_http
from ..conftest import assert_response_ok, assert_response_equivalence
from ..helpers.comparison import compare_sync_request, compare_sync_clients


class TestSyncRequestComparison:
    """Direct comparison of sync request functions."""
    
    def test_get_request_comparison(self, test_urls):
        """Compare GET requests between httpx and faster-http."""
        result = compare_sync_request('GET', test_urls['get'])
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
    
    def test_post_json_comparison(self, test_urls, sample_json_data):
        """Compare POST JSON requests between httpx and faster-http."""
        result = compare_sync_request('POST', test_urls['post'], json=sample_json_data)
        result.assert_basic_compatibility()
        
        # Both should echo back the same JSON
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert httpx_json['json'] == sample_json_data
        assert faster_json['json'] == sample_json_data
        assert httpx_json['json'] == faster_json['json']
    
    def test_post_form_data_comparison(self, test_urls, sample_form_data):
        """Compare POST form data requests between httpx and faster-http."""
        result = compare_sync_request('POST', test_urls['post'], data=sample_form_data)
        result.assert_basic_compatibility()
        
        # Both should echo back the same form data
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert httpx_json['form'] == sample_form_data
        assert faster_json['form'] == sample_form_data
        assert httpx_json['form'] == faster_json['form']
    
    def test_put_request_comparison(self, test_urls, sample_json_data):
        """Compare PUT requests between httpx and faster-http."""
        result = compare_sync_request('PUT', test_urls['put'], json=sample_json_data)
        result.assert_basic_compatibility()
        
        # Both should handle PUT request identically
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert httpx_json['json'] == sample_json_data
        assert faster_json['json'] == sample_json_data
    
    def test_patch_request_comparison(self, test_urls):
        """Compare PATCH requests between httpx and faster-http."""
        patch_data = {'patched': 'field', 'value': 'updated'}
        result = compare_sync_request('PATCH', test_urls['patch'], json=patch_data)
        result.assert_basic_compatibility()
        
        # Both should handle PATCH request identically
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert httpx_json['json'] == patch_data
        assert faster_json['json'] == patch_data
    
    def test_delete_request_comparison(self, test_urls):
        """Compare DELETE requests between httpx and faster-http."""
        result = compare_sync_request('DELETE', test_urls['delete'])
        result.assert_basic_compatibility()
        
        # Both should handle DELETE request identically
        assert result.httpx_result.status_code == 200
        assert result.faster_http_result.status_code == 200
    
    def test_head_request_comparison(self, test_urls):
        """Compare HEAD requests between httpx and faster-http."""
        result = compare_sync_request('HEAD', test_urls['get'])
        
        # Both should return 200 with no content
        assert result.httpx_result.status_code == 200
        assert result.faster_http_result.status_code == 200
        assert len(result.httpx_result.content) == 0
        assert len(result.faster_http_result.content) == 0
    
    def test_options_request_comparison(self, test_urls):
        """Compare OPTIONS requests between httpx and faster-http."""
        result = compare_sync_request('OPTIONS', test_urls['get'])
        
        # Both should return 200
        assert result.httpx_result.status_code == 200
        assert result.faster_http_result.status_code == 200


class TestSyncParameterComparison:
    """Compare request parameters between httpx and faster-http."""
    
    def test_params_comparison(self, test_urls, sample_params):
        """Compare query parameters between httpx and faster-http."""
        result = compare_sync_request('GET', test_urls['get'], params=sample_params)
        result.assert_basic_compatibility()
        
        # Both should include same query parameters
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        for key, value in sample_params.items():
            assert httpx_json['args'][key] == value
            assert faster_json['args'][key] == value
    
    def test_headers_comparison(self, test_urls, sample_headers):
        """Compare custom headers between httpx and faster-http."""
        result = compare_sync_request('GET', test_urls['get'], headers=sample_headers)
        result.assert_basic_compatibility()
        
        # Both should include same headers
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        for key, value in sample_headers.items():
            assert httpx_json['headers'][key] == value
            assert faster_json['headers'][key] == value
    
    def test_cookies_comparison(self, test_urls, sample_cookies):
        """Compare cookies between httpx and faster-http."""
        result = compare_sync_request('GET', test_urls['cookies'], cookies=sample_cookies)
        result.assert_basic_compatibility()
        
        # Both should include same cookies
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        for key, value in sample_cookies.items():
            assert httpx_json['cookies'][key] == value
            assert faster_json['cookies'][key] == value
    
    def test_files_comparison(self, test_urls, sample_files):
        """Compare file uploads between httpx and faster-http."""
        result = compare_sync_request('POST', test_urls['post'], files=sample_files)
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
    
    def test_timeout_comparison(self, test_urls):
        """Compare timeout parameter between httpx and faster-http."""
        timeout = 30.0
        result = compare_sync_request('GET', test_urls['get'], timeout=timeout)
        result.assert_basic_compatibility()
        
        # Both should complete within timeout
        assert result.httpx_result.elapsed < timeout
        assert result.faster_http_result.elapsed < timeout
    
    def test_follow_redirects_comparison(self, test_urls):
        """Compare redirect following between httpx and faster-http."""
        # Test with redirects followed
        result_follow = compare_sync_request('GET', test_urls['redirect'].format(n=1), follow_redirects=True)
        result_follow.assert_basic_compatibility()
        
        # Both should follow redirect and return 200
        assert result_follow.httpx_result.status_code == 200
        assert result_follow.faster_http_result.status_code == 200
        assert '/get' in result_follow.httpx_result.url
        assert '/get' in result_follow.faster_http_result.url
        
        # Test without redirects
        result_no_follow = compare_sync_request('GET', test_urls['redirect'].format(n=1), follow_redirects=False)
        
        # Both should return redirect status
        assert result_no_follow.httpx_result.status_code in [301, 302, 307, 308]
        assert result_no_follow.faster_http_result.status_code in [301, 302, 307, 308]
        assert result_no_follow.httpx_result.is_redirect
        assert result_no_follow.faster_http_result.is_redirect


class TestSyncClientComparison:
    """Compare sync client functionality between httpx and faster-http."""
    
    def test_client_basic_comparison(self, test_urls):
        """Compare basic client usage between httpx and faster-http."""
        result = compare_sync_clients('GET', test_urls['get'])
        result.assert_basic_compatibility()
        
        # Both should return same JSON structure
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert 'url' in httpx_json
        assert 'url' in faster_json
    
    def test_client_base_url_comparison(self, test_urls):
        """Compare client base URL between httpx and faster-http."""
        base_url = test_urls['get'].rsplit('/', 1)[0]  # Use local test server
        client_kwargs = {'base_url': base_url}
        result = compare_sync_clients('GET', '/get', client_kwargs=client_kwargs)
        result.assert_basic_compatibility()
        
        # Both should resolve relative URL correctly
        assert '/get' in result.httpx_result.url
        assert '/get' in result.faster_http_result.url
    
    def test_client_headers_comparison(self, test_urls, sample_headers):
        """Compare client default headers between httpx and faster-http."""
        headers = {'User-Agent': 'test-client/1.0', 'X-Custom': 'value'}
        client_kwargs = {'headers': headers}
        result = compare_sync_clients('GET', test_urls['get'], client_kwargs=client_kwargs)
        result.assert_basic_compatibility()
        
        # Both should include default headers
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert httpx_json['headers']['User-Agent'] == 'test-client/1.0'
        assert faster_json['headers']['User-Agent'] == 'test-client/1.0'
        assert httpx_json['headers']['X-Custom'] == 'value'
        assert faster_json['headers']['X-Custom'] == 'value'
    
    def test_client_cookies_comparison(self, test_urls, sample_cookies):
        """Compare client default cookies between httpx and faster-http."""
        cookies = {'session': 'abc123', 'user': 'testuser'}
        client_kwargs = {'cookies': cookies}
        result = compare_sync_clients('GET', test_urls['cookies'], client_kwargs=client_kwargs)
        result.assert_basic_compatibility()
        
        # Both should include default cookies
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        assert httpx_json['cookies']['session'] == 'abc123'
        assert faster_json['cookies']['session'] == 'abc123'
        assert httpx_json['cookies']['user'] == 'testuser'
        assert faster_json['cookies']['user'] == 'testuser'
    
    def test_client_timeout_comparison(self, test_urls):
        """Compare client timeout configuration between httpx and faster-http."""
        timeout = 30.0
        client_kwargs = {'timeout': timeout}
        result = compare_sync_clients('GET', test_urls['get'], client_kwargs=client_kwargs)
        result.assert_basic_compatibility()
        
        # Both should complete within timeout
        assert result.httpx_result.elapsed < timeout
        assert result.faster_http_result.elapsed < timeout
    
    def test_client_comprehensive_config_comparison(self, test_urls, sample_headers, sample_cookies):
        """Compare comprehensive client configuration between httpx and faster-http."""
        base_url = test_urls['get'].rsplit('/', 1)[0]  # Use local test server
        client_kwargs = {
            'base_url': base_url,
            'headers': sample_headers,
            'cookies': sample_cookies,
            'timeout': 30.0,
            'follow_redirects': True
        }
        result = compare_sync_clients('GET', '/get', client_kwargs=client_kwargs)
        result.assert_basic_compatibility()
        
        # Both should handle comprehensive configuration
        httpx_json = result.httpx_result.json()
        faster_json = result.faster_http_result.json()
        
        # Check that configuration is applied
        assert '/get' in result.httpx_result.url
        assert '/get' in result.faster_http_result.url
        assert result.httpx_result.elapsed < 30.0
        assert result.faster_http_result.elapsed < 30.0


class TestSyncErrorHandlingComparison:
    """Compare error handling between httpx and faster-http."""
    
    def test_http_error_comparison(self, test_urls):
        """Compare HTTP error handling between httpx and faster-http."""
        # Test 404 error
        result = compare_sync_request('GET', test_urls['status'].format(code=404))
        
        # Both should return 404
        assert result.httpx_result.status_code == 404
        assert result.faster_http_result.status_code == 404
        assert not result.httpx_result.ok
        assert not result.faster_http_result.ok
        assert result.httpx_result.is_client_error
        assert result.faster_http_result.is_client_error
        
        # Test 500 error
        result = compare_sync_request('GET', test_urls['status'].format(code=500))
        
        # Both should return 500
        assert result.httpx_result.status_code == 500
        assert result.faster_http_result.status_code == 500
        assert not result.httpx_result.ok
        assert not result.faster_http_result.ok
        assert result.httpx_result.is_server_error
        assert result.faster_http_result.is_server_error
    
    def test_raise_for_status_comparison(self, test_urls):
        """Compare raise_for_status behavior between httpx and faster-http."""
        # Test successful response
        result = compare_sync_request('GET', test_urls['get'])
        result.assert_basic_compatibility()
        
        # Both should not raise
        result.httpx_result.raise_for_status()
        result.faster_http_result.raise_for_status()
        
        # Test error response
        result = compare_sync_request('GET', test_urls['status'].format(code=404))
        
        # Both should raise
        with pytest.raises(httpx.HTTPStatusError):
            result.httpx_result.raise_for_status()
        
        with pytest.raises(faster_http.HTTPError):
            result.faster_http_result.raise_for_status()
    
    def test_connection_error_comparison(self):
        """Compare connection error handling between httpx and faster-http."""
        # Test connection to non-existent server
        invalid_url = 'http://127.0.0.1:99999'
        timeout = 1.0
        
        # Both should raise connection errors
        with pytest.raises((httpx.ConnectError, httpx.RequestError)):
            httpx.get(invalid_url, timeout=timeout)
        
        with pytest.raises((faster_http.ConnectTimeout, faster_http.RequestError)):
            faster_http.get(invalid_url, timeout=timeout)
    
    def test_timeout_error_comparison(self, test_urls):
        """Compare timeout error handling between httpx and faster-http."""
        # Test timeout with slow endpoint
        timeout = 1.0
        
        # Both should raise timeout errors
        with pytest.raises((httpx.ReadTimeout, httpx.TimeoutException)):
            httpx.get(test_urls['delay'].format(seconds=5), timeout=timeout)
        
        with pytest.raises((faster_http.ReadTimeout, faster_http.RequestError)):
            faster_http.get(test_urls['delay'].format(seconds=5), timeout=timeout)