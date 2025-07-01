"""
faster-http: A high-performance HTTP client for Python, powered by Rust's reqwest library.

This library provides a drop-in replacement for httpx with significantly better performance
by leveraging Rust's reqwest library through PyO3 bindings.
"""
import uuid

from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Mapping, Protocol
import base64
import codecs
import os
import io
import mimetypes
from pathlib import Path

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


class BasicAuth(Auth):
    """HTTP Basic Authentication."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    def auth_flow(self, request):
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
        
        from urllib.parse import parse_qsl
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


# ==================== File Upload Utilities ====================

class FileUpload:
    """File upload helper class."""
    
    def __init__(self, filename: Optional[str] = None, 
                 content: Union[bytes, str, io.IOBase] = None, 
                 content_type: Optional[str] = None):
        self.filename = filename
        self.content = content
        self.content_type = content_type
    
    def to_bytes(self) -> bytes:
        """Convert content to bytes."""
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, str):
            return self.content.encode('utf-8')
        elif hasattr(self.content, 'read'):
            return self._read_file_like_object()
        else:
            return str(self.content).encode('utf-8')
    
    def _read_file_like_object(self) -> bytes:
        """Read content from file-like object."""
        try:
            if hasattr(self.content, 'seek'):
                try:
                    self.content.seek(0)
                except (OSError, io.UnsupportedOperation):
                    pass
            
            content_data = self.content.read()
            
            if isinstance(content_data, str):
                return content_data.encode('utf-8')
            elif isinstance(content_data, bytes):
                return content_data
            else:
                return str(content_data).encode('utf-8')
                
        except Exception as e:
            raise ValueError(f"Failed to read content from file-like object: {e}")
    
    def get_content_type(self) -> str:
        """Get content type, auto-detecting if not specified."""
        if self.content_type:
            return self.content_type
        
        if self.filename:
            guessed_type, _ = mimetypes.guess_type(self.filename)
            if guessed_type:
                return guessed_type
        
        return 'application/octet-stream'


def process_files_parameter(files: Optional[Dict[str, Any]]) -> Optional[Dict[str, FileUpload]]:
    """Process files parameter to handle various httpx-compatible formats."""
    if not files:
        return None
    
    processed_files = {}
    
    for field_name, file_spec in files.items():
        processed_files[field_name] = _process_single_file(file_spec)
    
    return processed_files


def _process_single_file(file_spec: Any) -> FileUpload:
    """Process a single file specification."""
    if isinstance(file_spec, bytes):
        return FileUpload(filename=None, content=file_spec)
    
    elif isinstance(file_spec, (str, Path)):
        return _process_string_or_path(file_spec)
    
    elif hasattr(file_spec, 'read'):
        return _process_file_like_object(file_spec)
    
    elif isinstance(file_spec, (tuple, list)) and len(file_spec) >= 2:
        return _process_tuple_format(file_spec)
    
    else:
        raise ValueError(f"Unsupported file specification: {type(file_spec)}")


def _process_string_or_path(file_spec: Union[str, Path]) -> FileUpload:
    """Process string or Path file specification."""
    # Try as file path first for reasonable length strings
    if len(str(file_spec)) < 260:
        try:
            file_path = Path(file_spec)
            if file_path.exists() and file_path.is_file():
                with open(file_path, 'rb') as f:
                    content = f.read()
                return FileUpload(filename=file_path.name, content=content)
        except (OSError, PermissionError):
            pass
    
    # Treat as string content
    return FileUpload(filename=None, content=file_spec)


def _process_file_like_object(file_spec) -> FileUpload:
    """Process file-like object."""
    filename = getattr(file_spec, 'name', None)
    if filename and hasattr(filename, 'split'):
        filename = os.path.basename(filename)
    
    return FileUpload(filename=filename, content=file_spec)


def _process_tuple_format(file_spec) -> FileUpload:
    """Process tuple format file specification."""
    filename = file_spec[0]
    content = file_spec[1]
    content_type = file_spec[2] if len(file_spec) > 2 else None
    
    # Handle file path in content
    if isinstance(content, (str, Path)) and len(str(content)) < 260:
        try:
            content_path = Path(content)
            if content_path.exists():
                with open(content_path, 'rb') as f:
                    content = f.read()
                if not filename:
                    filename = content_path.name
        except (OSError, PermissionError):
            pass
    
    return FileUpload(filename=filename, content=content, content_type=content_type)


# ==================== Response Classes ====================

class StreamingResponse:
    """Streaming response with httpx compatibility."""
    
    def __init__(self, response, request=None):
        self._response = response
        self._request = request
        self._consumed = False
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
    
    def _check_consumed(self):
        """Check if response has been consumed."""
        if self._consumed:
            raise RuntimeError("Response stream has been consumed")
    
    # Delegate properties to underlying response
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return getattr(self._response, name)
    
    @property
    def request(self):
        return self._request
    
    def read(self) -> bytes:
        """Read complete response content."""
        self._check_consumed()
        self._consumed = True
        return self._response.content
    
    def iter_bytes(self, chunk_size: int = 8192):
        """Iterate response bytes."""
        self._check_consumed()
        self._consumed = True
        return self._response.iter_bytes(chunk_size)
    
    def iter_text(self, chunk_size: int = 8192):
        """Iterate response text."""
        self._check_consumed()
        self._consumed = True
        return self._response.iter_text(chunk_size)
    
    def iter_lines(self):
        """Iterate response lines."""
        self._check_consumed()
        self._consumed = True
        return self._response.iter_lines()
    
    def iter_raw(self, chunk_size: int = 8192):
        """Iterate raw response content."""
        return self.iter_bytes(chunk_size)
    
    async def aiter_bytes(self, chunk_size: int = 8192):
        """Async iterate response bytes."""
        self._check_consumed()
        self._consumed = True
        # Simulate async iteration for now
        for chunk in self._response.iter_bytes(chunk_size):
            yield chunk
    
    async def aiter_text(self, chunk_size: int = 8192):
        """Async iterate response text."""
        self._check_consumed()
        self._consumed = True
        for text in self._response.iter_text(chunk_size):
            yield text
    
    async def aiter_lines(self):
        """Async iterate response lines."""
        self._check_consumed()
        self._consumed = True
        for line in self._response.iter_lines():
            yield line
    
    def iter_sse_events(self):
        """Iterate Server-Sent Events."""
        self._check_consumed()
        self._consumed = True
        
        current_event = {}
        for line in self.iter_lines():
            line = line.strip()
            
            if not line:
                if current_event:
                    yield SSEEvent(**current_event)
                    current_event = {}
                continue
            
            if line.startswith(':'):
                continue
            
            if ':' in line:
                field, value = line.split(':', 1)
                value = value.lstrip()
            else:
                field, value = line, ''
            
            if field == 'data':
                if 'data' in current_event:
                    current_event['data'] += '\n' + value
                else:
                    current_event['data'] = value
            elif field in ('event', 'id', 'retry'):
                current_event[field] = value
        
        if current_event:
            yield SSEEvent(**current_event)
    
    async def aiter_sse_events(self):
        """Async iterate Server-Sent Events."""
        async for line in self.aiter_lines():
            # Implementation similar to iter_sse_events
            pass
    
    def close(self):
        """Close the response."""
        self._consumed = True
        if hasattr(self._response, 'close'):
            self._response.close()
    
    async def aclose(self):
        """Async close the response."""
        self._consumed = True
        if hasattr(self._response, 'aclose'):
            await self._response.aclose()
        elif hasattr(self._response, 'close'):
            self._response.close()
    
    def raise_for_status(self):
        """Check status and raise exception if needed."""
        return self._response.raise_for_status()


class SSEEvent:
    """Server-Sent Event."""
    
    def __init__(self, data='', event=None, id=None, retry=None):
        self.data = data
        self.event = event
        self.id = id
        self.retry = int(retry) if retry else None
    
    def __repr__(self):
        return f"SSEEvent(data={self.data!r}, event={self.event!r}, id={self.id!r})"
    
    def json(self):
        """Parse data field as JSON."""
        import json
        return json.loads(self.data)


class Response(Protocol):
    """HTTP Response protocol."""
    
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
    
    def json(self) -> Any: ...
    
    def raise_for_status(self) -> None: ...


# Use Rust's HttpClient and HttpRequest
Client = _HttpClient
Request = _HttpRequest


# ==================== Utility Functions ====================

def _process_auth(auth: Union[Auth, Tuple[str, str], None]) -> Optional[Tuple[str, str]]:
    """Process authentication parameter."""
    if auth is None:
        return None
    elif isinstance(auth, tuple) and len(auth) == 2:
        return (str(auth[0]), str(auth[1]))
    elif isinstance(auth, BasicAuth):
        return (auth.username, auth.password)
    elif hasattr(auth, 'username') and hasattr(auth, 'password'):
        return (auth.username, auth.password)
    return None


def _process_headers(headers: Union[Headers, Dict[str, str], None]) -> Optional[Dict[str, str]]:
    """Process headers parameter."""
    return dict(headers) if isinstance(headers, Headers) else headers


def _process_cookies(cookies: Union[Cookies, Dict[str, str], None]) -> Optional[Dict[str, str]]:
    """Process cookies parameter."""
    return dict(cookies) if isinstance(cookies, Cookies) else cookies


def _process_params(params: Union[QueryParams, Dict[str, str], None]) -> Optional[Dict[str, str]]:
    """Process params parameter."""
    return dict(params) if isinstance(params, QueryParams) else params


def _process_timeout(timeout: Union[Timeout, float, None]) -> Optional[float]:
    """Process timeout parameter."""
    if isinstance(timeout, Timeout):
        return timeout.read or 30.0
    return timeout


def _prepare_files(files: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Prepare files for upload."""
    if files is None:
        return None
    
    processed_files = process_files_parameter(files)
    if processed_files:
        return {field_name: file_upload for field_name, file_upload in processed_files.items()}
    return None


