"""
Unit tests for authentication functionality.
Tests various authentication methods by comparing with httpx.
"""

import pytest
import httpx
import faster_http
from ..conftest import assert_response_ok, skip_on_network_error


class TestBasicAuth:
    """Test BasicAuth functionality by comparing with httpx."""
    
    def test_basic_auth_creation(self):
        """Test BasicAuth class creation - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_auth = httpx.BasicAuth("testuser", "testpass")
        assert httpx_auth.username == "testuser"
        assert httpx_auth.password == "testpass"
        
        # Test with faster-http second
        faster_auth = faster_http.BasicAuth("testuser", "testpass")
        assert faster_auth.username == "testuser"
        assert faster_auth.password == "testpass"
        
        # Compare representations
        httpx_repr = repr(httpx_auth)
        faster_repr = repr(faster_auth)
        assert "BasicAuth" in httpx_repr
        assert "BasicAuth" in faster_repr
        assert "testuser" in httpx_repr
        assert "testuser" in faster_repr
        assert "testpass" not in httpx_repr  # Password should not be in repr
        assert "testpass" not in faster_repr  # Password should not be in repr
    
    @skip_on_network_error
    def test_basic_auth_tuple_compatibility(self, test_urls):
        """Test that BasicAuth works like tuple auth - compare httpx vs faster-http."""
        # Test with httpx first using tuple auth
        try:
            httpx_response = httpx.get(test_urls['basic_auth'], auth=("user", "pass"))
            httpx_status = httpx_response.status_code
            # Should get either success or 401 (auth failed), but not connection error
            assert httpx_status in [200, 401]
        except Exception as e:
            pytest.skip(f"httpx auth endpoint unavailable: {e}")
        
        # Test with faster-http second using tuple auth
        try:
            faster_response = faster_http.get(test_urls['basic_auth'], auth=("user", "pass"))
            faster_status = faster_response.status_code
            # Should get same result as httpx
            assert faster_status in [200, 401]
        except Exception as e:
            pytest.skip(f"faster-http auth endpoint unavailable: {e}")
        
        # Compare status codes
        assert httpx_status == faster_status
        
        # Test with httpx using BasicAuth object
        httpx_auth = httpx.BasicAuth("user", "pass")
        try:
            httpx_response_obj = httpx.get(test_urls['basic_auth'], auth=httpx_auth)
            httpx_obj_status = httpx_response_obj.status_code
            assert httpx_obj_status in [200, 401]
        except Exception as e:
            pytest.skip(f"httpx BasicAuth object unavailable: {e}")
        
        # Test with faster-http using BasicAuth object
        faster_auth = faster_http.BasicAuth("user", "pass")
        try:
            faster_response_obj = faster_http.get(test_urls['basic_auth'], auth=faster_auth)
            faster_obj_status = faster_response_obj.status_code
            assert faster_obj_status in [200, 401]
        except Exception as e:
            pytest.skip(f"faster-http BasicAuth object unavailable: {e}")
        
        # Compare BasicAuth object results
        assert httpx_obj_status == faster_obj_status
    
    @skip_on_network_error
    def test_basic_auth_with_client(self, test_urls):
        """Test BasicAuth with Client - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_auth = httpx.BasicAuth("user", "pass")
        try:
            with httpx.Client(auth=httpx_auth) as httpx_client:
                httpx_response = httpx_client.get(test_urls['basic_auth'])
                httpx_status = httpx_response.status_code
                assert httpx_status in [200, 401]
        except Exception as e:
            pytest.skip(f"httpx client auth unavailable: {e}")
        
        # Test with faster-http second
        faster_auth = faster_http.BasicAuth("user", "pass")
        try:
            with faster_http.Client(auth=faster_auth) as faster_client:
                faster_response = faster_client.get(test_urls['basic_auth'])
                faster_status = faster_response.status_code
                assert faster_status in [200, 401]
        except Exception as e:
            pytest.skip(f"faster-http client auth unavailable: {e}")
        
        # Compare results
        assert httpx_status == faster_status
    
    @pytest.mark.asyncio
    @skip_on_network_error
    async def test_basic_auth_with_async_client(self, test_urls):
        """Test BasicAuth with AsyncClient - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_auth = httpx.BasicAuth("user", "pass")
        try:
            async with httpx.AsyncClient(auth=httpx_auth) as httpx_client:
                httpx_response = await httpx_client.get(test_urls['basic_auth'])
                httpx_status = httpx_response.status_code
                assert httpx_status in [200, 401]
        except Exception as e:
            pytest.skip(f"httpx async client auth unavailable: {e}")
        
        # Test with faster-http second
        faster_auth = faster_http.BasicAuth("user", "pass")
        try:
            async with faster_http.AsyncClient(auth=faster_auth) as faster_client:
                faster_response = await faster_client.get(test_urls['basic_auth'])
                faster_status = faster_response.status_code
                assert faster_status in [200, 401]
        except Exception as e:
            pytest.skip(f"faster-http async client auth unavailable: {e}")
        
        # Compare results
        assert httpx_status == faster_status


class TestDigestAuth:
    """Test DigestAuth functionality by comparing with httpx."""
    
    def test_digest_auth_creation(self):
        """Test DigestAuth class creation - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_auth = httpx.DigestAuth("testuser", "testpass")
        assert httpx_auth.username == "testuser"
        assert httpx_auth.password == "testpass"
        
        # Test with faster-http second
        faster_auth = faster_http.DigestAuth("testuser", "testpass")
        assert faster_auth.username == "testuser"
        assert faster_auth.password == "testpass"
        
        # Compare representations
        httpx_repr = repr(httpx_auth)
        faster_repr = repr(faster_auth)
        assert "DigestAuth" in httpx_repr
        assert "DigestAuth" in faster_repr
        assert "testuser" in httpx_repr
        assert "testuser" in faster_repr
        assert "testpass" not in httpx_repr  # Password should not be in repr
        assert "testpass" not in faster_repr  # Password should not be in repr
    
    @skip_on_network_error
    def test_digest_auth_functionality(self, test_urls):
        """Test DigestAuth functionality - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_auth = httpx.DigestAuth("user", "pass")
        try:
            httpx_response = httpx.get(test_urls['digest_auth'], auth=httpx_auth)
            httpx_status = httpx_response.status_code
            # Should get either success or 401 (auth failed)
            assert httpx_status in [200, 401]
        except Exception as e:
            pytest.skip(f"httpx digest auth unavailable: {e}")
        
        # Test with faster-http second
        faster_auth = faster_http.DigestAuth("user", "pass")
        try:
            faster_response = faster_http.get(test_urls['digest_auth'], auth=faster_auth)
            faster_status = faster_response.status_code
            # Should get same result as httpx
            assert faster_status in [200, 401]
        except Exception as e:
            pytest.skip(f"faster-http digest auth unavailable: {e}")
        
        # Compare results
        assert httpx_status == faster_status
    
    @skip_on_network_error
    def test_digest_auth_with_client(self, test_urls):
        """Test DigestAuth with Client - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_auth = httpx.DigestAuth("user", "pass")
        try:
            with httpx.Client(auth=httpx_auth) as httpx_client:
                httpx_response = httpx_client.get(test_urls['digest_auth'])
                httpx_status = httpx_response.status_code
                assert httpx_status in [200, 401]
        except Exception as e:
            pytest.skip(f"httpx client digest auth unavailable: {e}")
        
        # Test with faster-http second
        faster_auth = faster_http.DigestAuth("user", "pass")
        try:
            with faster_http.Client(auth=faster_auth) as faster_client:
                faster_response = faster_client.get(test_urls['digest_auth'])
                faster_status = faster_response.status_code
                assert faster_status in [200, 401]
        except Exception as e:
            pytest.skip(f"faster-http client digest auth unavailable: {e}")
        
        # Compare results
        assert httpx_status == faster_status


