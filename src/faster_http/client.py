"""HTTP clients for faster-http."""
from typing import Dict, Optional, Union, List, Callable

from ._core import AsyncHttpClient as _AsyncHttpClient, HttpRequest as _HttpRequest
from .auth import Auth
from .models import Headers, Cookies, QueryParams, Timeout, Limits
from .responses import Response
from .utils import (
    _process_auth, _process_headers, _process_cookies, 
    _process_params, _process_timeout, _prepare_files
)


class AsyncClient:
    """Asynchronous HTTP client compatible with httpx.AsyncClient."""
    
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: Union[Timeout, float, None] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        verify: Optional[bool] = None,
        follow_redirects: Optional[bool] = None,
        auth: Union[Auth, tuple[str, str], None] = None,
        proxy: Optional[str] = None,
        cookies: Union[Cookies, Dict[str, str], None] = None,
        http2: Optional[bool] = None,
        limits: Optional[Limits] = None,
        event_hooks: Optional[Dict[str, List[Callable]]] = None,
    ):
        self._client = _AsyncHttpClient(
            base_url=base_url,
            timeout=_process_timeout(timeout),
            headers=_process_headers(headers),
            verify=verify,
            follow_redirects=follow_redirects,
            auth=_process_auth(auth),
            proxy=proxy,
            cookies=_process_cookies(cookies),
            http2=http2,
        )
    
    def build_request(
        self,
        method: str,
        url: str,
        *,
        params: Union[QueryParams, Dict[str, str], None] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        content: Optional[bytes] = None,
    ) -> _HttpRequest:
        """Build a request object."""
        return self._client.build_request(
            method, url, 
            params=_process_params(params), 
            headers=_process_headers(headers), 
            content=content
        )
    
    async def send(self, request: _HttpRequest) -> Response:
        """Send a pre-built request."""
        return await self._client.send(request)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def get(self, url: str, **kwargs) -> Response:
        """Send a GET request."""
        return await self._client.get(
            url,
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )
    
    async def post(self, url: str, **kwargs) -> Response:
        """Send a POST request."""
        return await self._client.post(
            url,
            content=kwargs.get('content'),
            data=kwargs.get('data'),
            json=kwargs.get('json'),
            files=_prepare_files(kwargs.get('files')),
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )
    
    async def put(self, url: str, **kwargs) -> Response:
        """Send a PUT request."""
        return await self._client.put(
            url,
            content=kwargs.get('content'),
            data=kwargs.get('data'),
            json=kwargs.get('json'),
            files=_prepare_files(kwargs.get('files')),
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )
    
    async def patch(self, url: str, **kwargs) -> Response:
        """Send a PATCH request."""
        return await self._client.patch(
            url,
            content=kwargs.get('content'),
            data=kwargs.get('data'),
            json=kwargs.get('json'),
            files=_prepare_files(kwargs.get('files')),
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )
    
    async def delete(self, url: str, **kwargs) -> Response:
        """Send a DELETE request."""
        return await self._client.delete(
            url,
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )
    
    async def head(self, url: str, **kwargs) -> Response:
        """Send a HEAD request."""
        return await self._client.head(
            url,
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        )
    
    async def options(self, url: str, **kwargs) -> Response:
        """Send an OPTIONS request."""
        return await self._client.options(
            url,
            params=_process_params(kwargs.get('params')),
            headers=_process_headers(kwargs.get('headers')),
            timeout=_process_timeout(kwargs.get('timeout')),
            auth=_process_auth(kwargs.get('auth')),
            follow_redirects=kwargs.get('follow_redirects'),
            cookies=_process_cookies(kwargs.get('cookies')),
        ) 