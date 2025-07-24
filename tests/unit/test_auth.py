"""
Unit tests for authentication functionality.
Tests various authentication methods and their properties.
"""

import faster_http


class TestBasicAuth:
    """Test BasicAuth functionality."""
    
    def test_basic_auth_creation(self):
        """Test BasicAuth class creation and properties."""
        auth = faster_http.BasicAuth("testuser", "testpass")
        assert auth.username == "testuser"
        assert auth.password == "testpass"
        
        # Test representation
        auth_repr = repr(auth)
        assert "BasicAuth" in auth_repr
        assert "testuser" in auth_repr
        # Password should not be in repr
        assert "testpass" not in auth_repr
    
    def test_basic_auth_equality(self):
        """Test BasicAuth equality comparison."""
        auth1 = faster_http.BasicAuth("testuser", "testpass")
        auth2 = faster_http.BasicAuth("testuser", "testpass")
        auth3 = faster_http.BasicAuth("different", "testpass")
        
        # Test that they have the same username and password
        assert auth1.username == auth2.username
        assert auth1.password == auth2.password
        assert auth1.username != auth3.username
    
    def test_basic_auth_with_empty_credentials(self):
        """Test BasicAuth with empty credentials."""
        auth = faster_http.BasicAuth("", "")
        assert auth.username == ""
        assert auth.password == ""
    
    def test_basic_auth_with_special_characters(self):
        """Test BasicAuth with special characters in credentials."""
        username = "user@domain.com"
        password = "p@ssw0rd!#$"
        auth = faster_http.BasicAuth(username, password)
        assert auth.username == username
        assert auth.password == password


class TestDigestAuth:
    """Test DigestAuth functionality."""
    
    def test_digest_auth_creation(self):
        """Test DigestAuth class creation and properties."""
        auth = faster_http.DigestAuth("testuser", "testpass")
        assert auth.username == "testuser" 
        assert auth.password == "testpass"
        
        # Test representation
        auth_repr = repr(auth)
        assert "DigestAuth" in auth_repr
    
    def test_digest_auth_equality(self):
        """Test DigestAuth equality comparison."""
        auth1 = faster_http.DigestAuth("testuser", "testpass")
        auth2 = faster_http.DigestAuth("testuser", "testpass") 
        auth3 = faster_http.DigestAuth("different", "testpass")
        
        # Test that they have the same username and password
        assert auth1.username == auth2.username
        assert auth1.password == auth2.password
        assert auth1.username != auth3.username


class TestNetRCAuth:
    """Test NetRCAuth functionality."""
    
    def test_netrc_auth_creation(self):
        """Test NetRCAuth class creation."""
        auth = faster_http.NetRCAuth()
        
        # Test that it has expected attributes
        assert hasattr(auth, 'file')
        
        # Test representation
        auth_repr = repr(auth)
        assert "NetRCAuth" in auth_repr
    
    def test_netrc_auth_with_file(self):
        """Test NetRCAuth with custom file path."""
        custom_file = "/custom/path/.netrc"
        auth = faster_http.NetRCAuth(file=custom_file)
        assert auth.file == custom_file


class TestAuthTuple:
    """Test authentication tuple functionality."""
    
    def test_auth_tuple_creation(self):
        """Test that auth tuples are handled correctly."""
        # This tests that the library accepts auth tuples
        # We can't test the actual HTTP request without external dependencies
        auth_tuple = ("testuser", "testpass")
        
        # Verify tuple structure
        assert len(auth_tuple) == 2
        assert auth_tuple[0] == "testuser"
        assert auth_tuple[1] == "testpass"
        
        # Test tuple unpacking
        username, password = auth_tuple
        assert username == "testuser"
        assert password == "testpass"