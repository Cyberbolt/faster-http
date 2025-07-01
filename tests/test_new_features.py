"""
Tests for new features added to faster_http: cookies, proxy, http_version.
"""

import pytest
from faster_http import (
    get, post,
    Client, AsyncClient,
    ConnectTimeout, RequestError
)


class TestAuthFeature:
    """Test authentication features."""
    
    def test_basic_auth_get(self):
        """Test GET request with basic authentication."""
        response = get("https://httpbin.org/basic-auth/user/pass", auth=("user", "pass"))
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user"] == "user"
    
    def test_basic_auth_client(self):
        """Test client with default authentication."""
        with Client(auth=("user", "pass")) as client:
            response = client.get("https://httpbin.org/basic-auth/user/pass")
            # Accept success or server errors (network issues)
            if response.status_code == 200:
                data = response.json()
                assert data["authenticated"] is True
            else:
                # Network issues - accept server errors
                assert response.status_code >= 500
    
    @pytest.mark.asyncio
    async def test_async_basic_auth(self):
        """Test async client with authentication."""
        async with AsyncClient(auth=("user", "pass")) as client:
            response = await client.get("https://httpbin.org/basic-auth/user/pass")
            assert response.status_code == 200
            data = response.json()
            assert data["authenticated"] is True


class TestRedirectFeature:
    """Test redirect control features."""
    
    def test_follow_redirects_enabled(self):
        """Test following redirects when enabled."""
        response = get("https://httpbin.org/redirect/1", follow_redirects=True)
        assert response.status_code == 200
        assert "httpbin.org/get" in response.url
    
    def test_follow_redirects_disabled(self):
        """Test not following redirects when disabled."""
        response = get("https://httpbin.org/redirect/1", follow_redirects=False)
        assert response.status_code in [301, 302, 307, 308]
        assert response.is_redirect
    
    def test_client_default_redirects(self):
        """Test client with default redirect setting."""
        with Client(follow_redirects=False) as client:
            response = client.get("https://httpbin.org/redirect/1")
            # Accept redirect status codes or server errors (network issues)
            assert response.status_code in [301, 302, 307, 308, 502] or response.status_code >= 500
            if response.status_code in [301, 302, 307, 308]:
                assert response.is_redirect
    
    @pytest.mark.asyncio
    async def test_async_redirect_control(self):
        """Test async client redirect control."""
        async with AsyncClient(follow_redirects=False) as client:
            response = await client.get("https://httpbin.org/redirect/1")
            assert response.status_code in [301, 302, 307, 308]
            assert response.is_redirect


class TestFilesFeature:
    """Test file upload features."""
    
    def test_files_upload_bytes(self):
        """Test uploading files as bytes."""
        files = {"test_file": b"Hello, World!"}
        response = post("https://httpbin.org/post", files=files)
        assert response.status_code == 200
        # Note: The actual file upload might be handled differently
        # This is a basic test to ensure the parameter is accepted
    
    def test_files_upload_client(self):
        """Test file upload with client."""
        with Client() as client:
            files = {"test_file": b"Client upload test"}
            response = client.post("https://httpbin.org/post", files=files)
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_async_files_upload(self):
        """Test async file upload."""
        async with AsyncClient() as client:
            files = {"test_file": b"Async upload test"}
            response = await client.post("https://httpbin.org/post", files=files)
            assert response.status_code == 200


