"""Authentication classes for faster-http."""
import base64
import os
from typing import Generator, Optional


class Auth:
    """Base class for authentication schemes."""
    
    def auth_flow(self, request) -> Generator:
        """Generator that yields the request with authentication applied."""
        yield request


class BasicAuth(Auth):
    """HTTP Basic Authentication."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    def auth_flow(self, request) -> Generator:
        """Apply basic authentication to the request."""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        if hasattr(request, 'headers'):
            request.headers["Authorization"] = f"Basic {encoded_credentials}"
        yield request
    
    def __repr__(self):
        return f"<BasicAuth [username={self.username!r}]>"


class DigestAuth(Auth):
    """HTTP Digest Authentication (simplified implementation)."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    def __repr__(self):
        return f"<DigestAuth [username={self.username!r}]>"


class NetRCAuth(Auth):
    """Authentication using .netrc file."""
    
    def __init__(self, file: Optional[str] = None):
        self.file = file or os.path.expanduser("~/.netrc")
    
    def __repr__(self):
        return f"<NetRCAuth [file={self.file!r}]>" 