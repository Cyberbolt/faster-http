"""
faster-http: A high-performance HTTP client for Python, powered by Rust's reqwest library.

This library provides a drop-in replacement for httpx with significantly better performance
by leveraging Rust's reqwest library through PyO3 bindings.
"""

from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Mapping, Protocol
import base64

from ._core import (
    HttpClient as _HttpClient,
    AsyncHttpClient as _AsyncHttpClient,
    HttpRequest as _HttpRequest,
    HTTPError,
    ConnectTimeout,
    ReadTimeout,
    RequestError,
    get as _get,
    post as _post,
    put as _put,
    patch as _patch,
    delete as _delete,
    head as _head,
    options as _options,
)

__version__ = "0.1.0"
__all__ = [
    "get", "post", "put", "patch", "delete", "head", "options", "stream",
    "Client", "AsyncClient", "Response", "Request",
    "HTTPError", "ConnectTimeout", "ReadTimeout", "RequestError",
    "BasicAuth", "DigestAuth", "NetRCAuth", "Auth",
    "URL", "Headers", "Cookies", "QueryParams",
    "Timeout", "Limits", 
]


# ==================== Authentication Classes ====================

class Auth:
    """Base class for authentication schemes."""
    
    def auth_flow(self, request):
        """Generator that yields the request with authentication applied."""
        yield request
    
    def sync_auth_flow(self, request):
        """Synchronous authentication flow."""
        return self.auth_flow(request)
    
    async def async_auth_flow(self, request):
        """Asynchronous authentication flow."""
        for req in self.auth_flow(request):
            yield req


class BasicAuth(Auth):
    """HTTP Basic Authentication."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    def auth_flow(self, request):
        """Apply basic authentication to the request."""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        request.headers["Authorization"] = f"Basic {encoded_credentials}"
        yield request


class DigestAuth(Auth):
    """HTTP Digest Authentication."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    def auth_flow(self, request):
        """Digest authentication flow (simplified implementation)."""
        # 注意：这是一个简化的实现，真正的 Digest 认证需要处理 challenge-response
        # 在实际实现中，需要处理 401 响应，解析 WWW-Authenticate 头，
        # 计算正确的响应摘要等
        yield request
    
    def __repr__(self):
        return f"<DigestAuth [username={self.username!r}]>"


class NetRCAuth(Auth):
    """Authentication using .netrc file."""
    
    def __init__(self, file: Optional[str] = None):
        import os
        self.file = file or os.path.expanduser("~/.netrc")
    
    def auth_flow(self, request):
        """NetRC authentication flow."""
        # 简化实现：实际应该读取 .netrc 文件并提取凭据
        try:
            import netrc
            import urllib.parse
            
            parsed_url = urllib.parse.urlparse(request.url)
            hostname = parsed_url.hostname
            
            if hostname:
                netrc_auth = netrc.netrc(self.file)
                auth_data = netrc_auth.authenticators(hostname)
                if auth_data:
                    username, _, password = auth_data
                    # 这里应该将认证信息添加到请求中
                    # 简化处理，直接返回原请求
                    pass
        except (FileNotFoundError, netrc.NetrcParseError):
            # 如果文件不存在或解析失败，继续无认证
            pass
        
        yield request
    
    def __repr__(self):
        return f"<NetRCAuth [file={self.file!r}]>"


# ==================== Helper Classes ====================

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
    
    def copy_with(self, **kwargs) -> 'URL':
        """Create a copy with modifications."""
        return URL(self._url)


class Headers(dict):
    """Case-insensitive headers."""
    
    def __init__(self, headers: Optional[Mapping[str, str]] = None):
        super().__init__()
        if headers:
            for key, value in headers.items():
                self[key] = value
    
    def __getitem__(self, key: str) -> str:
        # 大小写不敏感的查找
        for k, v in self.items():
            if k.lower() == key.lower():
                return v
        raise KeyError(key)
    
    def __setitem__(self, key: str, value: str):
        # 移除现有的同名键（大小写不敏感）
        to_remove = []
        for k in self.keys():
            if k.lower() == key.lower():
                to_remove.append(k)
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
            # 简化的查询字符串解析
            if params.startswith('?'):
                params = params[1:]
            for part in params.split('&'):
                if '=' in part:
                    key, value = part.split('=', 1)
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


# ==================== Response and Request Classes ====================