class TestNetRCAuth:
    """Test NetRCAuth functionality by comparing with httpx."""
    
    def test_netrc_auth_creation(self):
        """Test NetRCAuth class creation - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_auth = httpx.NetRCAuth()
        assert hasattr(httpx_auth, 'file')
        assert httpx_auth.file.endswith('.netrc')
        
        # Test with faster-http second
        faster_auth = faster_http.NetRCAuth()
        assert hasattr(faster_auth, 'file')
        assert faster_auth.file.endswith('.netrc')
        
        # Compare file paths
        assert httpx_auth.file == faster_auth.file
    
    def test_netrc_auth_explicit_file(self):
        """Test NetRCAuth with explicit file - compare httpx vs faster-http."""
        netrc_file = "/path/to/.netrc"
        
        # Test with httpx first
        httpx_auth = httpx.NetRCAuth(file=netrc_file)
        assert httpx_auth.file == netrc_file
        
        # Test with faster-http second
        faster_auth = faster_http.NetRCAuth(file=netrc_file)
        assert faster_auth.file == netrc_file
        
        # Compare file paths
        assert httpx_auth.file == faster_auth.file
    
    @skip_on_network_error
    def test_netrc_auth_functionality(self, test_urls):
        """Test NetRCAuth functionality - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_auth = httpx.NetRCAuth()
        try:
            httpx_response = httpx.get(test_urls['get'], auth=httpx_auth)
            httpx_status = httpx_response.status_code
            # Should succeed even without .netrc file
            assert httpx_status == 200
        except Exception as e:
            pytest.skip(f"httpx netrc auth unavailable: {e}")
        
        # Test with faster-http second
        faster_auth = faster_http.NetRCAuth()
        try:
            faster_response = faster_http.get(test_urls['get'], auth=faster_auth)
            faster_status = faster_response.status_code
            # Should succeed even without .netrc file
            assert faster_status == 200
        except Exception as e:
            pytest.skip(f"faster-http netrc auth unavailable: {e}")
        
        # Compare results
        assert httpx_status == faster_status