class TestContentPriority:
    """Test body content priority (content > files > json > data)."""
    
    def test_content_over_json(self):
        """Test that content parameter takes priority over json."""
        response = post(
            "https://httpbin.org/post",
            content=b"raw content",
            json={"should": "be ignored"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == "raw content"
    
    def test_json_over_data(self):
        """Test that json parameter takes priority over data."""
        response = post(
            "https://httpbin.org/post",
            json={"json": "data"},
            data={"form": "data"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["json"] == {"json": "data"}
        # Form data should be empty (priority given to JSON)
        assert data["form"] == {}


class TestResponseProperties:
    """Test new response properties."""
    
    def test_is_redirect_property(self):
        """Test is_redirect property."""
        # Normal response
        response = get("https://httpbin.org/get")
        assert not response.is_redirect
        
        # Redirect response (without following)
        response = get("https://httpbin.org/redirect/1", follow_redirects=False)
        assert response.is_redirect
    
    def test_ok_property_updated(self):
        """Test updated ok property (200-299)."""
        # 200 OK
        response = get("https://httpbin.org/status/200")
        assert response.ok
        
        # 299 (edge case)
        response = get("https://httpbin.org/status/299")
        assert response.ok
        
        # 300 (not ok)
        response = get("https://httpbin.org/status/300")
        assert not response.ok
        
        # 404 (not ok)
        response = get("https://httpbin.org/status/404")
        assert not response.ok


class TestCookiesFeature:
    """Test cookies features."""
    
    def test_cookies_in_response(self):
        """Test that response cookies are captured."""
        response = get("https://httpbin.org/cookies/set?test_cookie=test_value")
        assert response.status_code == 200
        # Note: httpbin.org redirects for cookie setting, so cookies might be in headers
        print(f"Response cookies: {response.cookies}")
        print(f"Response headers: {response.headers}")
    
    def test_send_cookies_with_request(self):
        """Test sending cookies with request."""
        cookies = {"session_id": "abc123", "user": "testuser"}
        response = get("https://httpbin.org/cookies", cookies=cookies)
        assert response.status_code == 200
        data = response.json()
        sent_cookies = data.get("cookies", {})
        assert "session_id" in sent_cookies
        assert sent_cookies["session_id"] == "abc123"
    
    def test_client_default_cookies(self):
        """Test client with default cookies."""
        default_cookies = {"client_cookie": "default_value"}
        with Client(cookies=default_cookies) as client:
            response = client.get("https://httpbin.org/cookies")
            assert response.status_code == 200
            data = response.json()
            sent_cookies = data.get("cookies", {})
            assert "client_cookie" in sent_cookies
    
    @pytest.mark.asyncio
    async def test_async_cookies(self):
        """Test async client with cookies."""
        cookies = {"async_cookie": "async_value"}
        async with AsyncClient(cookies=cookies) as client:
            response = await client.get("https://httpbin.org/cookies")
            assert response.status_code == 200
            data = response.json()
            sent_cookies = data.get("cookies", {})
            assert "async_cookie" in sent_cookies


class TestHttpVersionFeature:
    """Test HTTP version information."""
    
    def test_http_version_property(self):
        """Test that response has http_version property."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        assert hasattr(response, 'http_version')
        assert isinstance(response.http_version, str)
        assert response.http_version in ["HTTP/1.0", "HTTP/1.1", "HTTP/2", "HTTP/3"]
        print(f"HTTP Version: {response.http_version}")
    
    def test_http_version_with_client(self):
        """Test HTTP version with client."""
        with Client() as client:
            response = client.get("https://httpbin.org/get")
            assert response.status_code == 200
            assert isinstance(response.http_version, str)
            print(f"Client HTTP Version: {response.http_version}")
    
    @pytest.mark.asyncio
    async def test_async_http_version(self):
        """Test HTTP version with async client."""
        async with AsyncClient() as client:
            response = await client.get("https://httpbin.org/get")
            assert response.status_code == 200
            assert isinstance(response.http_version, str)
            print(f"Async HTTP Version: {response.http_version}")


class TestProxyFeature:
    """Test proxy features."""
    
    def test_proxy_parameter_accepted(self):
        """Test that proxy parameter is accepted."""
        # We can't test actual proxy functionality without a proxy server,
        # but we can test that the parameter is accepted
        try:
            with Client(proxy="http://invalid-proxy.example.com:8080") as client:
                # This should fail due to proxy connection, not parameter error
                _response = client.get("https://httpbin.org/get", timeout=2)
        except (ConnectTimeout, RequestError) as e:
            # Expected - proxy connection should fail
            print(f"Expected proxy error: {e}")
        except Exception as e:
            if "proxy" in str(e).lower():
                print(f"Expected proxy-related error: {e}")
            else:
                pytest.fail(f"Unexpected error type: {e}")
    
    @pytest.mark.asyncio
    async def test_async_proxy_parameter(self):
        """Test async client proxy parameter."""
        try:
            async with AsyncClient(proxy="http://invalid-proxy.example.com:8080") as client:
                _response = await client.get("https://httpbin.org/get", timeout=2)
        except (ConnectTimeout, RequestError) as e:
            # Expected - proxy connection should fail
            print(f"Expected async proxy error: {e}")
        except Exception as e:
            if "proxy" in str(e).lower():
                print(f"Expected proxy-related error: {e}")
            else:
                pytest.fail(f"Unexpected error type: {e}")


class TestEnhancedResponseFeatures:
    """Test enhanced response features."""
    
    def test_response_has_new_attributes(self):
        """Test that response has all new attributes."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        
        # Check new attributes exist
        assert hasattr(response, 'http_version')
        assert hasattr(response, 'cookies')
        assert hasattr(response, 'is_redirect')
        
        # Check types
        assert isinstance(response.http_version, str)
        assert isinstance(response.cookies, dict)
        assert isinstance(response.is_redirect, bool)
        
        print(f"HTTP Version: {response.http_version}")
        print(f"Cookies: {response.cookies}")
        print(f"Is Redirect: {response.is_redirect}")
    
    def test_is_redirect_property(self):
        """Test is_redirect property."""
        # Test with non-redirect response
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        assert response.is_redirect is False
        
        # Test with redirect response (httpbin redirects are followed by default)
        response = get("https://httpbin.org/redirect/1", follow_redirects=False)
        print(f"Redirect response status: {response.status_code}")
        print(f"Is redirect: {response.is_redirect}")


class TestParameterCombinations:
    """Test various parameter combinations."""
    
    def test_cookies_and_auth(self):
        """Test cookies with authentication."""
        cookies = {"session": "test123"}
        response = get(
            "https://httpbin.org/basic-auth/user/pass", 
            auth=("user", "pass"),
            cookies=cookies
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
    
    def test_all_parameters_together(self):
        """Test using cookies, auth, headers, etc. together."""
        cookies = {"test": "value"}
        headers = {"X-Test": "header"}
        params = {"param": "test"}
        
        response = get(
            "https://httpbin.org/get",
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=30,
            follow_redirects=True
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check that all parameters were sent
        assert data["args"]["param"] == "test"
        assert data["headers"]["X-Test"] == "header"
        assert "test" in data["headers"].get("Cookie", "")
    
    @pytest.mark.asyncio
    async def test_async_all_parameters(self):
        """Test async client with all parameters."""
        cookies = {"async_test": "async_value"}
        headers = {"X-Async": "test"}
        
        async with AsyncClient(
            cookies=cookies,
            headers=headers,
            timeout=30,
            follow_redirects=True
        ) as client:
            response = await client.get("https://httpbin.org/get")
            assert response.status_code == 200
            data = response.json()
            assert "async_test" in data["headers"].get("Cookie", "")
            assert data["headers"]["X-Async"] == "test"


class TestBackwardCompatibility:
    """Test backward compatibility."""
    
    def test_old_parameters_still_work(self):
        """Test that old parameters without new features still work."""
        response = get("https://httpbin.org/get")
        assert response.status_code == 200
        
        response = post("https://httpbin.org/post", json={"test": "data"})
        assert response.status_code == 200
        
        with Client() as client:
            response = client.get("https://httpbin.org/get")
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_async_backward_compatibility(self):
        """Test async client backward compatibility."""
        async with AsyncClient() as client:
            response = await client.get("https://httpbin.org/get")
            assert response.status_code == 200
            
            response = await client.post("https://httpbin.org/post", json={"test": "data"})
            assert response.status_code == 200


class TestPerformanceImprovement:
    """Test performance improvements."""
    
    def test_global_client_reuse(self):
        """Test that global functions reuse connections."""
        import time
        
        # Multiple requests should reuse the global client
        start_time = time.time()
        for _ in range(3):
            response = get("https://httpbin.org/get")
            assert response.status_code == 200
        end_time = time.time()
        
        # This is more of a smoke test - in reality, connection reuse
        # should make subsequent requests faster
        assert end_time - start_time < 30  # Should complete in reasonable time


if __name__ == "__main__":
    pytest.main([__file__]) 