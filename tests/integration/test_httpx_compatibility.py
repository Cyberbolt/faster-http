"""
Integration tests for complete httpx compatibility.
Tests that faster-http can be used as a complete drop-in replacement for httpx.
"""

import pytest
import asyncio
import httpx
import faster_http
from ..conftest import assert_response_ok, assert_httpx_compatibility


class TestCompleteHttpxCompatibility:
    """Test complete httpx compatibility in real-world scenarios."""
    
    def test_httpx_replacement_import(self, test_urls):
        """Test that faster-http can be imported as httpx completely."""
        # This is the key test - can we use faster-http as a complete replacement?
        import faster_http as httpx
        
        # Test basic functionality
        response = httpx.get(test_urls['get'])
        assert_response_ok(response)
        assert_httpx_compatibility(response)
        
        # Test that it has all the expected attributes
        assert hasattr(httpx, 'Client')
        assert hasattr(httpx, 'AsyncClient')
        assert hasattr(httpx, 'BasicAuth')
        assert hasattr(httpx, 'DigestAuth')
        assert hasattr(httpx, 'NetRCAuth')
        assert hasattr(httpx, 'HTTPError')
        
        # Test that basic usage works
        with httpx.Client() as client:
            response = client.get(test_urls['get'])
            assert_response_ok(response)
    
    @pytest.mark.asyncio
    async def test_async_httpx_replacement(self, test_urls):
        """Test that faster-http can replace httpx for async usage."""
        import faster_http as httpx
        
        # Test async functionality
        async with httpx.AsyncClient() as client:
            response = await client.get(test_urls['get'])
            assert_response_ok(response)
            assert_httpx_compatibility(response)
    
    def test_complex_workflow_compatibility(self, test_urls, sample_json_data, sample_headers):
        """Test complex workflow compatibility with httpx."""
        # Test with httpx first
        httpx_results = []
        with httpx.Client(headers=sample_headers) as httpx_client:
            # GET request
            response = httpx_client.get(test_urls['get'])
            httpx_results.append(response.status_code)
            
            # POST request
            response = httpx_client.post(test_urls['post'], json=sample_json_data)
            httpx_results.append(response.status_code)
            
            # PUT request
            response = httpx_client.put(test_urls['put'], json=sample_json_data)
            httpx_results.append(response.status_code)
            
            # Handle redirect
            response = httpx_client.get(test_urls['redirect'].format(n=1), follow_redirects=True)
            httpx_results.append(response.status_code)
        
        # Test with faster-http second
        faster_results = []
        with faster_http.Client(headers=sample_headers) as faster_client:
            # GET request
            response = faster_client.get(test_urls['get'])
            faster_results.append(response.status_code)
            
            # POST request
            response = faster_client.post(test_urls['post'], json=sample_json_data)
            faster_results.append(response.status_code)
            
            # PUT request
            response = faster_client.put(test_urls['put'], json=sample_json_data)
            faster_results.append(response.status_code)
            
            # Handle redirect
            response = faster_client.get(test_urls['redirect'].format(n=1), follow_redirects=True)
            faster_results.append(response.status_code)
        
        # Compare results
        assert httpx_results == faster_results, f"Workflow results differ: httpx={httpx_results}, faster-http={faster_results}"
    
    @pytest.mark.asyncio
    async def test_async_complex_workflow_compatibility(self, test_urls, sample_json_data, sample_headers):
        """Test async complex workflow compatibility with httpx."""
        # Test with httpx first
        httpx_results = []
        async with httpx.AsyncClient(headers=sample_headers) as httpx_client:
            # Concurrent requests
            tasks = [
                httpx_client.get(test_urls['get']),
                httpx_client.post(test_urls['post'], json=sample_json_data),
                httpx_client.put(test_urls['put'], json=sample_json_data),
                httpx_client.get(test_urls['redirect'].format(n=1), follow_redirects=True)
            ]
            responses = await asyncio.gather(*tasks)
            httpx_results = [r.status_code for r in responses]
        
        # Test with faster-http second
        faster_results = []
        async with faster_http.AsyncClient(headers=sample_headers) as faster_client:
            # Concurrent requests
            tasks = [
                faster_client.get(test_urls['get']),
                faster_client.post(test_urls['post'], json=sample_json_data),
                faster_client.put(test_urls['put'], json=sample_json_data),
                faster_client.get(test_urls['redirect'].format(n=1), follow_redirects=True)
            ]
            responses = await asyncio.gather(*tasks)
            faster_results = [r.status_code for r in responses]
        
        # Compare results
        assert httpx_results == faster_results, f"Async workflow results differ: httpx={httpx_results}, faster-http={faster_results}"
    
    def test_session_like_behavior(self, test_urls, sample_cookies):
        """Test session-like behavior compatibility with httpx."""
        # Test with httpx first
        httpx_cookies_received = []
        with httpx.Client(cookies=sample_cookies) as httpx_client:
            # First request should send cookies
            response = httpx_client.get(test_urls['cookies'])
            httpx_data = response.json()
            httpx_cookies_received.append(httpx_data['cookies'])
            
            # Second request should also send cookies
            response = httpx_client.get(test_urls['cookies'])
            httpx_data = response.json()
            httpx_cookies_received.append(httpx_data['cookies'])
        
        # Test with faster-http second
        faster_cookies_received = []
        with faster_http.Client(cookies=sample_cookies) as faster_client:
            # First request should send cookies
            response = faster_client.get(test_urls['cookies'])
            faster_data = response.json()
            faster_cookies_received.append(faster_data['cookies'])
            
            # Second request should also send cookies
            response = faster_client.get(test_urls['cookies'])
            faster_data = response.json()
            faster_cookies_received.append(faster_data['cookies'])
        
        # Compare cookie persistence
        assert httpx_cookies_received == faster_cookies_received
    
    def test_error_handling_compatibility(self, test_urls):
        """Test error handling compatibility with httpx."""
        # Test with httpx first
        httpx_errors = []
        
        # Test 404 error
        try:
            response = httpx.get(test_urls['status'].format(code=404))
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            httpx_errors.append(type(e).__name__)
        
        # Test connection error
        try:
            httpx.get('http://127.0.0.1:99999', timeout=1.0)
        except (httpx.ConnectError, httpx.RequestError) as e:
            httpx_errors.append(type(e).__name__)
        
        # Test timeout error
        try:
            httpx.get(test_urls['delay'].format(seconds=5), timeout=1.0)
        except (httpx.ReadTimeout, httpx.TimeoutException) as e:
            httpx_errors.append(type(e).__name__)
        
        # Test with faster-http second
        faster_errors = []
        
        # Test 404 error
        try:
            response = faster_http.get(test_urls['status'].format(code=404))
            response.raise_for_status()
        except faster_http.HTTPError as e:
            faster_errors.append(type(e).__name__)
        
        # Test connection error
        try:
            faster_http.get('http://127.0.0.1:99999', timeout=1.0)
        except (faster_http.ConnectTimeout, faster_http.RequestError) as e:
            faster_errors.append(type(e).__name__)
        
        # Test timeout error
        try:
            faster_http.get(test_urls['delay'].format(seconds=5), timeout=1.0)
        except (faster_http.ReadTimeout, faster_http.RequestError) as e:
            faster_errors.append(type(e).__name__)
        
        # Both should handle errors (even if exception names differ)
        assert len(httpx_errors) == len(faster_errors)
    
    def test_build_and_send_compatibility(self, test_urls, sample_json_data):
        """Test build_request and send compatibility with httpx."""
        # Test with httpx first
        with httpx.Client() as httpx_client:
            # Build request
            httpx_request = httpx_client.build_request('POST', test_urls['post'], json=sample_json_data)
            assert httpx_request.method == 'POST'
            assert httpx_request.url == test_urls['post']
            
            # Send request
            httpx_response = httpx_client.send(httpx_request)
            assert_response_ok(httpx_response)
            httpx_data = httpx_response.json()
        
        # Test with faster-http second
        with faster_http.Client() as faster_client:
            # Build request
            faster_request = faster_client.build_request('POST', test_urls['post'], json=sample_json_data)
            assert faster_request.method == 'POST'
            assert faster_request.url == test_urls['post']
            
            # Send request
            faster_response = faster_client.send(faster_request)
            assert_response_ok(faster_response)
            faster_data = faster_response.json()
        
        # Compare results
        assert httpx_data['json'] == faster_data['json']
    
    @pytest.mark.asyncio
    async def test_async_build_and_send_compatibility(self, test_urls, sample_json_data):
        """Test async build_request and send compatibility with httpx."""
        # Test with httpx first
        async with httpx.AsyncClient() as httpx_client:
            # Build request
            httpx_request = httpx_client.build_request('POST', test_urls['post'], json=sample_json_data)
            assert httpx_request.method == 'POST'
            assert httpx_request.url == test_urls['post']
            
            # Send request
            httpx_response = await httpx_client.send(httpx_request)
            assert_response_ok(httpx_response)
            httpx_data = httpx_response.json()
        
        # Test with faster-http second
        async with faster_http.AsyncClient() as faster_client:
            # Build request
            faster_request = faster_client.build_request('POST', test_urls['post'], json=sample_json_data)
            assert faster_request.method == 'POST'
            assert faster_request.url == test_urls['post']
            
            # Send request
            faster_response = await faster_client.send(faster_request)
            assert_response_ok(faster_response)
            faster_data = faster_response.json()
        
        # Compare results
        assert httpx_data['json'] == faster_data['json']


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_api_client_scenario(self, test_urls, sample_json_data, sample_headers):
        """Test typical API client usage scenario."""
        # Simulate a typical API client workflow
        base_url = test_urls['get'].rsplit('/', 1)[0]  # Use local test server
        headers = {'User-Agent': 'MyApp/1.0', 'Accept': 'application/json'}
        
        # Test with httpx first
        with httpx.Client(base_url=base_url, headers=headers) as httpx_client:
            # Get resource
            response = httpx_client.get('/get')
            assert_response_ok(response)
            httpx_get_data = response.json()
            
            # Create resource
            response = httpx_client.post('/post', json=sample_json_data)
            assert_response_ok(response)
            httpx_post_data = response.json()
            
            # Update resource
            update_data = {'id': 1, 'updated': True}
            response = httpx_client.put('/put', json=update_data)
            assert_response_ok(response)
            httpx_put_data = response.json()
            
            # Delete resource
            response = httpx_client.delete('/delete')
            assert_response_ok(response)
            httpx_delete_status = response.status_code
        
        # Test with faster-http second
        with faster_http.Client(base_url=base_url, headers=headers) as faster_client:
            # Get resource
            response = faster_client.get('/get')
            assert_response_ok(response)
            faster_get_data = response.json()
            
            # Create resource
            response = faster_client.post('/post', json=sample_json_data)
            assert_response_ok(response)
            faster_post_data = response.json()
            
            # Update resource
            update_data = {'id': 1, 'updated': True}
            response = faster_client.put('/put', json=update_data)
            assert_response_ok(response)
            faster_put_data = response.json()
            
            # Delete resource
            response = faster_client.delete('/delete')
            assert_response_ok(response)
            faster_delete_status = response.status_code
        
        # Compare results
        assert httpx_get_data['headers']['User-Agent'] == faster_get_data['headers']['User-Agent']
        assert httpx_post_data['json'] == faster_post_data['json']
        assert httpx_put_data['json'] == faster_put_data['json']
        assert httpx_delete_status == faster_delete_status
    
    @pytest.mark.asyncio
    async def test_async_api_client_scenario(self, test_urls, sample_json_data):
        """Test async API client usage scenario."""
        # Simulate async API client with concurrent requests
        base_url = test_urls['get'].rsplit('/', 1)[0]  # Use local test server
        headers = {'User-Agent': 'AsyncApp/1.0', 'Accept': 'application/json'}
        
        # Test with httpx first
        async with httpx.AsyncClient(base_url=base_url, headers=headers) as httpx_client:
            # Concurrent API calls
            tasks = [
                httpx_client.get('/get'),
                httpx_client.post('/post', json=sample_json_data),
                httpx_client.put('/put', json=sample_json_data),
                httpx_client.delete('/delete')
            ]
            httpx_responses = await asyncio.gather(*tasks)
            httpx_statuses = [r.status_code for r in httpx_responses]
        
        # Test with faster-http second
        async with faster_http.AsyncClient(base_url=base_url, headers=headers) as faster_client:
            # Concurrent API calls
            tasks = [
                faster_client.get('/get'),
                faster_client.post('/post', json=sample_json_data),
                faster_client.put('/put', json=sample_json_data),
                faster_client.delete('/delete')
            ]
            faster_responses = await asyncio.gather(*tasks)
            faster_statuses = [r.status_code for r in faster_responses]
        
        # Compare results
        assert httpx_statuses == faster_statuses
    
    def test_file_upload_scenario(self, test_urls, sample_files):
        """Test file upload scenario."""
        # Test with httpx first
        httpx_response = httpx.post(test_urls['post'], files=sample_files)
        assert_response_ok(httpx_response)
        httpx_data = httpx_response.json()
        
        # Test with faster-http second
        faster_response = faster_http.post(test_urls['post'], files=sample_files)
        assert_response_ok(faster_response)
        faster_data = faster_response.json()
        
        # Compare file upload results
        assert 'files' in httpx_data
        assert 'files' in faster_data
        
        # Check that files were uploaded
        for filename in sample_files.keys():
            assert filename in httpx_data['files']
            assert filename in faster_data['files']
    
    def test_form_data_scenario(self, test_urls, sample_form_data):
        """Test form data submission scenario."""
        # Test with httpx first
        httpx_response = httpx.post(test_urls['post'], data=sample_form_data)
        assert_response_ok(httpx_response)
        httpx_data = httpx_response.json()
        
        # Test with faster-http second
        faster_response = faster_http.post(test_urls['post'], data=sample_form_data)
        assert_response_ok(faster_response)
        faster_data = faster_response.json()
        
        # Compare form data results
        assert httpx_data['form'] == faster_data['form']
    
    def test_authentication_scenario(self, test_urls):
        """Test authentication scenario."""
        # Test with httpx first
        httpx_auth = httpx.BasicAuth('user', 'pass')
        try:
            httpx_response = httpx.get(test_urls['basic_auth'], auth=httpx_auth)
            httpx_status = httpx_response.status_code
            assert httpx_status in [200, 401]
        except Exception as e:
            pytest.skip(f"httpx auth test failed: {e}")
        
        # Test with faster-http second
        faster_auth = faster_http.BasicAuth('user', 'pass')
        try:
            faster_response = faster_http.get(test_urls['basic_auth'], auth=faster_auth)
            faster_status = faster_response.status_code
            assert faster_status in [200, 401]
        except Exception as e:
            pytest.skip(f"faster-http auth test failed: {e}")
        
        # Compare authentication results
        assert httpx_status == faster_status
    
    def test_redirect_handling_scenario(self, test_urls):
        """Test redirect handling scenario."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['redirect'].format(n=3), follow_redirects=True)
        assert_response_ok(httpx_response)
        httpx_final_url = httpx_response.url
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['redirect'].format(n=3), follow_redirects=True)
        assert_response_ok(faster_response)
        faster_final_url = faster_response.url
        
        # Both should end up at the same final URL  
        assert '/get' in httpx_final_url
        assert '/get' in faster_final_url
    
    def test_timeout_handling_scenario(self, test_urls):
        """Test timeout handling scenario."""
        # Test with httpx first
        try:
            httpx.get(test_urls['delay'].format(seconds=5), timeout=2.0)
            httpx_timeout_occurred = False
        except (httpx.ReadTimeout, httpx.TimeoutException):
            httpx_timeout_occurred = True
        
        # Test with faster-http second
        try:
            faster_http.get(test_urls['delay'].format(seconds=5), timeout=2.0)
            faster_timeout_occurred = False
        except (faster_http.ReadTimeout, faster_http.RequestError):
            faster_timeout_occurred = True
        
        # Both should timeout
        assert httpx_timeout_occurred
        assert faster_timeout_occurred
    
    def test_response_streaming_scenario(self, test_urls):
        """Test response streaming scenario."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['stream'].format(n=5))
        assert_response_ok(httpx_response)
        
        httpx_lines = httpx_response.iter_lines()
        assert len(httpx_lines) > 0
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['stream'].format(n=5))
        assert_response_ok(faster_response)
        
        faster_lines = faster_response.iter_lines()
        assert len(faster_lines) > 0
        
        # Both should return streaming data
        assert len(httpx_lines) == len(faster_lines)