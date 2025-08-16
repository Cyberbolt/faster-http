"""
Basic integration tests for faster-http functionality.
Tests real HTTP requests comparing httpx and faster-http behavior.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx

import faster_http


class TestBasicIntegration:
    """Test basic integration functionality - httpx vs faster_http comparison."""

    def test_library_import_comparison(self):
        """Test that both libraries have the same interface - httpx vs faster_http."""
        # First check httpx expected attributes
        expected_attrs = [
            "Client",
            "AsyncClient",
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
            "request",
        ]

        for attr in expected_attrs:
            assert hasattr(httpx, attr), f"httpx missing {attr}"

        # Test that httpx attributes are callable
        for attr in ["get", "post", "put", "patch", "delete", "head", "options", "request"]:
            assert callable(getattr(httpx, attr))

        # Then check faster_http has same attributes as httpx
        for attr in expected_attrs:
            assert hasattr(faster_http, attr), f"faster_http missing {attr} that httpx has"

        # Test that faster_http attributes are callable like httpx
        for attr in ["get", "post", "put", "patch", "delete", "head", "options", "request"]:
            assert callable(getattr(faster_http, attr))

    def test_auth_objects_creation_comparison(self):
        """Test authentication objects creation - httpx vs faster_http."""
        # First test httpx BasicAuth
        httpx_basic = httpx.BasicAuth("user", "pass")
        assert httpx_basic is not None
        assert hasattr(httpx_basic, "auth_flow")

        # Then test faster_http BasicAuth (should match httpx)
        faster_basic = faster_http.BasicAuth("user", "pass")
        assert faster_basic is not None
        assert hasattr(faster_basic, "auth_flow")

        # First test httpx DigestAuth
        httpx_digest = httpx.DigestAuth("user", "pass")
        assert httpx_digest is not None
        assert hasattr(httpx_digest, "auth_flow")

        # Then test faster_http DigestAuth (should match httpx)
        faster_digest = faster_http.DigestAuth("user", "pass")
        assert faster_digest is not None
        assert hasattr(faster_digest, "auth_flow")

        # Test NetRCAuth comparison (skip if no .netrc file)
        try:
            # First test httpx NetRCAuth
            httpx_netrc = httpx.NetRCAuth()
            assert httpx_netrc is not None
            assert hasattr(httpx_netrc, "auth_flow")

            # Then test faster_http NetRCAuth (should match httpx)
            faster_netrc = faster_http.NetRCAuth()
            assert faster_netrc is not None
            assert hasattr(faster_netrc, "auth_flow")
        except FileNotFoundError:
            # No .netrc file available, skip this part of the test
            pass

    def test_client_creation_with_config_comparison(self, stable_server):
        """Test client creation with configurations - httpx vs faster_http."""
        base_url = stable_server.base_url

        # First test httpx Client creation
        httpx_client = httpx.Client(timeout=5.0)
        assert httpx_client is not None

        # Test httpx client request
        httpx_response = httpx_client.get(f"{base_url}/get")
        assert httpx_response.status_code == 200

        httpx_client.close()

        # Then test faster_http Client creation (should match httpx)
        faster_client = faster_http.Client(timeout=5.0)
        assert faster_client is not None

        # Test faster_http client request (should match httpx behavior)
        faster_response = faster_client.get(f"{base_url}/get")
        assert faster_response.status_code == 200

        # Both should produce the same result
        assert httpx_response.status_code == faster_response.status_code

        faster_client.close()

        # Test client with base URL - httpx first
        with httpx.Client(base_url=base_url, timeout=5.0) as httpx_client:
            assert httpx_client.base_url is not None
            httpx_response = httpx_client.get("/get")
            assert httpx_response.status_code == 200

        # Then test faster_http with base URL (should match httpx)
        with faster_http.Client(base_url=base_url, timeout=5.0) as faster_client:
            assert faster_client.base_url == httpx_client.base_url
            faster_response = faster_client.get("/get")
            assert faster_response.status_code == 200

        # Both should produce the same result
        assert httpx_response.status_code == faster_response.status_code

    def test_real_http_requests_comparison(self, stable_server):
        """Test real HTTP requests - httpx vs faster_http."""
        base_url = stable_server.base_url

        # First test httpx GET request
        get_url = f"{base_url}/get"
        httpx_get = httpx.get(get_url, timeout=5.0)
        assert httpx_get.status_code == 200
        assert httpx_get.is_success

        # Test httpx JSON parsing
        httpx_json = httpx_get.json()
        assert httpx_json["method"] == "GET"
        assert httpx_json["path"] == "/get"

        # Then test faster_http GET request (should match httpx exactly)
        faster_get = faster_http.get(get_url, timeout=5.0)
        assert faster_get.status_code == 200
        assert faster_get.is_success

        # Test faster_http JSON parsing (should match httpx)
        faster_json = faster_get.json()
        assert faster_json["method"] == "GET"
        assert faster_json["path"] == "/get"

        # Both should produce identical results
        assert httpx_get.status_code == faster_get.status_code
        assert httpx_get.is_success == faster_get.is_success
        assert httpx_json["method"] == faster_json["method"]
        assert httpx_json["path"] == faster_json["path"]

        # Test POST request with JSON - httpx first
        post_url = f"{base_url}/post"
        test_data = {"test": "data", "number": 42}

        httpx_post = httpx.post(post_url, json=test_data, timeout=5.0)
        assert httpx_post.status_code == 200

        httpx_post_json = httpx_post.json()
        assert httpx_post_json["method"] == "POST"
        assert httpx_post_json["json"] == test_data

        # Then test faster_http POST request (should match httpx exactly)
        faster_post = faster_http.post(post_url, json=test_data, timeout=5.0)
        assert faster_post.status_code == 200

        faster_post_json = faster_post.json()
        assert faster_post_json["method"] == "POST"
        assert faster_post_json["json"] == test_data

        # Both should produce identical results
        assert httpx_post.status_code == faster_post.status_code
        assert httpx_post_json["method"] == faster_post_json["method"]
        assert httpx_post_json["json"] == faster_post_json["json"]

    def test_async_client_creation_comparison(self):
        """Test async client creation - httpx vs faster_http."""
        # First test httpx AsyncClient creation
        httpx_async_client = httpx.AsyncClient()
        assert httpx_async_client is not None

        # Then test faster_http AsyncClient creation (should match httpx)
        faster_async_client = faster_http.AsyncClient()
        assert faster_async_client is not None

        # Test httpx AsyncClient with base URL
        httpx_client_with_base = httpx.AsyncClient(base_url="https://api.test.local")
        assert httpx_client_with_base.base_url == "https://api.test.local"

        # Test faster_http AsyncClient with base URL (should match httpx)
        faster_client_with_base = faster_http.AsyncClient(base_url="https://api.test.local")
        assert faster_client_with_base.base_url == "https://api.test.local"

        # Both should have the same base URL
        assert httpx_client_with_base.base_url == faster_client_with_base.base_url

        # Test httpx AsyncClient with headers
        headers = {"Authorization": "Bearer token"}
        httpx_client_with_headers = httpx.AsyncClient(headers=headers)
        assert hasattr(httpx_client_with_headers, "headers") or hasattr(httpx_client_with_headers, "_headers")

        # Test faster_http AsyncClient with headers (should match httpx)
        faster_client_with_headers = faster_http.AsyncClient(headers=headers)
        assert hasattr(faster_client_with_headers, "headers") or hasattr(faster_client_with_headers, "_headers")

        # Test httpx AsyncClient with timeout
        httpx_client_with_timeout = httpx.AsyncClient(timeout=30.0)
        assert httpx_client_with_timeout is not None

        # Test faster_http AsyncClient with timeout (should match httpx)
        faster_client_with_timeout = faster_http.AsyncClient(timeout=30.0)
        assert faster_client_with_timeout is not None

        # Test httpx AsyncClient with auth
        auth = httpx.BasicAuth("user", "pass")
        httpx_client_with_auth = httpx.AsyncClient(auth=auth)
        assert hasattr(httpx_client_with_auth, "auth") or hasattr(httpx_client_with_auth, "_auth")

        # Test faster_http AsyncClient with auth (should match httpx)
        faster_auth = faster_http.BasicAuth("user", "pass")
        faster_client_with_auth = faster_http.AsyncClient(auth=faster_auth)
        assert hasattr(faster_client_with_auth, "auth") or hasattr(faster_client_with_auth, "_auth")

    def test_helper_objects_creation_comparison(self):
        """Test helper objects creation - httpx vs faster_http."""
        # First test httpx Timeout object - need to provide all parameters
        httpx_timeout = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
        assert httpx_timeout.connect == 5.0
        assert httpx_timeout.read == 30.0

        # Then test faster_http Timeout object (should match httpx)
        faster_timeout = faster_http.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
        assert faster_timeout.connect == 5.0
        assert faster_timeout.read == 30.0

        # Both should have the same values
        assert httpx_timeout.connect == faster_timeout.connect
        assert httpx_timeout.read == faster_timeout.read

        # First test httpx Headers object
        httpx_headers = httpx.Headers({"User-Agent": "test-client", "Accept": "application/json"})
        assert httpx_headers["user-agent"] == "test-client"
        assert httpx_headers["USER-AGENT"] == "test-client"

        # Then test faster_http Headers object (should match httpx)
        faster_headers = faster_http.Headers({"User-Agent": "test-client", "Accept": "application/json"})
        assert faster_headers["user-agent"] == "test-client"
        assert faster_headers["USER-AGENT"] == "test-client"

        # Both should handle case-insensitive access identically
        assert httpx_headers["user-agent"] == faster_headers["user-agent"]
        assert httpx_headers["USER-AGENT"] == faster_headers["USER-AGENT"]

        # First test httpx Cookies object
        httpx_cookies = httpx.Cookies()
        httpx_cookies["session"] = "abc123"
        assert httpx_cookies["session"] == "abc123"

        # Then test faster_http Cookies object (should match httpx)
        faster_cookies = faster_http.Cookies()
        faster_cookies["session"] = "abc123"
        assert faster_cookies["session"] == "abc123"

        # Both should handle cookies identically
        assert httpx_cookies["session"] == faster_cookies["session"]

        # First test httpx QueryParams object
        httpx_params = httpx.QueryParams({"search": "python", "limit": "10"})
        httpx_params_dict = dict(httpx_params)
        assert httpx_params_dict["search"] == "python"
        assert httpx_params_dict["limit"] == "10"

        # Then test faster_http QueryParams object (should match httpx)
        faster_params = faster_http.QueryParams({"search": "python", "limit": "10"})
        faster_params_dict = dict(faster_params)
        assert faster_params_dict["search"] == "python"
        assert faster_params_dict["limit"] == "10"

        # Both should produce identical dictionaries
        assert httpx_params_dict == faster_params_dict

    def test_client_methods_exist_comparison(self):
        """Test that HTTP methods exist on clients - httpx vs faster_http."""
        methods = ["get", "post", "put", "patch", "delete", "head", "options", "request"]

        # First test httpx clients
        httpx_client = httpx.Client()
        httpx_async_client = httpx.AsyncClient()

        for method in methods:
            assert hasattr(httpx_client, method), f"httpx Client missing {method} method"
            assert callable(getattr(httpx_client, method)), f"httpx Client {method} not callable"

            assert hasattr(httpx_async_client, method), f"httpx AsyncClient missing {method} method"
            assert callable(getattr(httpx_async_client, method)), f"httpx AsyncClient {method} not callable"

        # Then test faster_http clients (should match httpx exactly)
        faster_client = faster_http.Client()
        faster_async_client = faster_http.AsyncClient()

        for method in methods:
            assert hasattr(faster_client, method), f"faster_http Client missing {method} method that httpx has"
            assert callable(getattr(faster_client, method)), f"faster_http Client {method} not callable"

            assert hasattr(faster_async_client, method), (
                f"faster_http AsyncClient missing {method} method that httpx has"
            )
            assert callable(getattr(faster_async_client, method)), f"faster_http AsyncClient {method} not callable"

    def test_module_level_functions_exist_comparison(self):
        """Test module-level functions exist - httpx vs faster_http."""
        functions = ["get", "post", "put", "patch", "delete", "head", "options", "request"]

        # First test httpx module functions
        for func_name in functions:
            assert hasattr(httpx, func_name), f"httpx missing {func_name} function"
            assert callable(getattr(httpx, func_name)), f"httpx {func_name} not callable"

        # Then test faster_http module functions (should match httpx exactly)
        for func_name in functions:
            assert hasattr(faster_http, func_name), f"faster_http missing {func_name} function that httpx has"
            assert callable(getattr(faster_http, func_name)), f"faster_http {func_name} not callable"

    def test_context_manager_support_comparison(self):
        """Test context manager support - httpx vs faster_http."""
        # First test httpx context manager support
        httpx_client = httpx.Client()
        assert hasattr(httpx_client, "__enter__")
        assert hasattr(httpx_client, "__exit__")
        assert callable(httpx_client.__enter__)
        assert callable(httpx_client.__exit__)

        # Test that httpx context manager works
        with httpx.Client() as httpx_ctx_client:
            assert httpx_ctx_client is not None
            assert hasattr(httpx_ctx_client, "get")

        # Then test faster_http context manager support (should match httpx)
        faster_client = faster_http.Client()
        assert hasattr(faster_client, "__enter__")
        assert hasattr(faster_client, "__exit__")
        assert callable(faster_client.__enter__)
        assert callable(faster_client.__exit__)

        # Test that faster_http context manager works
        with faster_http.Client() as faster_ctx_client:
            assert faster_ctx_client is not None
            assert hasattr(faster_ctx_client, "get")

        # Test async context managers - httpx first
        httpx_async_client = httpx.AsyncClient()
        assert hasattr(httpx_async_client, "__aenter__")
        assert hasattr(httpx_async_client, "__aexit__")
        assert callable(httpx_async_client.__aenter__)
        assert callable(httpx_async_client.__aexit__)

        # Then test faster_http async context managers (should match httpx)
        faster_async_client = faster_http.AsyncClient()
        assert hasattr(faster_async_client, "__aenter__")
        assert hasattr(faster_async_client, "__aexit__")
        assert callable(faster_async_client.__aenter__)
        assert callable(faster_async_client.__aexit__)

    def test_auth_tuple_compatibility_comparison(self):
        """Test auth tuple compatibility - httpx vs faster_http."""
        auth_tuple = ("username", "password")

        # First test httpx auth tuple support
        try:
            httpx_client = httpx.Client(auth=auth_tuple)
            assert httpx_client is not None
            httpx_supports_tuple = True
        except TypeError:
            # httpx might require BasicAuth object
            httpx_auth = httpx.BasicAuth(*auth_tuple)
            httpx_client = httpx.Client(auth=httpx_auth)
            assert httpx_client is not None
            httpx_supports_tuple = False

        # Then test faster_http auth tuple support (should match httpx behavior)
        try:
            faster_client = faster_http.Client(auth=auth_tuple)
            assert faster_client is not None
            faster_supports_tuple = True
        except TypeError:
            # Should match httpx behavior
            faster_auth = faster_http.BasicAuth(*auth_tuple)
            faster_client = faster_http.Client(auth=faster_auth)
            assert faster_client is not None
            faster_supports_tuple = False

        # Both should handle auth tuples consistently
        assert httpx_supports_tuple == faster_supports_tuple

    def test_error_classes_exist_comparison(self):
        """Test error classes exist - httpx vs faster_http."""
        expected_errors = [
            "HTTPError",
            "HTTPStatusError",
            "RequestError",
            "ConnectError",
            "TimeoutException",
            "ReadTimeout",
            "WriteTimeout",
            "ConnectTimeout",
            "PoolTimeout",
            "ProtocolError",
            "TooManyRedirects",
            "TransportError",
            "StreamError",
            "InvalidURL",
            "LocalProtocolError",
            "RemoteProtocolError",
            "ReadError",
            "WriteError",
            "UnsupportedProtocol",
        ]

        # First check which error classes httpx has
        for error_name in expected_errors:
            if hasattr(httpx, error_name):
                httpx_error_class = getattr(httpx, error_name)
                assert isinstance(httpx_error_class, type), f"httpx {error_name} should be a class"

                # Then check that faster_http has the same error class
                assert hasattr(faster_http, error_name), f"faster_http missing {error_name} that httpx has"
                faster_error_class = getattr(faster_http, error_name)
                assert isinstance(faster_error_class, type), f"faster_http {error_name} should be a class"
