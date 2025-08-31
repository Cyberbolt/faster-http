"""
faster-http: HTTP client compatible with httpx API, powered by Rust's hyper library.

This library provides a drop-in replacement for httpx API, implemented using Rust's hyper library through PyO3 bindings.
"""

# All imports at the top following Python best practices
from . import proxy as _proxy_module
from ._core import (
    URL,
    USE_CLIENT_DEFAULT,
    ASGITransport,
    AsyncBaseTransport,
    AsyncByteStream,
    AsyncHTTPTransport,
    Auth,
    BaseTransport,
    BasicAuth,
    ByteStream,
    CloseError,
    ConnectError,
    ConnectTimeout,
    CookieConflict,
    Cookies,
    DecodingError,
    DigestAuth,
    Headers,
    HTTPError,
    HTTPStatusError,
    HTTPTransport,
    InvalidURL,
    Limits,
    LocalProtocolError,
    MockTransport,
    NetRCAuth,
    NetworkError,
    PoolTimeout,
    ProtocolError,
    ProxyError,
    QueryParams,
    ReadError,
    ReadTimeout,
    RemoteProtocolError,
    RequestError,
    RequestNotRead,
    ResponseNotRead,
    StreamClosed,
    StreamConsumed,
    StreamError,
    SyncByteStream,
    TimeoutException,
    TooManyRedirects,
    TransportError,
    UnsupportedProtocol,
    WriteError,
    WriteTimeout,
    WSGITransport,
    create_ssl_context,
    delete,
    get,
    head,
    main,
    options,
    patch,
    post,
    put,
    request,
    stream,
)
from ._core import (
    HttpRequest as Request,
)
from ._core import (
    HttpResponse as Response,
)
from ._timeout import Timeout
from ._wrapper_client import AsyncClient, Client
from .codes import codes

__version__ = "0.1.0"
__title__ = "faster-http"
__description__ = "HTTP client compatible with httpx API, powered by Rust's hyper library"
__name = "faster-http"
# All imports now at the top

# Proxy setup
Proxy = _proxy_module.Proxy
del _proxy_module

# Add __locals for httpx compatibility
__locals = locals()

# Store original Rust HTTP functions
_rust_get = get
_rust_post = post
_rust_put = put
_rust_patch = patch
_rust_delete = delete
_rust_head = head
_rust_options = options
_rust_request = request

# Create module-level default timeout to avoid B008 warning
_MODULE_DEFAULT_TIMEOUT = Timeout(timeout=5.0)

# Create Python wrapper functions with proper default values
def get(url, *, params=None, headers=None, cookies=None, auth=None, proxy=None,
        follow_redirects=False, verify=True, timeout=_MODULE_DEFAULT_TIMEOUT, trust_env=True):
    """Send GET request with httpx-compatible defaults."""
    # Convert timeout to float for Rust layer
    timeout_val = timeout.connect if hasattr(timeout, 'connect') and timeout.connect is not None else 5.0
    return _rust_get(url, params=params, headers=headers, cookies=cookies, auth=auth,
                     proxy=proxy, follow_redirects=follow_redirects, verify=verify,
                     timeout=timeout_val, trust_env=trust_env)

def post(url, *, content=None, data=None, json=None, files=None, params=None, headers=None,
         cookies=None, auth=None, proxy=None, follow_redirects=False, verify=True,
         timeout=_MODULE_DEFAULT_TIMEOUT, trust_env=True):
    """Send POST request with httpx-compatible defaults."""
    timeout_val = timeout.connect if hasattr(timeout, 'connect') and timeout.connect is not None else 5.0
    return _rust_post(url, content=content, data=data, json=json, files=files, params=params,
                      headers=headers, cookies=cookies, auth=auth, proxy=proxy,
                      follow_redirects=follow_redirects, verify=verify, timeout=timeout_val,
                      trust_env=trust_env)

def put(url, *, content=None, data=None, json=None, files=None, params=None, headers=None,
        cookies=None, auth=None, proxy=None, follow_redirects=False, verify=True,
        timeout=_MODULE_DEFAULT_TIMEOUT, trust_env=True):
    """Send PUT request with httpx-compatible defaults."""
    timeout_val = timeout.connect if hasattr(timeout, 'connect') and timeout.connect is not None else 5.0
    return _rust_put(url, content=content, data=data, json=json, files=files, params=params,
                     headers=headers, cookies=cookies, auth=auth, proxy=proxy,
                     follow_redirects=follow_redirects, verify=verify, timeout=timeout_val,
                     trust_env=trust_env)

def patch(url, *, content=None, data=None, json=None, files=None, params=None, headers=None,
          cookies=None, auth=None, proxy=None, follow_redirects=False, verify=True,
          timeout=_MODULE_DEFAULT_TIMEOUT, trust_env=True):
    """Send PATCH request with httpx-compatible defaults."""
    timeout_val = timeout.connect if hasattr(timeout, 'connect') and timeout.connect is not None else 5.0
    return _rust_patch(url, content=content, data=data, json=json, files=files, params=params,
                       headers=headers, cookies=cookies, auth=auth, proxy=proxy,
                       follow_redirects=follow_redirects, verify=verify, timeout=timeout_val,
                       trust_env=trust_env)

def delete(url, *, params=None, headers=None, cookies=None, auth=None, proxy=None,
           follow_redirects=False, verify=True, timeout=_MODULE_DEFAULT_TIMEOUT, trust_env=True):
    """Send DELETE request with httpx-compatible defaults."""
    timeout_val = timeout.connect if hasattr(timeout, 'connect') and timeout.connect is not None else 5.0
    return _rust_delete(url, params=params, headers=headers, cookies=cookies, auth=auth,
                        proxy=proxy, follow_redirects=follow_redirects, verify=verify,
                        timeout=timeout_val, trust_env=trust_env)

