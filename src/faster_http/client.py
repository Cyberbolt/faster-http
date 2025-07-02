"""HTTP clients for faster-http."""
from typing import Dict, Optional, Union, List, Callable, Tuple, Any
from types import TracebackType

from ._core import AsyncHttpClient as _AsyncHttpClient, HttpRequest as _HttpRequest, HttpResponse
from .auth import Auth
from .models import Headers, Cookies, QueryParams, Timeout, Limits
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
        timeout: Optional[Union[Timeout, float]] = None,
        headers: Optional[Union[Headers, Dict[str, str]]] = None,
        verify: Optional[bool] = None,
        follow_redirects: Optional[bool] = None,
        auth: Optional[Union[Auth, Tuple[str, str]]] = None,
        proxy: Optional[str] = None,
        cookies: Optional[Union[Cookies, Dict[str, str]]] = None,
        http2: Optional[bool] = None,
        limits: Optional[Limits] = None,
        event_hooks: Optional[Dict[str, List[Callable]]] = None,
    ) -> None:
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
        params: Optional[Union[QueryParams, Dict[str, str]]] = None,
        headers: Optional[Union[Headers, Dict[str, str]]] = None,
        content: Optional[bytes] = None,
    ) -> _HttpRequest:
        """Build a request object."""
        return self._client.build_request(
            method, url, 
            params=_process_params(params), 
            headers=_process_headers(headers), 
            content=content
        )
    
    async def send(self, request: _HttpRequest) -> HttpResponse:
        """Send a pre-built request."""
        return await self._client.send(request)
    
    async def __aenter__(self) -> "AsyncClient":
        return self
    
    async def __aexit__(
        self, 
        exc_type: Optional[type], 
        exc_val: Optional[BaseException], 
        exc_tb: Optional[TracebackType]
    ) -> None:
        pass
    
    async def get(
        self, 
        url: str,
        *,
        params: Optional[Union[QueryParams, Dict[str, str]]] = None,
        headers: Optional[Union[Headers, Dict[str, str]]] = None,
        timeout: Optional[Union[Timeout, float]] = None,
        auth: Optional[Union[Auth, Tuple[str, str]]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Union[Cookies, Dict[str, str]]] = None,
    ) -> HttpResponse:
        """Send a GET request."""
        return await self._client.get(
            url,
            params=_process_params(params),
            headers=_process_headers(headers),
            timeout=_process_timeout(timeout),
            auth=_process_auth(auth),
            follow_redirects=follow_redirects,
            cookies=_process_cookies(cookies),
        )
    
    async def post(
        self, 
        url: str,
        *,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Union[QueryParams, Dict[str, str]]] = None,
        headers: Optional[Union[Headers, Dict[str, str]]] = None,
        timeout: Optional[Union[Timeout, float]] = None,
        auth: Optional[Union[Auth, Tuple[str, str]]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Union[Cookies, Dict[str, str]]] = None,
    ) -> HttpResponse:
        """Send a POST request."""
        return await self._client.post(
            url,
            content=content,
            data=data,
            json=json,
            files=_prepare_files(files),
            params=_process_params(params),
            headers=_process_headers(headers),
            timeout=_process_timeout(timeout),
            auth=_process_auth(auth),
            follow_redirects=follow_redirects,
            cookies=_process_cookies(cookies),
        )
    
    async def put(
        self, 
        url: str,
        *,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Union[QueryParams, Dict[str, str]]] = None,
        headers: Optional[Union[Headers, Dict[str, str]]] = None,
        timeout: Optional[Union[Timeout, float]] = None,
        auth: Optional[Union[Auth, Tuple[str, str]]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Union[Cookies, Dict[str, str]]] = None,
    ) -> HttpResponse:
        """Send a PUT request."""
        return await self._client.put(
            url,
            content=content,
            data=data,
            json=json,
            files=_prepare_files(files),
            params=_process_params(params),
            headers=_process_headers(headers),
            timeout=_process_timeout(timeout),
            auth=_process_auth(auth),
            follow_redirects=follow_redirects,
            cookies=_process_cookies(cookies),
        )
    
    async def patch(
        self, 
        url: str,
        *,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Union[QueryParams, Dict[str, str]]] = None,
        headers: Optional[Union[Headers, Dict[str, str]]] = None,
        timeout: Optional[Union[Timeout, float]] = None,
        auth: Optional[Union[Auth, Tuple[str, str]]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Union[Cookies, Dict[str, str]]] = None,
    ) -> HttpResponse:
        """Send a PATCH request."""
        return await self._client.patch(
            url,
            content=content,
            data=data,
            json=json,
            files=_prepare_files(files),
            params=_process_params(params),
            headers=_process_headers(headers),
            timeout=_process_timeout(timeout),
            auth=_process_auth(auth),
            follow_redirects=follow_redirects,
            cookies=_process_cookies(cookies),
        )
    
    async def delete(
        self, 
        url: str,
        *,
        params: Optional[Union[QueryParams, Dict[str, str]]] = None,
        headers: Optional[Union[Headers, Dict[str, str]]] = None,
        timeout: Optional[Union[Timeout, float]] = None,
        auth: Optional[Union[Auth, Tuple[str, str]]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Union[Cookies, Dict[str, str]]] = None,
    ) -> HttpResponse:
        """Send a DELETE request."""
        return await self._client.delete(
            url,
            params=_process_params(params),
            headers=_process_headers(headers),
            timeout=_process_timeout(timeout),
            auth=_process_auth(auth),
            follow_redirects=follow_redirects,
            cookies=_process_cookies(cookies),
        )
    
    async def head(
        self, 
        url: str,
        *,
        params: Optional[Union[QueryParams, Dict[str, str]]] = None,
        headers: Optional[Union[Headers, Dict[str, str]]] = None,
        timeout: Optional[Union[Timeout, float]] = None,
        auth: Optional[Union[Auth, Tuple[str, str]]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Union[Cookies, Dict[str, str]]] = None,
    ) -> HttpResponse:
        """Send a HEAD request."""
        return await self._client.head(
            url,
            params=_process_params(params),
            headers=_process_headers(headers),
            timeout=_process_timeout(timeout),
            auth=_process_auth(auth),
            follow_redirects=follow_redirects,
            cookies=_process_cookies(cookies),
        )
    
    async def options(
        self, 
        url: str,
        *,
        params: Optional[Union[QueryParams, Dict[str, str]]] = None,
        headers: Optional[Union[Headers, Dict[str, str]]] = None,
        timeout: Optional[Union[Timeout, float]] = None,
        auth: Optional[Union[Auth, Tuple[str, str]]] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Union[Cookies, Dict[str, str]]] = None,
    ) -> HttpResponse:
        """Send an OPTIONS request."""
        return await self._client.options(
            url,
            params=_process_params(params),
            headers=_process_headers(headers),
            timeout=_process_timeout(timeout),
            auth=_process_auth(auth),
            follow_redirects=follow_redirects,
            cookies=_process_cookies(cookies),
        ) 