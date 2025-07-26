"""
Unit tests for codes module
Testing httpx.codes compatibility and comparison.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx
import faster_http


class TestStatusCodes:
    """Test HTTP status code constants - httpx vs faster_http comparison."""
    
    def test_codes_import_comparison(self):
        """Test that codes can be imported - httpx vs faster_http."""
        # First test httpx codes import
        assert hasattr(httpx, 'codes')
        assert httpx.codes is not None
        
        # Then test faster_http codes import (should match httpx)
        assert hasattr(faster_http, 'codes')
        assert faster_http.codes is not None
    
    def test_informational_1xx_codes_comparison(self):
        """Test 1xx informational status codes - httpx vs faster_http."""
        # First test httpx 1xx codes
        httpx_codes = httpx.codes
        
        # Check httpx has standard 1xx codes
        assert hasattr(httpx_codes, 'CONTINUE')
        assert httpx_codes.CONTINUE == 100
        assert hasattr(httpx_codes, 'SWITCHING_PROTOCOLS')
        assert httpx_codes.SWITCHING_PROTOCOLS == 101
        
        # Then test faster_http 1xx codes (should match httpx exactly)
        faster_codes = faster_http.codes
        
        # Check faster_http has same 1xx codes as httpx
        assert hasattr(faster_codes, 'CONTINUE')
        assert faster_codes.CONTINUE == 100
        assert hasattr(faster_codes, 'SWITCHING_PROTOCOLS')
        assert faster_codes.SWITCHING_PROTOCOLS == 101
        
        # Both should have identical values
        assert httpx_codes.CONTINUE == faster_codes.CONTINUE
        assert httpx_codes.SWITCHING_PROTOCOLS == faster_codes.SWITCHING_PROTOCOLS
        
        # Test additional 1xx codes if httpx has them
        if hasattr(httpx_codes, 'PROCESSING'):
            assert hasattr(faster_codes, 'PROCESSING')
            assert httpx_codes.PROCESSING == faster_codes.PROCESSING == 102
        
        if hasattr(httpx_codes, 'EARLY_HINTS'):
            assert hasattr(faster_codes, 'EARLY_HINTS')
            assert httpx_codes.EARLY_HINTS == faster_codes.EARLY_HINTS == 103
    
    def test_successful_2xx_codes_comparison(self):
        """Test 2xx successful status codes - httpx vs faster_http."""
        # First test httpx 2xx codes
        httpx_codes = httpx.codes
        
        # Check httpx has standard 2xx codes
        assert hasattr(httpx_codes, 'OK')
        assert httpx_codes.OK == 200
        assert hasattr(httpx_codes, 'CREATED')
        assert httpx_codes.CREATED == 201
        assert hasattr(httpx_codes, 'ACCEPTED')
        assert httpx_codes.ACCEPTED == 202
        assert hasattr(httpx_codes, 'NO_CONTENT')
        assert httpx_codes.NO_CONTENT == 204
        
        # Then test faster_http 2xx codes (should match httpx exactly)
        faster_codes = faster_http.codes
        
        # Check faster_http has same 2xx codes as httpx
        assert hasattr(faster_codes, 'OK')
        assert faster_codes.OK == 200
        assert hasattr(faster_codes, 'CREATED')
        assert faster_codes.CREATED == 201
        assert hasattr(faster_codes, 'ACCEPTED')
        assert faster_codes.ACCEPTED == 202
        assert hasattr(faster_codes, 'NO_CONTENT')
        assert faster_codes.NO_CONTENT == 204
        
        # Both should have identical values
        assert httpx_codes.OK == faster_codes.OK
        assert httpx_codes.CREATED == faster_codes.CREATED
        assert httpx_codes.ACCEPTED == faster_codes.ACCEPTED
        assert httpx_codes.NO_CONTENT == faster_codes.NO_CONTENT
        
        # Test additional 2xx codes if httpx has them
        if hasattr(httpx_codes, 'NON_AUTHORITATIVE_INFORMATION'):
            assert hasattr(faster_codes, 'NON_AUTHORITATIVE_INFORMATION')
            assert httpx_codes.NON_AUTHORITATIVE_INFORMATION == faster_codes.NON_AUTHORITATIVE_INFORMATION == 203
        
        if hasattr(httpx_codes, 'RESET_CONTENT'):
            assert hasattr(faster_codes, 'RESET_CONTENT')
            assert httpx_codes.RESET_CONTENT == faster_codes.RESET_CONTENT == 205
        
        if hasattr(httpx_codes, 'PARTIAL_CONTENT'):
            assert hasattr(faster_codes, 'PARTIAL_CONTENT')
            assert httpx_codes.PARTIAL_CONTENT == faster_codes.PARTIAL_CONTENT == 206
    
    def test_redirection_3xx_codes_comparison(self):
        """Test 3xx redirection status codes - httpx vs faster_http."""
        # First test httpx 3xx codes
        httpx_codes = httpx.codes
        
        # Check httpx has standard 3xx codes
        assert hasattr(httpx_codes, 'MOVED_PERMANENTLY')
        assert httpx_codes.MOVED_PERMANENTLY == 301
        assert hasattr(httpx_codes, 'FOUND')
        assert httpx_codes.FOUND == 302
        assert hasattr(httpx_codes, 'SEE_OTHER')
        assert httpx_codes.SEE_OTHER == 303
        assert hasattr(httpx_codes, 'NOT_MODIFIED')
        assert httpx_codes.NOT_MODIFIED == 304
        
        # Then test faster_http 3xx codes (should match httpx exactly)
        faster_codes = faster_http.codes
        
        # Check faster_http has same 3xx codes as httpx
        assert hasattr(faster_codes, 'MOVED_PERMANENTLY')
        assert faster_codes.MOVED_PERMANENTLY == 301
        assert hasattr(faster_codes, 'FOUND')
        assert faster_codes.FOUND == 302
        assert hasattr(faster_codes, 'SEE_OTHER')
        assert faster_codes.SEE_OTHER == 303
        assert hasattr(faster_codes, 'NOT_MODIFIED')
        assert faster_codes.NOT_MODIFIED == 304
        
        # Both should have identical values
        assert httpx_codes.MOVED_PERMANENTLY == faster_codes.MOVED_PERMANENTLY
        assert httpx_codes.FOUND == faster_codes.FOUND
        assert httpx_codes.SEE_OTHER == faster_codes.SEE_OTHER
        assert httpx_codes.NOT_MODIFIED == faster_codes.NOT_MODIFIED
        
        # Test additional 3xx codes if httpx has them
        if hasattr(httpx_codes, 'MULTIPLE_CHOICES'):
            assert hasattr(faster_codes, 'MULTIPLE_CHOICES')
            assert httpx_codes.MULTIPLE_CHOICES == faster_codes.MULTIPLE_CHOICES == 300
        
        if hasattr(httpx_codes, 'TEMPORARY_REDIRECT'):
            assert hasattr(faster_codes, 'TEMPORARY_REDIRECT')
            assert httpx_codes.TEMPORARY_REDIRECT == faster_codes.TEMPORARY_REDIRECT == 307
        
        if hasattr(httpx_codes, 'PERMANENT_REDIRECT'):
            assert hasattr(faster_codes, 'PERMANENT_REDIRECT')
            assert httpx_codes.PERMANENT_REDIRECT == faster_codes.PERMANENT_REDIRECT == 308
    
    def test_client_error_4xx_codes_comparison(self):
        """Test 4xx client error status codes - httpx vs faster_http."""
        # First test httpx 4xx codes
        httpx_codes = httpx.codes
        
        # Check httpx has standard 4xx codes
        assert hasattr(httpx_codes, 'BAD_REQUEST')
        assert httpx_codes.BAD_REQUEST == 400
        assert hasattr(httpx_codes, 'UNAUTHORIZED')
        assert httpx_codes.UNAUTHORIZED == 401
        assert hasattr(httpx_codes, 'FORBIDDEN')
        assert httpx_codes.FORBIDDEN == 403
        assert hasattr(httpx_codes, 'NOT_FOUND')
        assert httpx_codes.NOT_FOUND == 404
        
        # Then test faster_http 4xx codes (should match httpx exactly)
        faster_codes = faster_http.codes
        
        # Check faster_http has same 4xx codes as httpx
        assert hasattr(faster_codes, 'BAD_REQUEST')
        assert faster_codes.BAD_REQUEST == 400
        assert hasattr(faster_codes, 'UNAUTHORIZED')
        assert faster_codes.UNAUTHORIZED == 401
        assert hasattr(faster_codes, 'FORBIDDEN')
        assert faster_codes.FORBIDDEN == 403
        assert hasattr(faster_codes, 'NOT_FOUND')
        assert faster_codes.NOT_FOUND == 404
        
        # Both should have identical values
        assert httpx_codes.BAD_REQUEST == faster_codes.BAD_REQUEST
        assert httpx_codes.UNAUTHORIZED == faster_codes.UNAUTHORIZED
        assert httpx_codes.FORBIDDEN == faster_codes.FORBIDDEN
        assert httpx_codes.NOT_FOUND == faster_codes.NOT_FOUND
        
        # Test additional 4xx codes if httpx has them
        if hasattr(httpx_codes, 'METHOD_NOT_ALLOWED'):
            assert hasattr(faster_codes, 'METHOD_NOT_ALLOWED')
            assert httpx_codes.METHOD_NOT_ALLOWED == faster_codes.METHOD_NOT_ALLOWED == 405
        
        if hasattr(httpx_codes, 'NOT_ACCEPTABLE'):
            assert hasattr(faster_codes, 'NOT_ACCEPTABLE')
            assert httpx_codes.NOT_ACCEPTABLE == faster_codes.NOT_ACCEPTABLE == 406
        
        if hasattr(httpx_codes, 'REQUEST_TIMEOUT'):
            assert hasattr(faster_codes, 'REQUEST_TIMEOUT')
            assert httpx_codes.REQUEST_TIMEOUT == faster_codes.REQUEST_TIMEOUT == 408
        
        if hasattr(httpx_codes, 'CONFLICT'):
            assert hasattr(faster_codes, 'CONFLICT')
            assert httpx_codes.CONFLICT == faster_codes.CONFLICT == 409
        
        if hasattr(httpx_codes, 'GONE'):
            assert hasattr(faster_codes, 'GONE')  
            assert httpx_codes.GONE == faster_codes.GONE == 410
        
        if hasattr(httpx_codes, 'UNPROCESSABLE_ENTITY'):
            assert hasattr(faster_codes, 'UNPROCESSABLE_ENTITY')
            assert httpx_codes.UNPROCESSABLE_ENTITY == faster_codes.UNPROCESSABLE_ENTITY == 422
        
        if hasattr(httpx_codes, 'TOO_MANY_REQUESTS'):
            assert hasattr(faster_codes, 'TOO_MANY_REQUESTS')
            assert httpx_codes.TOO_MANY_REQUESTS == faster_codes.TOO_MANY_REQUESTS == 429
    
    def test_server_error_5xx_codes_comparison(self):
        """Test 5xx server error status codes - httpx vs faster_http."""
        # First test httpx 5xx codes
        httpx_codes = httpx.codes
        
        # Check httpx has standard 5xx codes
        assert hasattr(httpx_codes, 'INTERNAL_SERVER_ERROR')
        assert httpx_codes.INTERNAL_SERVER_ERROR == 500
        assert hasattr(httpx_codes, 'NOT_IMPLEMENTED')
        assert httpx_codes.NOT_IMPLEMENTED == 501
        assert hasattr(httpx_codes, 'BAD_GATEWAY')
        assert httpx_codes.BAD_GATEWAY == 502
        assert hasattr(httpx_codes, 'SERVICE_UNAVAILABLE')
        assert httpx_codes.SERVICE_UNAVAILABLE == 503
        assert hasattr(httpx_codes, 'GATEWAY_TIMEOUT')
        assert httpx_codes.GATEWAY_TIMEOUT == 504
        
        # Then test faster_http 5xx codes (should match httpx exactly)
        faster_codes = faster_http.codes
        
        # Check faster_http has same 5xx codes as httpx
        assert hasattr(faster_codes, 'INTERNAL_SERVER_ERROR')
        assert faster_codes.INTERNAL_SERVER_ERROR == 500
        assert hasattr(faster_codes, 'NOT_IMPLEMENTED')
        assert faster_codes.NOT_IMPLEMENTED == 501
        assert hasattr(faster_codes, 'BAD_GATEWAY')
        assert faster_codes.BAD_GATEWAY == 502
        assert hasattr(faster_codes, 'SERVICE_UNAVAILABLE')
        assert faster_codes.SERVICE_UNAVAILABLE == 503
        assert hasattr(faster_codes, 'GATEWAY_TIMEOUT')
        assert faster_codes.GATEWAY_TIMEOUT == 504
        
        # Both should have identical values
        assert httpx_codes.INTERNAL_SERVER_ERROR == faster_codes.INTERNAL_SERVER_ERROR
        assert httpx_codes.NOT_IMPLEMENTED == faster_codes.NOT_IMPLEMENTED
        assert httpx_codes.BAD_GATEWAY == faster_codes.BAD_GATEWAY
        assert httpx_codes.SERVICE_UNAVAILABLE == faster_codes.SERVICE_UNAVAILABLE
        assert httpx_codes.GATEWAY_TIMEOUT == faster_codes.GATEWAY_TIMEOUT
        
        # Test additional 5xx codes if httpx has them
        if hasattr(httpx_codes, 'HTTP_VERSION_NOT_SUPPORTED'):
            assert hasattr(faster_codes, 'HTTP_VERSION_NOT_SUPPORTED')
            assert httpx_codes.HTTP_VERSION_NOT_SUPPORTED == faster_codes.HTTP_VERSION_NOT_SUPPORTED == 505
    
    def test_codes_consistency_comparison(self):
        """Test that faster_http doesn't implement codes that httpx doesn't have."""
        httpx_codes = httpx.codes
        faster_codes = faster_http.codes
        
        # Get all attributes from both codes modules
        httpx_attrs = set(attr for attr in dir(httpx_codes) if not attr.startswith('_'))
        faster_attrs = set(attr for attr in dir(faster_codes) if not attr.startswith('_'))
        
        # faster_http should not have codes that httpx doesn't have
        extra_codes = faster_attrs - httpx_attrs
        assert len(extra_codes) == 0, f"faster_http has extra codes that httpx doesn't have: {extra_codes}"
        
        # Check that all common codes have the same values
        common_codes = httpx_attrs & faster_attrs
        for code_name in common_codes:
            httpx_value = getattr(httpx_codes, code_name)
            faster_value = getattr(faster_codes, code_name)
            assert httpx_value == faster_value, f"Code {code_name} differs: httpx={httpx_value}, faster_http={faster_value}"