class StreamingResponse:
    """Streaming response context manager with enhanced functionality."""
    
    def __init__(self, response):
        self._response = response
        self._consumed = False
    
    def __enter__(self):
        return self._response
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def __aenter__(self):
        return self._response
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def iter_bytes(self, chunk_size: Optional[int] = None):
        """迭代响应的字节内容。"""
        if self._consumed:
            raise RuntimeError("Response stream has been consumed")
        return self._response.iter_bytes(chunk_size)
    
    def iter_text(self, chunk_size: Optional[int] = None):
        """迭代响应的文本内容。"""
        if self._consumed:
            raise RuntimeError("Response stream has been consumed")
        return self._response.iter_text(chunk_size)
    
    def iter_lines(self):
        """迭代响应的行内容。"""
        if self._consumed:
            raise RuntimeError("Response stream has been consumed")
        return self._response.iter_lines()
    
    def iter_sse_events(self):
        """迭代 Server-Sent Events (SSE) 事件。"""
        if self._consumed:
            raise RuntimeError("Response stream has been consumed")
        
        # 如果响应对象有 iter_sse_lines 方法，使用它
        if hasattr(self._response, 'iter_sse_lines'):
            return self._response.iter_sse_lines()
        
        # 否则手动解析 SSE 事件
        events = []
        for line in self._response.iter_lines():
            if line.startswith('data:'):
                events.append(line)
            elif line.startswith(('event:', 'id:', 'retry:')):
                events.append(line)
        return events
    
    @property
    def status_code(self):
        return self._response.status_code
    
    @property
    def headers(self):
        return self._response.headers
    
    @property
    def url(self):
        return self._response.url
    
    def close(self):
        """关闭流式响应。"""
        self._consumed = True


class Response(Protocol):
    """HTTP Response protocol compatible with httpx.Response."""
    
    @property
    def status_code(self) -> int: ...
    
    @property
    def headers(self) -> Dict[str, str]: ...
    
    @property
    def url(self) -> str: ...
    
    @property
    def ok(self) -> bool: ...
    
    @property
    def content(self) -> bytes: ...
    
    @property
    def text(self) -> str: ...
    
    @property
    def encoding(self) -> Optional[str]: ...
    
    @encoding.setter
    def encoding(self, value: Optional[str]) -> None: ...
    
    @property
    def charset_encoding(self) -> Optional[str]: ...
    
    @property
    def elapsed(self) -> float: ...
    
    @property
    def is_client_error(self) -> bool: ...
    
    @property
    def is_server_error(self) -> bool: ...
    
    @property
    def is_redirect(self) -> bool: ...
    
    @property
    def http_version(self) -> str: ...
    
    @property
    def cookies(self) -> Dict[str, str]: ...
    
    @property
    def history(self) -> List[Any]: ...
    
    @property
    def request(self) -> Optional[Any]: ...
    
    def iter_bytes(self, chunk_size: Optional[int] = None) -> List[bytes]: ...
    
    def iter_text(self, chunk_size: Optional[int] = None) -> List[str]: ...
    
    def iter_lines(self) -> List[str]: ...
    
    def iter_raw(self, chunk_size: Optional[int] = None) -> List[bytes]: ...
    
    def json(self) -> Any: ...
    
    def raise_for_status(self) -> None: ...


# 使用 Rust 的 HttpClient 和 HttpRequest
# 直接使用导入的类，避免类型检查器混淆
Client = _HttpClient
Request = _HttpRequest


# ==================== Utility Functions ====================

def _process_auth(auth: Union[Auth, Tuple[str, str], None]) -> Optional[Tuple[str, str]]:
    """处理认证参数，将 Auth 类转换为元组格式."""
    if auth is None:
        return None
    elif isinstance(auth, tuple):
        return auth
    elif isinstance(auth, BasicAuth):
        return (auth.username, auth.password)
    elif isinstance(auth, (DigestAuth, NetRCAuth)):
        # 对于更复杂的认证，暂时返回 None
        return None
    else:
        return None


def _process_headers(headers: Union[Headers, Dict[str, str], None]) -> Optional[Dict[str, str]]:
    """处理 headers 参数."""
    if isinstance(headers, Headers):
        return dict(headers)
    return headers


def _process_cookies(cookies: Union[Cookies, Dict[str, str], None]) -> Optional[Dict[str, str]]:
    """处理 cookies 参数."""
    if isinstance(cookies, Cookies):
        return dict(cookies)
    return cookies


def _process_params(params: Union[QueryParams, Dict[str, str], None]) -> Optional[Dict[str, str]]:
    """处理 params 参数."""
    if isinstance(params, QueryParams):
        return dict(params)
    return params


