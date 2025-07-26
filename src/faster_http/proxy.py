"""
Proxy configuration class for faster-http
Compatible with httpx.Proxy interface  
"""

import ssl
from typing import Dict, Optional, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from . import URL, Headers


class Proxy:
    """HTTP proxy configuration class matching httpx.Proxy interface"""
    
    def __init__(
        self,
        url: Union[str, "URL"],
        *,
        ssl_context: Optional[ssl.SSLContext] = None,
        auth: Optional[Tuple[str, str]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize a Proxy configuration.
        
        Args:
            url: The URL of the proxy server
            ssl_context: SSL context for HTTPS proxies
            auth: Authentication credentials (username, password) for the proxy
            headers: Headers to send with proxy requests
        """
        # Import URL here to avoid circular imports
        from . import URL
        
        if isinstance(url, str):
            self._url = URL(url)
        else:
            self._url = url
            
        self._ssl_context = ssl_context
        self._auth = auth
        
        # Import Headers here to avoid circular imports
        from . import Headers
        
        if headers is None:
            self._headers = Headers()
        elif isinstance(headers, dict):
            self._headers = Headers(headers)
        else:
            self._headers = headers
    
    @property
    def url(self) -> "URL":
        """The URL of the proxy server"""
        return self._url
    
    @property
    def auth(self) -> Optional[Tuple[str, str]]:
        """Authentication credentials for the proxy"""
        return self._auth
    
    @property
    def raw_auth(self) -> Optional[Tuple[bytes, bytes]]:
        """Authentication credentials for the proxy as bytes"""
        if self._auth is None:
            return None
        return (self._auth[0].encode('utf-8'), self._auth[1].encode('utf-8'))
    
    @property
    def headers(self) -> "Headers":
        """Headers to send with proxy requests"""
        return self._headers
    
    @property
    def ssl_context(self) -> Optional[ssl.SSLContext]:
        """SSL context for HTTPS proxies"""
        return self._ssl_context
    
    def __repr__(self) -> str:
        auth_info = "with auth" if self._auth else "no auth"
        return f"<Proxy {self._url} ({auth_info})>"
    
    def __str__(self) -> str:
        return str(self._url)
    
    
