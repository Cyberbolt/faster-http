"""
Integration tests for features ensuring httpx compatibility.
Tests Client constructor, Response methods, and Request constructor compatibility.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import asyncio

import httpx

import faster_http


class TestIntegratedFeatures:
    """Test integrated features ensuring httpx compatibility - httpx vs faster_http comparison."""

    def test_client_comprehensive_parameters_comparison(self, stable_server):
        """Test Client with comprehensive parameters - httpx vs faster_http."""
        base_url = stable_server.base_url
        headers = {"User-Agent": "integration-test", "X-Test": "true"}
        params = {"test": "integration", "version": "v1"}
        timeout = 10.0

        # First test httpx Client with comprehensive parameters
        httpx_client = httpx.Client(
            base_url=base_url, timeout=timeout, headers=headers, params=params, follow_redirects=True
        )

        # Test httpx request processing
        httpx_response = httpx_client.get("/get")
        assert httpx_response.status_code == 200
        httpx_data = httpx_response.json()

        # Verify httpx processed parameters correctly
        assert "query_params" in httpx_data
        assert httpx_data["query_params"]["test"] == "integration"
        assert httpx_data["query_params"]["version"] == "v1"
        assert "headers" in httpx_data
        assert httpx_data["headers"]["User-Agent"] == "integration-test"
        assert httpx_data["headers"]["X-Test"] == "true"

        httpx_client.close()

        # Then test faster_http Client with same parameters (should match httpx exactly)
        faster_client = faster_http.Client(
            base_url=base_url, timeout=timeout, headers=headers, params=params, follow_redirects=True
        )

        # Test faster_http request processing (should match httpx)
        faster_response = faster_client.get("/get")
        assert faster_response.status_code == 200
        faster_data = faster_response.json()

        # Verify faster_http processed parameters identically to httpx
        assert "query_params" in faster_data
        assert faster_data["query_params"]["test"] == "integration"
        assert faster_data["query_params"]["version"] == "v1"
        assert "headers" in faster_data
        assert faster_data["headers"]["User-Agent"] == "integration-test"
        assert faster_data["headers"]["X-Test"] == "true"

        # Both should produce identical results
        assert httpx_response.status_code == faster_response.status_code
        assert httpx_data["query_params"] == faster_data["query_params"]
        assert httpx_data["headers"]["User-Agent"] == faster_data["headers"]["User-Agent"]
        assert httpx_data["headers"]["X-Test"] == faster_data["headers"]["X-Test"]

        faster_client.close()

    def test_response_methods_comprehensive_comparison(self, stable_server):
        """Test Response methods comprehensively - httpx vs faster_http."""
        url = stable_server.url("/json")

        # First test httpx Response methods
        httpx_response = httpx.get(url)
        assert httpx_response.status_code == 200

        # Test all httpx Response methods and properties
        httpx_json = httpx_response.json()
        httpx_text = httpx_response.text
        httpx_content = httpx_response.content
        httpx_url = httpx_response.url
        httpx_encoding = httpx_response.encoding

        # Test httpx boolean properties
        assert httpx_response.is_success

        # Test httpx status classification methods if they exist
        httpx_is_client_error = getattr(httpx_response, "is_client_error", False)
        httpx_is_server_error = getattr(httpx_response, "is_server_error", False)
        httpx_is_redirect = httpx_response.is_redirect

        # Then test faster_http Response methods (should match httpx exactly)
        faster_response = faster_http.get(url)
        assert faster_response.status_code == 200

        # Test all faster_http Response methods and properties (should match httpx)
        faster_json = faster_response.json()
        faster_text = faster_response.text
        faster_content = faster_response.content
        faster_url = faster_response.url
        faster_encoding = faster_response.encoding

        # Test faster_http boolean properties (should match httpx)
        assert faster_response.is_success

        # Test faster_http status classification methods (should match httpx)
        faster_is_client_error = getattr(faster_response, "is_client_error", False)
        faster_is_server_error = getattr(faster_response, "is_server_error", False)
        faster_is_redirect = faster_response.is_redirect

        # Both should produce identical results
        assert httpx_response.status_code == faster_response.status_code
        assert httpx_json == faster_json
        assert httpx_text == faster_text
        assert httpx_content == faster_content
        assert str(httpx_url) == str(faster_url)
        assert httpx_encoding == faster_encoding

        # Boolean properties should match
        assert httpx_response.is_success == faster_response.is_success
        assert httpx_is_client_error == faster_is_client_error
        assert httpx_is_server_error == faster_is_server_error
        assert httpx_is_redirect == faster_is_redirect

    def test_request_construction_comprehensive_comparison(self, stable_server):
        """Test comprehensive Request construction - httpx vs faster_http."""
        url = stable_server.url("/post")
        method = "POST"
        headers = {"Content-Type": "application/json", "X-Custom": "test"}
        json_data = {"message": "integration test", "number": 42}

        # First test httpx Request construction
        httpx_request = httpx.Request(method=method, url=url, headers=headers, json=json_data)

        # Test httpx Request properties
        assert httpx_request.method == method
        assert str(httpx_request.url) == url
        assert "Content-Type" in httpx_request.headers
        assert "X-Custom" in httpx_request.headers
        assert httpx_request.headers["Content-Type"] == "application/json"
        assert httpx_request.headers["X-Custom"] == "test"

        # Send httpx request
        with httpx.Client() as httpx_client:
            httpx_response = httpx_client.send(httpx_request)
            assert httpx_response.status_code == 200
            httpx_response_data = httpx_response.json()

        # Then test faster_http Request construction (should match httpx exactly)
        faster_request = faster_http.Request(method=method, url=url, headers=headers, json=json_data)

        # Test faster_http Request properties (should match httpx)
        assert faster_request.method == method
        assert faster_request.url == url
        assert "Content-Type" in faster_request.headers
        assert "X-Custom" in faster_request.headers
        assert faster_request.headers["Content-Type"] == "application/json"
        assert faster_request.headers["X-Custom"] == "test"

        # Send faster_http request
        with faster_http.Client() as faster_client:
            faster_response = faster_client.send(faster_request)
            assert faster_response.status_code == 200
            faster_response_data = faster_response.json()

        # Both should produce identical results
        assert httpx_response.status_code == faster_response.status_code
        assert httpx_request.method == faster_request.method
        assert str(httpx_request.url) == faster_request.url
        assert httpx_request.headers["Content-Type"] == faster_request.headers["Content-Type"]
        assert httpx_request.headers["X-Custom"] == faster_request.headers["X-Custom"]

        # Response data should be identical
        assert "json" in httpx_response_data
        assert "json" in faster_response_data
        assert httpx_response_data["json"] == faster_response_data["json"]
        assert httpx_response_data["json"]["message"] == faster_response_data["json"]["message"]
        assert httpx_response_data["json"]["number"] == faster_response_data["json"]["number"]

    def test_streaming_comprehensive_comparison(self, stable_server):
        """Test comprehensive streaming functionality - httpx vs faster_http."""
        url = stable_server.url("/stream/3")

        # First test httpx streaming
        with httpx.stream("GET", url) as httpx_stream:
            assert httpx_stream.status_code == 200

            # Test httpx streaming iteration
            httpx_chunks = []
            for chunk in httpx_stream.iter_bytes():
                httpx_chunks.append(chunk)

            # Test httpx stream properties
            httpx_url = httpx_stream.url
            httpx_status = httpx_stream.status_code

        # Reconstruct content from httpx chunks
        httpx_full_content = b"".join(httpx_chunks)

        # Then test faster_http streaming (should match httpx exactly)
        with faster_http.stream("GET", url) as faster_stream:
            assert faster_stream.status_code == 200

            # Test faster_http streaming iteration
            faster_chunks = []
            for chunk in faster_stream.iter_bytes():
                faster_chunks.append(chunk)

            # Test faster_http stream properties (should match httpx)
            faster_url = faster_stream.url
            faster_status = faster_stream.status_code

        # Reconstruct content from faster_http chunks
        faster_full_content = b"".join(faster_chunks)

        # Both should produce identical results
        assert httpx_status == faster_status
        assert str(httpx_url) == str(faster_url)
        assert len(httpx_chunks) > 0 and len(faster_chunks) > 0
        assert len(httpx_full_content) > 0 and len(faster_full_content) > 0

        # Both should contain valid JSON content structure
        import json

        httpx_json = json.loads(httpx_full_content.decode())
        faster_json = json.loads(faster_full_content.decode())

        # Structure should be identical
        assert "method" in httpx_json and "method" in faster_json
        assert httpx_json["method"] == faster_json["method"] == "GET"

    def test_authentication_comprehensive_comparison(self, stable_server):
        """Test comprehensive authentication - httpx vs faster_http."""
        url = stable_server.url("/get")
        username = "testuser"
        password = "testpass"

        # First test httpx with BasicAuth
        httpx_auth = httpx.BasicAuth(username, password)
        httpx_response = httpx.get(url, auth=httpx_auth)
        assert httpx_response.status_code == 200
        httpx_data = httpx_response.json()

        # Test httpx auth properties - httpx.BasicAuth doesn't expose username/password
        # but we can verify it has _auth_header
        assert hasattr(httpx_auth, "_auth_header")

        # Check that httpx added Authorization header
        assert "headers" in httpx_data
        assert "Authorization" in httpx_data["headers"]
        httpx_auth_header = httpx_data["headers"]["Authorization"]

        # Then test faster_http with BasicAuth (should match httpx exactly)
        faster_auth = faster_http.BasicAuth(username, password)
        faster_response = faster_http.get(url, auth=faster_auth)
        assert faster_response.status_code == 200
        faster_data = faster_response.json()

        # Test faster_http auth properties (should match httpx)
        assert faster_auth.username == username
        assert faster_auth.password == password

        # Check that faster_http added Authorization header (same as httpx)
        assert "headers" in faster_data
        assert "Authorization" in faster_data["headers"]
        faster_auth_header = faster_data["headers"]["Authorization"]

        # Both should produce identical authentication
        assert httpx_response.status_code == faster_response.status_code
        # Compare auth headers instead of object attributes since httpx.BasicAuth
        # doesn't expose username/password while faster_http.BasicAuth does
        assert httpx_auth_header == faster_auth_header

        # Test that faster_http BasicAuth has expected attributes (unlike httpx)
        assert faster_auth.username == username
        assert faster_auth.password == password

    def test_error_handling_comprehensive_comparison(self, stable_server):
        """Test comprehensive error handling - httpx vs faster_http."""
        # Test 404 error handling
        not_found_url = stable_server.url("/nonexistent")

        # First test httpx error handling
        httpx_response = httpx.get(not_found_url)
        assert httpx_response.status_code == 404

        # Test httpx error properties
        httpx_is_client_error = getattr(
            httpx_response, "is_client_error", httpx_response.status_code >= 400 and httpx_response.status_code < 500
        )
        httpx_is_success = httpx_response.is_success

        # Test httpx raise_for_status
        try:
            httpx_response.raise_for_status()
            httpx_raises_error = False
        except httpx.HTTPStatusError as e:
            httpx_raises_error = True
            httpx_error_status = e.response.status_code

        # Then test faster_http error handling (should match httpx exactly)
        faster_response = faster_http.get(not_found_url)
        assert faster_response.status_code == 404

        # Test faster_http error properties (should match httpx)
        faster_is_client_error = getattr(
            faster_response, "is_client_error", faster_response.status_code >= 400 and faster_response.status_code < 500
        )
        faster_is_success = getattr(
            faster_response, "is_success", faster_response.status_code >= 200 and faster_response.status_code < 300
        )

        # Test faster_http raise_for_status (should match httpx)
        try:
            faster_response.raise_for_status()
            faster_raises_error = False
        except faster_http.HTTPStatusError as e:
            faster_raises_error = True
            faster_error_status = e.response.status_code

        # Both should handle errors identically
        assert httpx_response.status_code == faster_response.status_code
        assert httpx_is_client_error == faster_is_client_error
        assert httpx_is_success == faster_is_success
        assert httpx_raises_error == faster_raises_error

        if httpx_raises_error and faster_raises_error:
            assert httpx_error_status == faster_error_status

    def test_async_integration_comprehensive_comparison(self, stable_server):
        """Test comprehensive async integration - httpx vs faster_http."""

        async def test_async_integration():
            url = stable_server.url("/json")

            # First test httpx AsyncClient
            async with httpx.AsyncClient() as httpx_client:
                httpx_response = await httpx_client.get(url)
                assert httpx_response.status_code == 200

                httpx_json = httpx_response.json()
                httpx_url = httpx_response.url

            # Then test faster_http AsyncClient (should match httpx exactly)
            async with faster_http.AsyncClient() as faster_client:
                faster_response = await faster_client.get(url)
                assert faster_response.status_code == 200

                faster_json = faster_response.json()
                faster_url = faster_response.url

            # Both should produce identical results
            assert httpx_response.status_code == faster_response.status_code
            assert httpx_json == faster_json
            assert str(httpx_url) == str(faster_url)

            # Both should handle async context managers identically
            assert httpx_response.status_code == 200
            assert faster_response.status_code == 200

        asyncio.run(test_async_integration())

    def test_interface_consistency_comprehensive_comparison(self, stable_server):
        """Test comprehensive interface consistency - httpx vs faster_http."""
        # Test that faster_http doesn't have extra interfaces that httpx doesn't have
        url = stable_server.url("/json")

        # Create instances for comprehensive interface comparison
        httpx_response = httpx.get(url)
        faster_response = faster_http.get(url)

        # Get all public methods and properties
        httpx_attrs = {attr for attr in dir(httpx_response) if not attr.startswith("_")}
        faster_attrs = {attr for attr in dir(faster_response) if not attr.startswith("_")}

        # faster_http should not have attributes that httpx doesn't have
        extra_attrs = faster_attrs - httpx_attrs
        assert len(extra_attrs) == 0, (
            f"faster_http Response has extra attributes that httpx Response doesn't have: {extra_attrs}"
        )

        # Test Client interface consistency
        httpx_client = httpx.Client()
        faster_client = faster_http.Client()

        httpx_client_attrs = {attr for attr in dir(httpx_client) if not attr.startswith("_")}
        faster_client_attrs = {attr for attr in dir(faster_client) if not attr.startswith("_")}

        extra_client_attrs = faster_client_attrs - httpx_client_attrs
        assert len(extra_client_attrs) == 0, (
            f"faster_http Client has extra attributes that httpx Client doesn't have: {extra_client_attrs}"
        )

        httpx_client.close()
        faster_client.close()

        # Test module-level interface consistency
        {attr for attr in dir(httpx) if not attr.startswith("_")}
        {attr for attr in dir(faster_http) if not attr.startswith("_")}

        # Check that essential httpx attributes exist in faster_http
        essential_attrs = {
            "Client",
            "AsyncClient",
            "Request",
            "Response",
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
            "BasicAuth",
        }
        for attr in essential_attrs:
            if hasattr(httpx, attr):
                assert hasattr(faster_http, attr), f"faster_http missing essential httpx attribute: {attr}"
