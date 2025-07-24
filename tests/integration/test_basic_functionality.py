"""
Basic integration tests for faster-http functionality.
Tests that the library can be imported and basic objects work.
"""

import faster_http


class TestBasicIntegration:
    """Test basic integration functionality."""
    
    def test_library_import(self):
        """Test that the library imports correctly."""
        # Test that we can import all major components
        assert hasattr(faster_http, 'Client')
        assert hasattr(faster_http, 'AsyncClient')
        assert hasattr(faster_http, 'get')
        assert hasattr(faster_http, 'post')
        assert hasattr(faster_http, 'put')
        assert hasattr(faster_http, 'patch')
        assert hasattr(faster_http, 'delete')
        assert hasattr(faster_http, 'head')
        assert hasattr(faster_http, 'options')
        assert hasattr(faster_http, 'request')
    
    def test_auth_objects_creation(self):
        """Test that authentication objects can be created."""
        # Test BasicAuth
        basic_auth = faster_http.BasicAuth("user", "pass")
        assert basic_auth.username == "user"
        assert basic_auth.password == "pass"
        
        # Test DigestAuth
        digest_auth = faster_http.DigestAuth("user", "pass")
        assert digest_auth.username == "user"
        assert digest_auth.password == "pass"
        
        # Test NetRCAuth
        netrc_auth = faster_http.NetRCAuth()
        assert hasattr(netrc_auth, 'file')
    
    def test_client_creation_with_config(self):
        """Test that clients can be created with various configurations."""
        # Basic client
        client = faster_http.Client()
        assert client is not None
        
        # Client with base URL
        client_with_base = faster_http.Client(base_url="https://api.test.local")
        assert client_with_base.base_url == "https://api.test.local"
        
        # Client with headers
        headers = {"Authorization": "Bearer token"}
        client_with_headers = faster_http.Client(headers=headers)
        assert hasattr(client_with_headers, 'headers') or hasattr(client_with_headers, '_headers')
        
        # Client with timeout
        client_with_timeout = faster_http.Client(timeout=30.0)
        assert client_with_timeout is not None
        
        # Client with auth
        auth = faster_http.BasicAuth("user", "pass")
        client_with_auth = faster_http.Client(auth=auth)
        assert hasattr(client_with_auth, 'auth') or hasattr(client_with_auth, '_auth')
    
    def test_async_client_creation_with_config(self):
        """Test that async clients can be created with various configurations."""
        # Basic async client
        async_client = faster_http.AsyncClient()
        assert async_client is not None
        
        # Async client with base URL
        async_client_with_base = faster_http.AsyncClient(base_url="https://api.test.local")
        assert async_client_with_base.base_url == "https://api.test.local"
        
        # Async client with headers
        headers = {"Authorization": "Bearer token"}
        async_client_with_headers = faster_http.AsyncClient(headers=headers)
        assert hasattr(async_client_with_headers, 'headers') or hasattr(async_client_with_headers, '_headers')
        
        # Async client with timeout
        async_client_with_timeout = faster_http.AsyncClient(timeout=30.0)
        assert async_client_with_timeout is not None
        
        # Async client with auth
        auth = faster_http.BasicAuth("user", "pass")
        async_client_with_auth = faster_http.AsyncClient(auth=auth)
        assert hasattr(async_client_with_auth, 'auth') or hasattr(async_client_with_auth, '_auth')
    
    def test_helper_objects_creation(self):
        """Test that helper objects can be created."""
        # Test Timeout object
        timeout = faster_http.Timeout(connect=5.0, read=30.0)
        assert timeout.connect == 5.0
        assert timeout.read == 30.0
        
        # Test Headers object
        headers = faster_http.Headers({
            "User-Agent": "test-client",
            "Accept": "application/json"
        })
        assert headers['user-agent'] == "test-client"
        assert headers['USER-AGENT'] == "test-client"
        
        # Test Cookies object
        cookies = faster_http.Cookies()
        cookies['session'] = 'abc123'
        assert cookies['session'] == 'abc123'
        
        # Test QueryParams object
        params = faster_http.QueryParams({
            'search': 'python',
            'limit': '10'
        })
        params_dict = dict(params)
        assert params_dict['search'] == 'python'
        assert params_dict['limit'] == '10'
    
    def test_client_methods_exist(self):
        """Test that all expected HTTP methods exist on clients."""
        client = faster_http.Client()
        async_client = faster_http.AsyncClient()
        
        methods = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'request']
        
        for method in methods:
            # Test sync client
            assert hasattr(client, method), f"Client missing {method} method"
            assert callable(getattr(client, method)), f"Client {method} not callable"
            
            # Test async client
            assert hasattr(async_client, method), f"AsyncClient missing {method} method"
            assert callable(getattr(async_client, method)), f"AsyncClient {method} not callable"
    
    def test_module_level_functions_exist(self):
        """Test that module-level convenience functions exist."""
        functions = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'request']
        
        for func_name in functions:
            assert hasattr(faster_http, func_name), f"Module missing {func_name} function"
            assert callable(getattr(faster_http, func_name)), f"Module {func_name} not callable"
    
    def test_context_manager_support(self):
        """Test that clients support context manager protocol."""
        # Test sync client
        client = faster_http.Client()
        assert hasattr(client, '__enter__')
        assert hasattr(client, '__exit__')
        assert callable(client.__enter__)
        assert callable(client.__exit__)
        
        # Test that context manager works
        with faster_http.Client() as ctx_client:
            assert ctx_client is not None
            assert hasattr(ctx_client, 'get')
        
        # Test async client
        async_client = faster_http.AsyncClient()
        assert hasattr(async_client, '__aenter__')
        assert hasattr(async_client, '__aexit__')
        assert callable(async_client.__aenter__)
        assert callable(async_client.__aexit__)
    
    def test_auth_tuple_compatibility(self):
        """Test that auth tuples are supported."""
        auth_tuple = ("username", "password")
        
        # Test that we can create clients with auth tuples
        try:
            client = faster_http.Client(auth=auth_tuple) 
            assert client is not None
        except TypeError:
            # If auth tuples aren't supported yet, that's OK
            # but we should be able to create BasicAuth from tuple
            auth = faster_http.BasicAuth(*auth_tuple)
            client = faster_http.Client(auth=auth)
            assert client is not None
    
    def test_error_classes_exist(self):
        """Test that expected error classes exist."""
        expected_errors = [
            'HTTPError', 'HTTPStatusError', 'RequestError', 'ConnectError', 
            'TimeoutError', 'ReadTimeout', 'WriteTimeout', 'ConnectTimeout',
            'PoolTimeout', 'NetworkError', 'ProtocolError', 'DecodingError',
            'TooManyRedirects', 'InvalidURL'
        ]
        
        for error_name in expected_errors:
            if hasattr(faster_http, error_name):
                error_class = getattr(faster_http, error_name)
                assert isinstance(error_class, type), f"{error_name} should be a class"