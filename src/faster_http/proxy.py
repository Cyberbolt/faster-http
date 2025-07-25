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
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Proxy):
            return False
        return (
            str(self._url) == str(other._url) and
            self._auth == other._auth and
            self._ssl_context == other._ssl_context and
            list(self._headers.items()) == list(other._headers.items())
        )
    
    def __hash__(self) -> int:
        return hash((
            str(self._url),
            self._auth,
            id(self._ssl_context) if self._ssl_context else None,
            tuple(sorted(self._headers.items()))
        ))
    
    def copy_with(
        self,
        *,
        url: Optional[Union[str, "URL"]] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        auth: Optional[Tuple[str, str]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> "Proxy":
        """
        Create a copy of this proxy with modified parameters.
        
        Args:
            url: New proxy URL (optional)
            ssl_context: New SSL context (optional)
            auth: New authentication credentials (optional)
            headers: New headers (optional)
            
        Returns:
            A new Proxy instance with the specified modifications
        """
        return Proxy(
            url=url if url is not None else self._url,
            ssl_context=ssl_context if ssl_context is not None else self._ssl_context,
            auth=auth if auth is not None else self._auth,
            headers=headers if headers is not None else dict(self._headers.items())
        )
    
    def get_proxy_url_for_scheme(self, scheme: str) -> str:
        """
        Get the appropriate proxy URL for a given scheme.
        
        Args:
            scheme: The URL scheme (http, https, etc.)
            
        Returns:
            The proxy URL as a string
        """
        return str(self._url)
    
    def supports_scheme(self, scheme: str) -> bool:
        """
        Check if this proxy supports the given scheme.
        
        Args:
            scheme: The URL scheme to check
            
        Returns:
            True if the proxy supports the scheme, False otherwise
        """
        # Extract scheme from URL string since URL object may not have scheme attribute
        url_str = str(self._url)
        if "://" in url_str:
            proxy_scheme = url_str.split("://")[0].lower()
        else:
            proxy_scheme = "http"  # default
            
        scheme = scheme.lower()
        
        # HTTP proxies can handle both HTTP and HTTPS traffic
        if proxy_scheme == "http":
            return scheme in ("http", "https")
        
        # HTTPS proxies can handle both HTTP and HTTPS traffic  
        elif proxy_scheme == "https":
            return scheme in ("http", "https")
        
        # SOCKS proxies can handle various protocols
        elif proxy_scheme.startswith("socks"):
            return scheme in ("http", "https", "ftp")
        
        # For other proxy types, require exact scheme match
        else:
            return proxy_scheme == scheme
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert the proxy configuration to a dictionary format.
        
        Returns:
            Dictionary with proxy configuration
        """
        result = {"url": str(self._url)}
        
        if self._auth:
            result["auth"] = f"{self._auth[0]}:{self._auth[1]}"
        
        if self._headers:
            result["headers"] = dict(self._headers.items())
        
        if self._ssl_context:
            result["ssl_context"] = str(self._ssl_context)
        
        return result