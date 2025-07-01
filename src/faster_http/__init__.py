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


# ==================== File Upload Utilities ====================

class FileUpload:
    """File upload helper class supporting multiple input formats."""
    
    def __init__(self, filename: Optional[str] = None, content: Union[bytes, str, io.IOBase] = None, 
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
            # File-like object
            try:
                # Try to seek to beginning if possible
                if hasattr(self.content, 'seek'):
                    try:
                        self.content.seek(0)
                    except (OSError, io.UnsupportedOperation):
                        pass
                
                content_data = self.content.read()
                
                # Handle both text and binary file objects
                if isinstance(content_data, str):
                    return content_data.encode('utf-8')
                elif isinstance(content_data, bytes):
                    return content_data
                else:
                    # Convert any other type to string first
                    return str(content_data).encode('utf-8')
                    
            except Exception as e:
                raise ValueError(f"Failed to read content from file-like object: {e}")
        else:
            # Convert any other type to string and then to bytes
            return str(self.content).encode('utf-8')
    
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
    """
    Process files parameter to handle various httpx-compatible formats:
    
    - files = {'upload-file': open('report.xls', 'rb')}
    - files = {'upload-file': b'file content'}
    - files = {'upload-file': 'text content'}
    - files = {'upload-file': ('filename.txt', open('file.txt', 'rb'))}
    - files = {'upload-file': ('filename.txt', b'content', 'text/plain')}
    - files = {'upload-file': (None, 'text content', 'text/plain')}
    - files = {'upload-file': '/path/to/file.txt'}
    """
    if not files:
        return None
    
    processed_files = {}
    
    for field_name, file_spec in files.items():
        if isinstance(file_spec, bytes):
            # Raw bytes content
            processed_files[field_name] = FileUpload(
                filename=None,
                content=file_spec,
                content_type=None
            )
        
        elif isinstance(file_spec, (str, Path)):
            # String can be either file path or content
            if isinstance(file_spec, Path) or (isinstance(file_spec, str) and len(file_spec) < 260):
                # Try as file path first
                try:
                    file_path = Path(file_spec)
                    if file_path.exists() and file_path.is_file():
                        with open(file_path, 'rb') as f:
                            content = f.read()
                        
                        processed_files[field_name] = FileUpload(
                            filename=file_path.name,
                            content=content,
                            content_type=None  # Will be auto-detected
                        )
                        continue
                except (OSError, PermissionError):
                    pass
            
            # Treat as string content
            processed_files[field_name] = FileUpload(
                filename=None,
                content=file_spec,
                content_type=None
            )
        
        elif hasattr(file_spec, 'read'):
            # File-like object (including BytesIO, StringIO, file objects)
            filename = getattr(file_spec, 'name', None)
            if filename and hasattr(filename, 'split'):
                filename = os.path.basename(filename)
            
            # Try to seek to beginning if possible
            if hasattr(file_spec, 'seek'):
                try:
                    file_spec.seek(0)
                except (OSError, io.UnsupportedOperation):
                    pass
            
            processed_files[field_name] = FileUpload(
                filename=filename,
                content=file_spec,
                content_type=None
            )
        
        elif isinstance(file_spec, (tuple, list)) and len(file_spec) >= 2:
            # Tuple format: (filename, content) or (filename, content, content_type)
            filename = file_spec[0]
            content = file_spec[1]
            content_type = file_spec[2] if len(file_spec) > 2 else None
            
            # Handle file path in content
            if isinstance(content, (str, Path)) and len(str(content)) < 260:  # Likely a file path
                try:
                    content_path = Path(content)
                    if content_path.exists():
                        with open(content_path, 'rb') as f:
                            content = f.read()
                        if not filename:
                            filename = content_path.name
                except (OSError, PermissionError):
                    # If it fails, treat as content string
                    pass
            
            processed_files[field_name] = FileUpload(
                filename=filename,
                content=content,
                content_type=content_type
            )
        
        else:
            raise ValueError(f"Unsupported file specification for '{field_name}': {type(file_spec)}")
    
    return processed_files


def create_form_data_payload(
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, FileUpload]] = None
) -> Tuple[bytes, str]:
    """
    Create multipart/form-data payload.
    Returns (payload_bytes, content_type_with_boundary)
    """
    boundary = uuid.uuid4().hex
    content_type = f'multipart/form-data; boundary={boundary}'
    
    parts = []
    
    # Add regular form fields
    if data:
        for name, value in data.items():
            part = f'--{boundary}\r\n'
            part += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            part += str(value) + '\r\n'
            parts.append(part.encode('utf-8'))
    
    # Add file fields
    if files:
        for field_name, file_upload in files.items():
            part = f'--{boundary}\r\n'
            
            if file_upload.filename:
                part += f'Content-Disposition: form-data; name="{field_name}"; filename="{file_upload.filename}"\r\n'
            else:
                part += f'Content-Disposition: form-data; name="{field_name}"\r\n'
            
            content_type_header = file_upload.get_content_type()
            part += f'Content-Type: {content_type_header}\r\n\r\n'
            
            parts.append(part.encode('utf-8'))
            parts.append(file_upload.to_bytes())
            parts.append(b'\r\n')
    
    # Add final boundary
    parts.append(f'--{boundary}--\r\n'.encode('utf-8'))
    
    payload = b''.join(parts)
    return payload, content_type