def _process_timeout(timeout: Union[Timeout, float, None]) -> Optional[float]:
    """处理 timeout 参数."""
    if isinstance(timeout, Timeout):
        return timeout.read  # 简化处理，取 read timeout
    return timeout


# ==================== Async Client ====================

class AsyncClient:
    """
    Asynchronous HTTP client compatible with httpx.AsyncClient.
    """
    
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: Union[Timeout, float, None] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        verify: Optional[bool] = None,
        follow_redirects: Optional[bool] = None,
        auth: Union[Auth, Tuple[str, str], None] = None,
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
        
        self._limits = limits
        self._event_hooks = event_hooks or {}
    
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
    
    async def send(self, request: _HttpRequest) -> "Response":
        """Send a pre-built request."""
        return await self._client.send(request)
    
    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Union[QueryParams, Dict[str, str], None] = None,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        timeout: Union[Timeout, float, None] = None,
        auth: Union[Auth, Tuple[str, str], None] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Union[Cookies, Dict[str, str], None] = None,
    ) -> StreamingResponse:
        """Send a streaming request."""
        # TODO: 实现流式请求
        request = self.build_request(
            method, url, params=params, headers=headers, content=content
        )
        response = await self.send(request)
        return StreamingResponse(response)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def get(
        self,
        url: str,
        *,
        params: Union[QueryParams, Dict[str, str], None] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        timeout: Union[Timeout, float, None] = None,
        auth: Union[Auth, Tuple[str, str], None] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Union[Cookies, Dict[str, str], None] = None,
    ) -> "Response":
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
        params: Union[QueryParams, Dict[str, str], None] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        timeout: Union[Timeout, float, None] = None,
        auth: Union[Auth, Tuple[str, str], None] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Union[Cookies, Dict[str, str], None] = None,
    ) -> "Response":
        """Send a POST request."""
        return await self._client.post(
            url,
            content=content,
            data=data,
            json=json,
            files=files,
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
        params: Union[QueryParams, Dict[str, str], None] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        timeout: Union[Timeout, float, None] = None,
        auth: Union[Auth, Tuple[str, str], None] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Union[Cookies, Dict[str, str], None] = None,
    ) -> "Response":
        """Send a PUT request."""
        return await self._client.put(
            url,
            content=content,
            data=data,
            json=json,
            files=files,
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
        params: Union[QueryParams, Dict[str, str], None] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        timeout: Union[Timeout, float, None] = None,
        auth: Union[Auth, Tuple[str, str], None] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Union[Cookies, Dict[str, str], None] = None,
    ) -> "Response":
        """Send a PATCH request."""
        return await self._client.patch(
            url,
            content=content,
            data=data,
            json=json,
            files=files,
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
        params: Union[QueryParams, Dict[str, str], None] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        timeout: Union[Timeout, float, None] = None,
        auth: Union[Auth, Tuple[str, str], None] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Union[Cookies, Dict[str, str], None] = None,
    ) -> "Response":
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
        params: Union[QueryParams, Dict[str, str], None] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        timeout: Union[Timeout, float, None] = None,
        auth: Union[Auth, Tuple[str, str], None] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Union[Cookies, Dict[str, str], None] = None,
    ) -> "Response":
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
        params: Union[QueryParams, Dict[str, str], None] = None,
        headers: Union[Headers, Dict[str, str], None] = None,
        timeout: Union[Timeout, float, None] = None,
        auth: Union[Auth, Tuple[str, str], None] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Union[Cookies, Dict[str, str], None] = None,
    ) -> "Response":
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


# ==================== Global Functions ====================

def stream(
    method: str,
    url: str,
    *,
    params: Union[QueryParams, Dict[str, str], None] = None,
    content: Optional[bytes] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    headers: Union[Headers, Dict[str, str], None] = None,
    timeout: Union[Timeout, float, None] = None,
    auth: Union[Auth, Tuple[str, str], None] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Union[Cookies, Dict[str, str], None] = None,
) -> StreamingResponse:
    """Send a streaming request."""
    with Client() as client:
        request = client.build_request(
            method, url, 
            params=_process_params(params), 
            headers=_process_headers(headers), 
            content=content
        )
        response = client.send(request)
        return StreamingResponse(response)


def get(
    url: str,
    *,
    params: Union[QueryParams, Dict[str, str], None] = None,
    headers: Union[Headers, Dict[str, str], None] = None,
    timeout: Union[Timeout, float, None] = None,
    auth: Union[Auth, Tuple[str, str], None] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Union[Cookies, Dict[str, str], None] = None,
) -> "Response":
    """Send a GET request."""
    return _get(
        url,
        params=_process_params(params),
        headers=_process_headers(headers),
        timeout=_process_timeout(timeout),
        auth=_process_auth(auth),
        follow_redirects=follow_redirects,
        cookies=_process_cookies(cookies),
    )