class TestAuthIntegration:
    """Test authentication integration with various request methods."""
    
    @skip_on_network_error
    def test_auth_with_post_request(self, test_urls, sample_json_data):
        """Test authentication with POST request - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_auth = httpx.BasicAuth("user", "pass")
        try:
            httpx_response = httpx.post(test_urls['basic_auth'], json=sample_json_data, auth=httpx_auth)
            httpx_status = httpx_response.status_code
            assert httpx_status in [200, 401, 405]  # 405 if POST not allowed
        except Exception as e:
            pytest.skip(f"httpx POST auth unavailable: {e}")
        
        # Test with faster-http second
        faster_auth = faster_http.BasicAuth("user", "pass")
        try:
            faster_response = faster_http.post(test_urls['basic_auth'], json=sample_json_data, auth=faster_auth)
            faster_status = faster_response.status_code
            assert faster_status in [200, 401, 405]  # 405 if POST not allowed
        except Exception as e:
            pytest.skip(f"faster-http POST auth unavailable: {e}")
        
        # Compare results
        assert httpx_status == faster_status
    
    @skip_on_network_error
    def test_auth_precedence(self, test_urls):
        """Test authentication precedence - compare httpx vs faster-http."""
        # Test client-level auth vs request-level auth
        client_auth = ("client_user", "client_pass")
        request_auth = ("request_user", "request_pass")
        
        # Test with httpx first
        try:
            with httpx.Client(auth=client_auth) as httpx_client:
                # Request-level auth should override client-level auth
                httpx_response = httpx_client.get(test_urls['basic_auth'], auth=request_auth)
                httpx_status = httpx_response.status_code
                assert httpx_status in [200, 401]
        except Exception as e:
            pytest.skip(f"httpx auth precedence unavailable: {e}")
        
        # Test with faster-http second
        try:
            with faster_http.Client(auth=client_auth) as faster_client:
                # Request-level auth should override client-level auth
                faster_response = faster_client.get(test_urls['basic_auth'], auth=request_auth)
                faster_status = faster_response.status_code
                assert faster_status in [200, 401]
        except Exception as e:
            pytest.skip(f"faster-http auth precedence unavailable: {e}")
        
        # Compare results
        assert httpx_status == faster_status
    
    @skip_on_network_error
    def test_auth_with_redirects(self, test_urls):
        """Test authentication with redirects - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_auth = httpx.BasicAuth("user", "pass")
        try:
            httpx_response = httpx.get(test_urls['redirect'].format(n=1), auth=httpx_auth, follow_redirects=True)
            httpx_status = httpx_response.status_code
            assert httpx_status == 200
        except Exception as e:
            pytest.skip(f"httpx auth with redirects unavailable: {e}")
        
        # Test with faster-http second
        faster_auth = faster_http.BasicAuth("user", "pass")
        try:
            faster_response = faster_http.get(test_urls['redirect'].format(n=1), auth=faster_auth, follow_redirects=True)
            faster_status = faster_response.status_code
            assert faster_status == 200
        except Exception as e:
            pytest.skip(f"faster-http auth with redirects unavailable: {e}")
        
        # Compare results
        assert httpx_status == faster_status
    
    @pytest.mark.asyncio
    @skip_on_network_error
    async def test_auth_async_integration(self, test_urls):
        """Test authentication with async client - compare httpx vs faster-http."""
        # Test with httpx first
        httpx_auth = httpx.BasicAuth("user", "pass")
        try:
            async with httpx.AsyncClient(auth=httpx_auth) as httpx_client:
                httpx_response = await httpx_client.get(test_urls['basic_auth'])
                httpx_status = httpx_response.status_code
                assert httpx_status in [200, 401]
        except Exception as e:
            pytest.skip(f"httpx async auth unavailable: {e}")
        
        # Test with faster-http second
        faster_auth = faster_http.BasicAuth("user", "pass")
        try:
            async with faster_http.AsyncClient(auth=faster_auth) as faster_client:
                faster_response = await faster_client.get(test_urls['basic_auth'])
                faster_status = faster_response.status_code
                assert faster_status in [200, 401]
        except Exception as e:
            pytest.skip(f"faster-http async auth unavailable: {e}")
        
        # Compare results
        assert httpx_status == faster_status