def prepare_request_data(
    content: Optional[bytes] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Prepare request data with proper content type.
    Returns (body_bytes, content_type)
    
    Priority: content > files > json > data
    """
    # Priority 1: Raw content
    if content is not None:
        return content, None
    
    # Priority 2: Files (multipart/form-data)  
    if files is not None:
        processed_files = process_files_parameter(files)
        if processed_files or data:
            body, content_type = create_form_data_payload(data, processed_files)
            return body, content_type
        elif processed_files:
            # 只有文件，没有其他数据
            body, content_type = create_form_data_payload(None, processed_files)
            return body, content_type
    
    # Priority 3: JSON
    if json is not None:
        import json as json_module
        json_str = json_module.dumps(json)
        return json_str.encode('utf-8'), 'application/json'
    
    # Priority 4: Form data
    if data is not None:
        from urllib.parse import urlencode
        form_str = urlencode(data)
        return form_str.encode('utf-8'), 'application/x-www-form-urlencoded'
    
    return None, None


# ==================== Response and Request Classes ====================

class StreamingResponse:
    """Enhanced streaming response with full httpx compatibility."""
    
    def __init__(self, response, request=None):
        self._response = response
        self._request = request
        self._consumed = False
        self._stream_consumed = False
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
    
    # ========== 基础属性 ==========
    @property
    def status_code(self):
        return self._response.status_code
    
    @property
    def headers(self):
        return self._response.headers
    
    @property
    def url(self):
        return self._response.url
        
    @property
    def ok(self):
        return self._response.ok
        
    @property
    def http_version(self):
        return self._response.http_version
        
    @property
    def is_redirect(self):
        return self._response.is_redirect
        
    @property
    def is_client_error(self):
        return self._response.is_client_error
        
    @property
    def is_server_error(self):
        return self._response.is_server_error
    
    @property
    def request(self):
        return self._request
    
    @property
    def num_bytes_downloaded(self) -> int:
        """已下载的字节数 (httpx 兼容)"""
        if hasattr(self._response, 'num_bytes_downloaded'):
            return self._response.num_bytes_downloaded
        return len(self._response.content) if not self._stream_consumed else 0
    
    # ========== 内容访问 ==========
    @property
    def content(self) -> bytes:
        """获取响应内容（一次性读取）"""
        if self._stream_consumed:
            raise RuntimeError("Response stream has been consumed")
        return self._response.content
    
    @property
    def text(self) -> str:
        """获取响应文本（一次性读取）"""
        if self._stream_consumed:
            raise RuntimeError("Response stream has been consumed")
        return self._response.text
    
    def json(self):
        """解析 JSON 响应"""
        if self._stream_consumed:
            raise RuntimeError("Response stream has been consumed")
        return self._response.json()
    
    def read(self) -> bytes:
        """读取完整响应内容（httpx 兼容）"""
        if self._stream_consumed:
            raise RuntimeError("Response stream has been consumed")
        self._stream_consumed = True
        return self._response.content
    
    # ========== 同步流式迭代 ==========
    def iter_bytes(self, chunk_size: int = 8192):
        """迭代响应的字节内容"""
        if self._stream_consumed or self._consumed:
            raise RuntimeError("Response stream has been consumed")
        
        # 标记为已消费
        self._stream_consumed = True
        
        # 如果响应对象支持真正的流式处理
        if hasattr(self._response, 'stream_bytes'):
            return self._response.stream_bytes(chunk_size)
        else:
            # 模拟分块读取
            content = self._response.content
            chunks = []
            for i in range(0, len(content), chunk_size):
                chunks.append(content[i:i + chunk_size])
            return chunks
    
    def iter_text(self, chunk_size: int = 8192, decode_unicode: bool = True):
        """迭代响应的文本内容"""
        if self._stream_consumed or self._consumed:
            raise RuntimeError("Response stream has been consumed")
        
        # 标记为已消费
        self._stream_consumed = True
            
        # 如果响应对象支持真正的流式文本处理
        if hasattr(self._response, 'stream_text'):
            return self._response.stream_text(chunk_size, decode_unicode)
        else:
            # 基于字节块解码文本
            decoder = codecs.getincrementaldecoder(self._response.encoding or 'utf-8')()
            content = self._response.content
            text_chunks = []
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                text_chunk = decoder.decode(chunk, False)
                if text_chunk:
                    text_chunks.append(text_chunk)
            # 处理剩余字节
            final_chunk = decoder.decode(b'', True)
            if final_chunk:
                text_chunks.append(final_chunk)
            return text_chunks
    
    def iter_lines(self, chunk_size: int = 8192, decode_unicode: bool = True, delimiter: str = '\n'):
        """迭代响应的行内容"""
        if self._stream_consumed or self._consumed:
            raise RuntimeError("Response stream has been consumed")
        
        # 标记为已消费
        self._stream_consumed = True
            
        buffer = ""
        decoder = codecs.getincrementaldecoder(self._response.encoding or 'utf-8')()
        content = self._response.content
        lines = []
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            text_chunk = decoder.decode(chunk, False)
            buffer += text_chunk
            while delimiter in buffer:
                line, buffer = buffer.split(delimiter, 1)
                lines.append(line)
        
        # 处理剩余字节和最后一行
        final_chunk = decoder.decode(b'', True)
        buffer += final_chunk
        if buffer:
            lines.append(buffer)
        
        return lines
    
    def iter_raw(self, chunk_size: int = 8192):
        """迭代原始字节内容（与 iter_bytes 相同，httpx 兼容）"""
        yield from self.iter_bytes(chunk_size)
    
    # ========== 异步流式迭代 ==========
    async def aiter_bytes(self, chunk_size: int = 8192):
        """异步迭代响应的字节内容"""
        if self._stream_consumed:
            raise RuntimeError("Response stream has been consumed")
        
        # 如果响应对象支持异步流式处理
        if hasattr(self._response, 'astream_bytes'):
            self._stream_consumed = True
            async for chunk in self._response.astream_bytes(chunk_size):
                yield chunk
        else:
            # 模拟异步分块读取
            content = self._response.content
            self._stream_consumed = True
            for i in range(0, len(content), chunk_size):
                yield content[i:i + chunk_size]
    
    async def aiter_text(self, chunk_size: int = 8192, decode_unicode: bool = True):
        """异步迭代响应的文本内容"""
        if self._stream_consumed:
            raise RuntimeError("Response stream has been consumed")
            
        decoder = codecs.getincrementaldecoder(self._response.encoding or 'utf-8')()
        async for chunk in self.aiter_bytes(chunk_size):
            text_chunk = decoder.decode(chunk, False)
            if text_chunk:
                yield text_chunk
        # 处理剩余字节
        final_chunk = decoder.decode(b'', True)
        if final_chunk:
            yield final_chunk
    
    async def aiter_lines(self, chunk_size: int = 8192, decode_unicode: bool = True, delimiter: str = '\n'):
        """异步迭代响应的行内容"""
        if self._stream_consumed:
            raise RuntimeError("Response stream has been consumed")
            
        buffer = ""
        async for text_chunk in self.aiter_text(chunk_size, decode_unicode):
            buffer += text_chunk
            while delimiter in buffer:
                line, buffer = buffer.split(delimiter, 1)
                yield line
        
        # 返回最后一行（如果有的话）
        if buffer:
            yield buffer
    
    async def aiter_raw(self, chunk_size: int = 8192):
        """异步迭代原始字节内容"""
        async for chunk in self.aiter_bytes(chunk_size):
            yield chunk
    
    # ========== SSE 支持 ==========
    def iter_sse_events(self):
        """迭代 Server-Sent Events (SSE) 事件"""
        if self._stream_consumed:
            raise RuntimeError("Response stream has been consumed")
        
        # 如果响应对象有专门的 SSE 支持
        if hasattr(self._response, 'iter_sse_events'):
            self._stream_consumed = True
            yield from self._response.iter_sse_events()
        else:
            # 手动解析 SSE 事件
            current_event = {}
            for line in self.iter_lines():
                line = line.strip()
                
                if not line:
                    # 空行表示事件结束
                    if current_event:
                        yield SSEEvent(**current_event)
                        current_event = {}
                    continue
                
                if line.startswith(':'):
                    # 注释行，忽略
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
            
            # 处理最后一个事件
            if current_event:
                yield SSEEvent(**current_event)
    
    async def aiter_sse_events(self):
        """异步迭代 Server-Sent Events (SSE) 事件"""
        if self._stream_consumed:
            raise RuntimeError("Response stream has been consumed")
        
        current_event = {}
        async for line in self.aiter_lines():
            line = line.strip()
            
            if not line:
                # 空行表示事件结束
                if current_event:
                    yield SSEEvent(**current_event)
                    current_event = {}
                continue
            
            if line.startswith(':'):
                # 注释行，忽略
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
        
        # 处理最后一个事件
        if current_event:
            yield SSEEvent(**current_event)
    
    # ========== 流控制方法 ==========
    def close(self):
        """关闭流式响应"""
        self._consumed = True
        self._stream_consumed = True
        if hasattr(self._response, 'close'):
            self._response.close()
    
    async def aclose(self):
        """异步关闭流式响应"""
        self._consumed = True
        self._stream_consumed = True
        if hasattr(self._response, 'aclose'):
            await self._response.aclose()
        elif hasattr(self._response, 'close'):
            self._response.close()
    
    def raise_for_status(self):
        """检查状态码并抛出异常"""
        return self._response.raise_for_status()


# SSE 事件类
class SSEEvent:
    """Server-Sent Event"""
    
    def __init__(self, data='', event=None, id=None, retry=None):
        self.data = data
        self.event = event
        self.id = id
        self.retry = int(retry) if retry else None
    
    def __repr__(self):
        return f"SSEEvent(data={self.data!r}, event={self.event!r}, id={self.id!r})"
    
    def json(self):
        """解析 data 字段为 JSON"""
        import json
        return json.loads(self.data)


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
    elif isinstance(auth, tuple) and len(auth) == 2:
        # 确保元组格式正确
        return (str(auth[0]), str(auth[1]))
    elif isinstance(auth, BasicAuth):
        return (auth.username, auth.password)
    elif isinstance(auth, (DigestAuth, NetRCAuth)):
        # 对于更复杂的认证，暂时返回 None
        return None
    else:
        # 尝试提取用户名和密码属性
        if hasattr(auth, 'username') and hasattr(auth, 'password'):
            return (auth.username, auth.password)
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
        # 预处理文件数据
        processed_files = None
        if files is not None:
            processed_files = process_files_parameter(files)
            if processed_files:
                files = {field_name: file_upload for field_name, file_upload in processed_files.items()}
        
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
        # 预处理文件数据
        if files is not None:
            processed_files = process_files_parameter(files)
            if processed_files:
                files = {field_name: file_upload for field_name, file_upload in processed_files.items()}
        
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
        # 预处理文件数据
        if files is not None:
            processed_files = process_files_parameter(files)
            if processed_files:
                files = {field_name: file_upload for field_name, file_upload in processed_files.items()}
        
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
    # 预处理文件数据
    processed_files = None
    if files is not None:
        processed_files = process_files_parameter(files)
        if processed_files:
            # 将处理后的文件转换为可传递给Rust的格式
            files = {field_name: file_upload for field_name, file_upload in processed_files.items()}
    
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
    # 预处理文件数据
    if files is not None:
        processed_files = process_files_parameter(files)
        if processed_files:
            files = {field_name: file_upload for field_name, file_upload in processed_files.items()}
    
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
    # 预处理文件数据
    if files is not None:
        processed_files = process_files_parameter(files)
        if processed_files:
            files = {field_name: file_upload for field_name, file_upload in processed_files.items()}
    
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