# ==================== Async Client ====================

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
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def get(self, url: str, **kwargs) -> "Response":
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
    
    async def post(self, url: str, **kwargs) -> "Response":
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
    
    async def put(self, url: str, **kwargs) -> "Response":
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
    
    async def patch(self, url: str, **kwargs) -> "Response":
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
    
    async def delete(self, url: str, **kwargs) -> "Response":
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
    
    async def head(self, url: str, **kwargs) -> "Response":
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
    
    async def options(self, url: str, **kwargs) -> "Response":
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


# ==================== Global Functions ====================

def stream(method: str, url: str, **kwargs) -> StreamingResponse:
    """Send a streaming request."""
    with Client() as client:
        request = client.build_request(
            method, url, 
            params=_process_params(kwargs.get('params')), 
            headers=_process_headers(kwargs.get('headers')), 
            content=kwargs.get('content')
        )
        response = client.send(request)
        return StreamingResponse(response, request)


def get(url: str, **kwargs) -> "Response":
    """Send a GET request."""
    return _get(
        url,
        params=_process_params(kwargs.get('params')),
        headers=_process_headers(kwargs.get('headers')),
        timeout=_process_timeout(kwargs.get('timeout')),
        auth=_process_auth(kwargs.get('auth')),
        follow_redirects=kwargs.get('follow_redirects'),
        cookies=_process_cookies(kwargs.get('cookies')),
    )


