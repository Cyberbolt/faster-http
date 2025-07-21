"""
Unit tests for Response object functionality.
Tests response object properties and methods by comparing with httpx.
"""

import pytest
import httpx
import faster_http
from ..conftest import assert_response_ok, assert_httpx_compatibility


class TestResponseProperties:
    """Test Response object properties by comparing with httpx."""
    
    def test_response_basic_properties(self, test_urls):
        """Test basic response properties - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['get'])
        assert_response_ok(httpx_response)
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['get'])
        assert_response_ok(faster_response)
        assert_httpx_compatibility(faster_response)
        
        # Compare basic properties
        assert httpx_response.status_code == faster_response.status_code
        assert type(httpx_response.headers) == type(faster_response.headers)
        assert type(httpx_response.content) == type(faster_response.content)
        assert type(httpx_response.text) == type(faster_response.text)
        assert type(httpx_response.url) == type(faster_response.url)
        assert type(httpx_response.elapsed) == type(faster_response.elapsed)
    
    def test_response_status_properties(self, test_urls):
        """Test response status properties - compare httpx vs faster-http."""
        # Test successful response
        httpx_success = httpx.get(test_urls['status'].format(code=200))
        faster_success = faster_http.get(test_urls['status'].format(code=200))
        
        assert httpx_success.ok == faster_success.ok
        assert httpx_success.is_redirect == faster_success.is_redirect
        assert httpx_success.is_client_error == faster_success.is_client_error
        assert httpx_success.is_server_error == faster_success.is_server_error
        
        # Test client error
        httpx_client_error = httpx.get(test_urls['status'].format(code=404))
        faster_client_error = faster_http.get(test_urls['status'].format(code=404))
        
        assert httpx_client_error.ok == faster_client_error.ok
        assert httpx_client_error.is_client_error == faster_client_error.is_client_error
        assert httpx_client_error.is_server_error == faster_client_error.is_server_error
        
        # Test server error
        httpx_server_error = httpx.get(test_urls['status'].format(code=500))
        faster_server_error = faster_http.get(test_urls['status'].format(code=500))
        
        assert httpx_server_error.ok == faster_server_error.ok
        assert httpx_server_error.is_client_error == faster_server_error.is_client_error
        assert httpx_server_error.is_server_error == faster_server_error.is_server_error
    
    def test_response_content_properties(self, test_urls):
        """Test response content properties - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['get'])
        assert_response_ok(httpx_response)
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['get'])
        assert_response_ok(faster_response)
        
        # Compare content properties
        assert isinstance(httpx_response.content, bytes)
        assert isinstance(faster_response.content, bytes)
        assert isinstance(httpx_response.text, str)
        assert isinstance(faster_response.text, str)
        assert isinstance(httpx_response.headers, dict)
        assert isinstance(faster_response.headers, dict)
        assert isinstance(httpx_response.cookies, dict)
        assert isinstance(faster_response.cookies, dict)
        assert isinstance(httpx_response.encoding, str)
        assert isinstance(faster_response.encoding, str)
        assert isinstance(httpx_response.http_version, str)
        assert isinstance(faster_response.http_version, str)
        assert isinstance(httpx_response.elapsed, float)
        assert isinstance(faster_response.elapsed, float)
    
    def test_response_json_parsing(self, test_urls):
        """Test JSON response parsing - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['json'])
        assert_response_ok(httpx_response)
        httpx_data = httpx_response.json()
        assert isinstance(httpx_data, dict)
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['json'])
        assert_response_ok(faster_response)
        faster_data = faster_response.json()
        assert isinstance(faster_data, dict)
        
        # Compare JSON data
        assert httpx_data == faster_data
    
    def test_response_headers_handling(self, test_urls):
        """Test response headers handling - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['get'])
        assert_response_ok(httpx_response)
        httpx_headers = httpx_response.headers
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['get'])
        assert_response_ok(faster_response)
        faster_headers = faster_response.headers
        
        # Check that both have headers
        assert isinstance(httpx_headers, dict)
        assert isinstance(faster_headers, dict)
        
        # Check common headers exist
        common_headers = ['Content-Type', 'Server', 'Date']
        for header in common_headers:
            httpx_val = httpx_headers.get(header) or httpx_headers.get(header.lower())
            faster_val = faster_headers.get(header) or faster_headers.get(header.lower())
            # Both should have the header or both should not have it
            assert (httpx_val is not None) == (faster_val is not None), f"Header {header} presence differs"
    
    def test_response_cookies_handling(self, test_urls):
        """Test response cookies handling - compare httpx vs faster-http."""
        # Use endpoint that sets cookies
        cookie_url = test_urls['cookies_set'] + '/test/value'
        
        # Test with httpx first
        httpx_response = httpx.get(cookie_url)
        assert_response_ok(httpx_response)
        httpx_cookies = httpx_response.cookies
        
        # Test with faster-http second
        faster_response = faster_http.get(cookie_url)
        assert_response_ok(faster_response)
        faster_cookies = faster_response.cookies
        
        # Check that both handle cookies
        assert isinstance(httpx_cookies, dict)
        assert isinstance(faster_cookies, dict)
    
    def test_response_url_handling(self, test_urls):
        """Test response URL handling - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['get'])
        assert_response_ok(httpx_response)
        httpx_url = httpx_response.url
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['get'])
        assert_response_ok(faster_response)
        faster_url = faster_response.url
        
        # URLs should be equivalent
        assert isinstance(httpx_url, str)
        assert isinstance(faster_url, str)
        assert '/get' in httpx_url
        assert '/get' in faster_url
    
    def test_response_encoding_handling(self, test_urls):
        """Test response encoding handling - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['encoding'])
        assert_response_ok(httpx_response)
        httpx_encoding = httpx_response.encoding
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['encoding'])
        assert_response_ok(faster_response)
        faster_encoding = faster_response.encoding
        
        # Both should have valid encoding
        assert isinstance(httpx_encoding, str)
        assert isinstance(faster_encoding, str)
        assert httpx_encoding.lower() in ['utf-8', 'utf8', 'iso-8859-1', 'ascii']
        assert faster_encoding.lower() in ['utf-8', 'utf8', 'iso-8859-1', 'ascii']