def post(
    url: str,
    *,
    content: Optional[bytes] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    params: Union[QueryParams, Dict[str, str], None] = None,
    headers: Union[Headers, Dict[str, str], None] = None,
    timeout: Union[Timeout, float, None] = None,
    auth: Union[Auth, Tuple[str, str], None] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Union[Cookies, Dict[str, str], None] = None,
) -> "Response":
    """Send a POST request."""
    return _post(
        url,
        content=content,
        data=data,
        json=json,
        files=files,
        params=_process_params(params),
        headers=_process_headers(headers),
        timeout=_process_timeout(timeout),
        auth=_process_auth(auth),
        follow_redirects=follow_redirects,
        cookies=_process_cookies(cookies),
    )


def put(
    url: str,
    *,
    content: Optional[bytes] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    params: Union[QueryParams, Dict[str, str], None] = None,
    headers: Union[Headers, Dict[str, str], None] = None,
    timeout: Union[Timeout, float, None] = None,
    auth: Union[Auth, Tuple[str, str], None] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Union[Cookies, Dict[str, str], None] = None,
) -> "Response":
    """Send a PUT request."""
    return _put(
        url,
        content=content,
        data=data,
        json=json,
        files=files,
        params=_process_params(params),
        headers=_process_headers(headers),
        timeout=_process_timeout(timeout),
        auth=_process_auth(auth),
        follow_redirects=follow_redirects,
        cookies=_process_cookies(cookies),
    )


def patch(
    url: str,
    *,
    content: Optional[bytes] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    params: Union[QueryParams, Dict[str, str], None] = None,
    headers: Union[Headers, Dict[str, str], None] = None,
    timeout: Union[Timeout, float, None] = None,
    auth: Union[Auth, Tuple[str, str], None] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Union[Cookies, Dict[str, str], None] = None,
) -> "Response":
    """Send a PATCH request."""
    return _patch(
        url,
        content=content,
        data=data,
        json=json,
        files=files,
        params=_process_params(params),
        headers=_process_headers(headers),
        timeout=_process_timeout(timeout),
        auth=_process_auth(auth),
        follow_redirects=follow_redirects,
        cookies=_process_cookies(cookies),
    )


def delete(
    url: str,
    *,
    params: Union[QueryParams, Dict[str, str], None] = None,
    headers: Union[Headers, Dict[str, str], None] = None,
    timeout: Union[Timeout, float, None] = None,
    auth: Union[Auth, Tuple[str, str], None] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Union[Cookies, Dict[str, str], None] = None,
) -> "Response":
    """Send a DELETE request."""
    return _delete(
        url,
        params=_process_params(params),
        headers=_process_headers(headers),
        timeout=_process_timeout(timeout),
        auth=_process_auth(auth),
        follow_redirects=follow_redirects,
        cookies=_process_cookies(cookies),
    )


def head(
    url: str,
    *,
    params: Union[QueryParams, Dict[str, str], None] = None,
    headers: Union[Headers, Dict[str, str], None] = None,
    timeout: Union[Timeout, float, None] = None,
    auth: Union[Auth, Tuple[str, str], None] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Union[Cookies, Dict[str, str], None] = None,
) -> "Response":
    """Send a HEAD request."""
    return _head(
        url,
        params=_process_params(params),
        headers=_process_headers(headers),
        timeout=_process_timeout(timeout),
        auth=_process_auth(auth),
        follow_redirects=follow_redirects,
        cookies=_process_cookies(cookies),
    )


def options(
    url: str,
    *,
    params: Union[QueryParams, Dict[str, str], None] = None,
    headers: Union[Headers, Dict[str, str], None] = None,
    timeout: Union[Timeout, float, None] = None,
    auth: Union[Auth, Tuple[str, str], None] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Union[Cookies, Dict[str, str], None] = None,
) -> "Response":
    """Send an OPTIONS request."""
    return _options(
        url,
        params=_process_params(params),
        headers=_process_headers(headers),
        timeout=_process_timeout(timeout),
        auth=_process_auth(auth),
        follow_redirects=follow_redirects,
        cookies=_process_cookies(cookies),
    )


def main():
    """Entry point for the faster-http CLI."""
    print("faster-http: High-performance HTTP client powered by Rust")
    print("For more information, visit: https://github.com/your-repo/faster-http")


if __name__ == "__main__":
    main()
