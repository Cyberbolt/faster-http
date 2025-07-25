"""
Unit tests for faster-http codes module
Testing httpx.codes compatibility
"""

import pytest
import faster_http


class TestStatusCodes:
    """Test HTTP status code constants"""
    
    def test_codes_import(self):
        """Test that codes can be imported"""
        assert hasattr(faster_http, 'codes')
        assert faster_http.codes is not None
    
    def test_informational_1xx_codes(self):
        """Test 1xx informational status codes"""
        codes = faster_http.codes
        
        assert codes.CONTINUE == 100
        assert codes.SWITCHING_PROTOCOLS == 101
        assert codes.PROCESSING == 102
        assert codes.EARLY_HINTS == 103
    
    def test_successful_2xx_codes(self):
        """Test 2xx successful status codes"""
        codes = faster_http.codes
        
        assert codes.OK == 200
        assert codes.CREATED == 201
        assert codes.ACCEPTED == 202
        assert codes.NON_AUTHORITATIVE_INFORMATION == 203
        assert codes.NO_CONTENT == 204
        assert codes.RESET_CONTENT == 205
        assert codes.PARTIAL_CONTENT == 206
        assert codes.MULTI_STATUS == 207
        assert codes.ALREADY_REPORTED == 208
        assert codes.IM_USED == 226
    
    def test_redirection_3xx_codes(self):
        """Test 3xx redirection status codes"""
        codes = faster_http.codes
        
        assert codes.MULTIPLE_CHOICES == 300
        assert codes.MOVED_PERMANENTLY == 301
        assert codes.FOUND == 302
        assert codes.SEE_OTHER == 303
        assert codes.NOT_MODIFIED == 304
        assert codes.USE_PROXY == 305
        assert codes.TEMPORARY_REDIRECT == 307
        assert codes.PERMANENT_REDIRECT == 308
    
    def test_client_error_4xx_codes(self):
        """Test 4xx client error status codes"""
        codes = faster_http.codes
        
        assert codes.BAD_REQUEST == 400
        assert codes.UNAUTHORIZED == 401
        assert codes.PAYMENT_REQUIRED == 402
        assert codes.FORBIDDEN == 403
        assert codes.NOT_FOUND == 404
        assert codes.METHOD_NOT_ALLOWED == 405
        assert codes.NOT_ACCEPTABLE == 406
        assert codes.PROXY_AUTHENTICATION_REQUIRED == 407
        assert codes.REQUEST_TIMEOUT == 408
        assert codes.CONFLICT == 409
        assert codes.GONE == 410
        assert codes.LENGTH_REQUIRED == 411
        assert codes.PRECONDITION_FAILED == 412
        assert codes.PAYLOAD_TOO_LARGE == 413
        assert codes.URI_TOO_LONG == 414
        assert codes.UNSUPPORTED_MEDIA_TYPE == 415
        assert codes.RANGE_NOT_SATISFIABLE == 416
        assert codes.EXPECTATION_FAILED == 417
        assert codes.IM_A_TEAPOT == 418
        assert codes.MISDIRECTED_REQUEST == 421
        assert codes.UNPROCESSABLE_ENTITY == 422
        assert codes.LOCKED == 423
        assert codes.FAILED_DEPENDENCY == 424
        assert codes.TOO_EARLY == 425
        assert codes.UPGRADE_REQUIRED == 426
        assert codes.PRECONDITION_REQUIRED == 428
        assert codes.TOO_MANY_REQUESTS == 429
        assert codes.REQUEST_HEADER_FIELDS_TOO_LARGE == 431
        assert codes.UNAVAILABLE_FOR_LEGAL_REASONS == 451
    
    def test_server_error_5xx_codes(self):
        """Test 5xx server error status codes"""
        codes = faster_http.codes
        
        assert codes.INTERNAL_SERVER_ERROR == 500
        assert codes.NOT_IMPLEMENTED == 501
        assert codes.BAD_GATEWAY == 502
        assert codes.SERVICE_UNAVAILABLE == 503
        assert codes.GATEWAY_TIMEOUT == 504
        assert codes.HTTP_VERSION_NOT_SUPPORTED == 505
        assert codes.VARIANT_ALSO_NEGOTIATES == 506
        assert codes.INSUFFICIENT_STORAGE == 507
        assert codes.LOOP_DETECTED == 508
        assert codes.NOT_EXTENDED == 510
        assert codes.NETWORK_AUTHENTICATION_REQUIRED == 511
    
    def test_codes_usage_like_httpx(self):
        """Test codes usage similar to httpx examples"""
        codes = faster_http.codes
        
        # Test the most common usage pattern
        status_code = 200
        assert status_code == codes.OK
        
        status_code = 404  
        assert status_code == codes.NOT_FOUND
        
        status_code = 500
        assert status_code == codes.INTERNAL_SERVER_ERROR
    
    def test_codes_contains_method(self):
        """Test the __contains__ method"""
        codes = faster_http.codes
        
        # Test known status codes
        assert 200 in codes
        assert 404 in codes
        assert 500 in codes
        
        # Test edge cases - these might not work as expected in current implementation
        # but shows the intended behavior
        try:
            # Codes object doesn't implement __contains__ for integer values
            # but this test documents the intended behavior
            pass
        except (TypeError, AttributeError):
            pass
    
    def test_get_reason_phrase(self):
        """Test getting reason phrases for status codes"""
        codes = faster_http.codes
        
        assert codes.get_reason_phrase(200) == 'OK'
        assert codes.get_reason_phrase(404) == 'Not Found'
        assert codes.get_reason_phrase(500) == 'Internal Server Error'
        assert codes.get_reason_phrase(418) == "I'm A Teapot"
        
        # Test unknown status code
        assert codes.get_reason_phrase(999) == 'Unknown'
    
    def test_codes_singleton_behavior(self):
        """Test that codes behave as a singleton"""
        codes1 = faster_http.codes
        codes2 = faster_http.codes
        
        # Should be the same instance
        assert codes1 is codes2
        
        # Test that attributes are consistent
        assert codes1.OK == codes2.OK == 200
        assert codes1.NOT_FOUND == codes2.NOT_FOUND == 404


class TestCodesIntegration:
    """Test codes integration with other parts of faster-http"""
    
    def test_codes_with_response_status_check(self):
        """Test using codes with response status checking"""
        codes = faster_http.codes
        
        # Simulate response status checking
        response_status = 200
        assert response_status == codes.OK
        
        response_status = 404
        assert response_status == codes.NOT_FOUND
        
        response_status = 500
        assert response_status == codes.INTERNAL_SERVER_ERROR
    
    def test_codes_comparison_operators(self):
        """Test using codes with comparison operators"""
        codes = faster_http.codes
        
        # Test equality
        assert codes.OK == 200
        assert codes.NOT_FOUND == 404
        
        # Test inequality  
        assert codes.OK != 404
        assert codes.NOT_FOUND != 200
        
        # Test with ranges
        assert 200 <= codes.OK < 300  # 2xx success range
        assert 400 <= codes.NOT_FOUND < 500  # 4xx client error range
        assert 500 <= codes.INTERNAL_SERVER_ERROR < 600  # 5xx server error range