def head(url, *, params=None, headers=None, cookies=None, auth=None, proxy=None,
         follow_redirects=False, verify=True, timeout=_MODULE_DEFAULT_TIMEOUT, trust_env=True):
    """Send HEAD request with httpx-compatible defaults."""
    timeout_val = timeout.connect if hasattr(timeout, 'connect') and timeout.connect is not None else 5.0
    return _rust_head(url, params=params, headers=headers, cookies=cookies, auth=auth,
                      proxy=proxy, follow_redirects=follow_redirects, verify=verify,
                      timeout=timeout_val, trust_env=trust_env)

def options(url, *, params=None, headers=None, cookies=None, auth=None, proxy=None,
            follow_redirects=False, verify=True, timeout=_MODULE_DEFAULT_TIMEOUT, trust_env=True):
    """Send OPTIONS request with httpx-compatible defaults."""
    timeout_val = timeout.connect if hasattr(timeout, 'connect') and timeout.connect is not None else 5.0
    return _rust_options(url, params=params, headers=headers, cookies=cookies, auth=auth,
                         proxy=proxy, follow_redirects=follow_redirects, verify=verify,
                         timeout=timeout_val, trust_env=trust_env)

def request(method, url, *, content=None, data=None, json=None, files=None, params=None,
            headers=None, cookies=None, auth=None, proxy=None, follow_redirects=False,
            verify=True, timeout=_MODULE_DEFAULT_TIMEOUT, trust_env=True):
    """Send HTTP request with httpx-compatible defaults."""
    timeout_val = timeout.connect if hasattr(timeout, 'connect') and timeout.connect is not None else 5.0
    return _rust_request(method, url, content=content, data=data, json=json, files=files,
                         params=params, headers=headers, cookies=cookies, auth=auth,
                         proxy=proxy, follow_redirects=follow_redirects, verify=verify,
                         timeout=timeout_val, trust_env=trust_env)

# All exception classes are now implemented in Rust and imported from _core
# Remove non-httpx compatible aliases - these don't exist in httpx

# Enhance HTTPStatusError and RequestError to support keyword arguments
# Store original constructors in closure scope to avoid variable deletion issues
def _create_enhanced_exceptions():
    """Create enhanced exception classes with keyword argument support."""
    # Store original constructors in local scope
    orig_http_status_error_init = HTTPStatusError.__init__
    orig_request_error_init = RequestError.__init__

    def enhanced_httpstatuserror_init(self, message=None, *, request=None, response=None):
        """Enhanced HTTPStatusError initializer with keyword argument support."""
        if message is None:
            message = "HTTP status error"
        # Call original constructor
        orig_http_status_error_init(self, message)
        # Store request and response as attributes for httpx compatibility
        if request is not None:
            self.request = request
        if response is not None:
            self.response = response

    def enhanced_requesterror_init(self, message=None, *, request=None):
        """Enhanced RequestError initializer with keyword argument support."""
        if message is None:
            message = "Request error"
        # Call original constructor
        orig_request_error_init(self, message)
        if request is not None:
            self.request = request

    # Apply enhanced implementations
    HTTPStatusError.__init__ = enhanced_httpstatuserror_init
    RequestError.__init__ = enhanced_requesterror_init

    return enhanced_httpstatuserror_init, enhanced_requesterror_init

# Create enhanced exceptions and store references to prevent garbage collection
_enhanced_httpstatuserror_init, _enhanced_requesterror_init = _create_enhanced_exceptions()


# Note: Transport and authentication classes are implemented in Rust
# Stream functionality is provided through the Response object


# Remove non-httpx constants


# Define public API
__all__ = [
    "URL",
    "USE_CLIENT_DEFAULT",
    "ASGITransport",
    "AsyncBaseTransport",
    "AsyncByteStream",
    "AsyncClient",
    "AsyncHTTPTransport",
    "Auth",
    "BaseTransport",
    "BasicAuth",
    "ByteStream",
    "Client",
    "CloseError",
    "ConnectError",
    "ConnectTimeout",
    "CookieConflict",
    "Cookies",
    "DecodingError",
    "DigestAuth",
    "HTTPError",
    "HTTPStatusError",
    "HTTPTransport",
    "Headers",
    "InvalidURL",
    "Limits",
    "LocalProtocolError",
    "MockTransport",
    "NetRCAuth",
    "NetworkError",
    "PoolTimeout",
    "ProtocolError",
    "Proxy",
    "ProxyError",
    "QueryParams",
    "ReadError",
    "ReadTimeout",
    "RemoteProtocolError",
    "Request",
    "RequestError",
    "RequestNotRead",
    "Response",
    "ResponseNotRead",
    "StreamClosed",
    "StreamConsumed",
    "StreamError",
    "SyncByteStream",
    "Timeout",
    "TimeoutException",
    "TooManyRedirects",
    "TransportError",
    "UnsupportedProtocol",
    "WSGITransport",
    "WriteError",
    "WriteTimeout",
    "codes",
    "create_ssl_context",
    "delete",
    "get",
    "head",
    "main",
    "options",
    "patch",
    "post",
    "put",
    "request",
    "stream",
]

# Hide internal implementation details from public API at module end

# Hide internal modules that shouldn't be exposed in httpx API
try:
    del _core
except NameError:
    pass

try:
    del _timeout
except NameError:
    pass

try:
    del _wrapper_client
except NameError:
    pass

# Explicitly remove proxy module reference to prevent exposure
try:
    del proxy
except NameError:
    pass

if __name__ == "__main__":
    import sys
    # Module information available through __doc__ or help() if needed
    sys.exit(0)