def post(url: str, **kwargs) -> "Response":
    """Send a POST request."""
    return _post(
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


def put(url: str, **kwargs) -> "Response":
    """Send a PUT request."""
    return _put(
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


def patch(url: str, **kwargs) -> "Response":
    """Send a PATCH request."""
    return _patch(
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


def delete(url: str, **kwargs) -> "Response":
    """Send a DELETE request."""
    return _delete(
        url,
        params=_process_params(kwargs.get('params')),
        headers=_process_headers(kwargs.get('headers')),
        timeout=_process_timeout(kwargs.get('timeout')),
        auth=_process_auth(kwargs.get('auth')),
        follow_redirects=kwargs.get('follow_redirects'),
        cookies=_process_cookies(kwargs.get('cookies')),
    )


def head(url: str, **kwargs) -> "Response":
    """Send a HEAD request."""
    return _head(
        url,
        params=_process_params(kwargs.get('params')),
        headers=_process_headers(kwargs.get('headers')),
        timeout=_process_timeout(kwargs.get('timeout')),
        auth=_process_auth(kwargs.get('auth')),
        follow_redirects=kwargs.get('follow_redirects'),
        cookies=_process_cookies(kwargs.get('cookies')),
    )


def options(url: str, **kwargs) -> "Response":
    """Send an OPTIONS request."""
    return _options(
        url,
        params=_process_params(kwargs.get('params')),
        headers=_process_headers(kwargs.get('headers')),
        timeout=_process_timeout(kwargs.get('timeout')),
        auth=_process_auth(kwargs.get('auth')),
        follow_redirects=kwargs.get('follow_redirects'),
        cookies=_process_cookies(kwargs.get('cookies')),
    )


def main():
    """Entry point for the faster-http CLI."""
    print("faster-http: High-performance HTTP client powered by Rust")
    print("For more information, visit: https://github.com/your-repo/faster-http")


if __name__ == "__main__":
    main()
