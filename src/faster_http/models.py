"""Data models for faster-http."""
from typing import Dict, Mapping, Optional, Union
from urllib.parse import parse_qsl


class URL:
    """URL parsing and manipulation."""
    
    def __init__(self, url: str):
        self._url = url
    
    def __str__(self) -> str:
        return self._url
    
    @property
    def scheme(self) -> str:
        """URL scheme (http/https)."""
        if "://" in self._url:
            return self._url.split("://")[0]
        return ""
    
    @property
    def host(self) -> str:
        """URL host."""
        if "://" in self._url:
            parts = self._url.split("://")[1]
            return parts.split("/")[0].split(":")[0]
        return ""


class Headers(dict):
    """Case-insensitive headers."""
    
    def __init__(self, headers: Optional[Mapping[str, str]] = None):
        super().__init__()
        if headers:
            for key, value in headers.items():
                self[key] = value
    
    def __getitem__(self, key: str) -> str:
        for k, v in self.items():
            if k.lower() == key.lower():
                return v
        raise KeyError(key)
    
    def __setitem__(self, key: str, value: str):
        # Remove existing key (case-insensitive)
        to_remove = [k for k in self.keys() if k.lower() == key.lower()]
        for k in to_remove:
            del self[k]
        super().__setitem__(key, value)


class Cookies(dict):
    """HTTP cookies container."""
    
    def set(self, name: str, value: str, domain: Optional[str] = None):
        """Set a cookie."""
        self[name] = value


class QueryParams(dict):
    """URL query parameters."""
    
    def __init__(self, params: Optional[Union[Dict[str, str], str]] = None):
        super().__init__()
        if isinstance(params, dict):
            self.update(params)
        elif isinstance(params, str):
            self._parse_query_string(params)
    
    def _parse_query_string(self, query_string: str):
        """Parse query string into parameters."""
        if query_string.startswith('?'):
            query_string = query_string[1:]
        
        for key, value in parse_qsl(query_string, keep_blank_values=True):
            self[key] = value


class Timeout:
    """Timeout configuration."""
    
    def __init__(self, 
                 connect: Optional[float] = None,
                 read: Optional[float] = None,
                 write: Optional[float] = None,
                 pool: Optional[float] = None):
        self.connect = connect
        self.read = read
        self.write = write
        self.pool = pool


class Limits:
    """Connection pool limits."""
    
    def __init__(self, 
                 max_keepalive_connections: int = 20,
                 max_connections: int = 100,
                 keepalive_expiry: float = 5.0):
        self.max_keepalive_connections = max_keepalive_connections
        self.max_connections = max_connections
        self.keepalive_expiry = keepalive_expiry 