class TestResponseMethods:
    """Test Response object methods by comparing with httpx."""
    
    def test_response_repr(self, test_urls):
        """Test response string representation - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['get'])
        httpx_repr = repr(httpx_response)
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['get'])
        faster_repr = repr(faster_response)
        
        # Both should have meaningful representations
        assert 'Response' in httpx_repr
        assert 'Response' in faster_repr
        assert '200' in httpx_repr
        assert '200' in faster_repr
    
    def test_response_raise_for_status_success(self, test_urls):
        """Test raise_for_status with successful response - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['get'])
        # Should not raise any exception
        httpx_response.raise_for_status()
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['get'])
        # Should not raise any exception
        faster_response.raise_for_status()
    
    def test_response_raise_for_status_error(self, test_urls):
        """Test raise_for_status with error response - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['status'].format(code=404))
        with pytest.raises(httpx.HTTPStatusError):
            httpx_response.raise_for_status()
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['status'].format(code=404))
        with pytest.raises(faster_http.HTTPError):
            faster_response.raise_for_status()
    
    def test_response_iteration_methods(self, test_urls):
        """Test response iteration methods - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['get'])
        assert_response_ok(httpx_response)
        
        # Test iter_bytes
        httpx_byte_chunks = httpx_response.iter_bytes(chunk_size=100)
        assert isinstance(httpx_byte_chunks, list)
        assert len(httpx_byte_chunks) > 0
        assert all(isinstance(chunk, bytes) for chunk in httpx_byte_chunks)
        
        # Test iter_text
        httpx_text_chunks = httpx_response.iter_text(chunk_size=100)
        assert isinstance(httpx_text_chunks, list)
        assert len(httpx_text_chunks) > 0
        assert all(isinstance(chunk, str) for chunk in httpx_text_chunks)
        
        # Test iter_lines
        httpx_lines = httpx_response.iter_lines()
        assert isinstance(httpx_lines, list)
        assert len(httpx_lines) > 0
        assert all(isinstance(line, str) for line in httpx_lines)
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['get'])
        assert_response_ok(faster_response)
        
        # Test iter_bytes
        faster_byte_chunks = faster_response.iter_bytes(chunk_size=100)
        assert isinstance(faster_byte_chunks, list)
        assert len(faster_byte_chunks) > 0
        assert all(isinstance(chunk, bytes) for chunk in faster_byte_chunks)
        
        # Test iter_text
        faster_text_chunks = faster_response.iter_text(chunk_size=100)
        assert isinstance(faster_text_chunks, list)
        assert len(faster_text_chunks) > 0
        assert all(isinstance(chunk, str) for chunk in faster_text_chunks)
        
        # Test iter_lines
        faster_lines = faster_response.iter_lines()
        assert isinstance(faster_lines, list)
        assert len(faster_lines) > 0
        assert all(isinstance(line, str) for line in faster_lines)
        
        # Compare iteration results
        assert len(httpx_byte_chunks) == len(faster_byte_chunks)
        assert len(httpx_text_chunks) == len(faster_text_chunks)
        assert len(httpx_lines) == len(faster_lines)
    
    def test_response_raw_iteration(self, test_urls):
        """Test response raw iteration - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['get'])
        assert_response_ok(httpx_response)
        
        httpx_raw_chunks = httpx_response.iter_raw(chunk_size=100)
        assert isinstance(httpx_raw_chunks, list)
        assert len(httpx_raw_chunks) > 0
        assert all(isinstance(chunk, bytes) for chunk in httpx_raw_chunks)
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['get'])
        assert_response_ok(faster_response)
        
        faster_raw_chunks = faster_response.iter_raw(chunk_size=100)
        assert isinstance(faster_raw_chunks, list)
        assert len(faster_raw_chunks) > 0
        assert all(isinstance(chunk, bytes) for chunk in faster_raw_chunks)
        
        # Compare raw iteration results
        assert len(httpx_raw_chunks) == len(faster_raw_chunks)


class TestResponseContentTypes:
    """Test Response object with different content types."""
    
    def test_response_json_content(self, test_urls):
        """Test JSON response content - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['json'])
        assert_response_ok(httpx_response)
        httpx_json = httpx_response.json()
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['json'])
        assert_response_ok(faster_response)
        faster_json = faster_response.json()
        
        # Compare JSON content
        assert httpx_json == faster_json
        assert isinstance(httpx_json, dict)
        assert isinstance(faster_json, dict)
    
    def test_response_html_content(self, test_urls):
        """Test HTML response content - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['html'])
        assert_response_ok(httpx_response)
        httpx_text = httpx_response.text
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['html'])
        assert_response_ok(faster_response)
        faster_text = faster_response.text
        
        # Compare HTML content
        assert httpx_text == faster_text
        assert isinstance(httpx_text, str)
        assert isinstance(faster_text, str)
        assert '<html>' in httpx_text.lower()
        assert '<html>' in faster_text.lower()
    
    def test_response_xml_content(self, test_urls):
        """Test XML response content - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['xml'])
        assert_response_ok(httpx_response)
        httpx_text = httpx_response.text
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['xml'])
        assert_response_ok(faster_response)
        faster_text = faster_response.text
        
        # Compare XML content
        assert httpx_text == faster_text
        assert isinstance(httpx_text, str)
        assert isinstance(faster_text, str)
        assert '<?xml' in httpx_text
        assert '<?xml' in faster_text
    
    def test_response_binary_content(self, test_urls):
        """Test binary response content - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['bytes'].format(size=1024))
        assert_response_ok(httpx_response)
        httpx_content = httpx_response.content
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['bytes'].format(size=1024))
        assert_response_ok(faster_response)
        faster_content = faster_response.content
        
        # Compare binary content
        assert httpx_content == faster_content
        assert isinstance(httpx_content, bytes)
        assert isinstance(faster_content, bytes)
        assert len(httpx_content) == len(faster_content)
    
    def test_response_image_content(self, test_urls):
        """Test image response content - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_response = httpx.get(test_urls['image'])
        assert_response_ok(httpx_response)
        httpx_content = httpx_response.content
        
        # Test with faster-http second
        faster_response = faster_http.get(test_urls['image'])
        assert_response_ok(faster_response)
        faster_content = faster_response.content
        
        # Compare image content
        assert httpx_content == faster_content
        assert isinstance(httpx_content, bytes)
        assert isinstance(faster_content, bytes)
        assert len(httpx_content) > 0
        assert len(faster_content) > 0