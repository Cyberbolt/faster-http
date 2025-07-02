"""Global API functions for faster-http."""
from typing import Any, Dict, Optional, Union

from ._core import (
    get as _get,
    post as _post,
    put as _put,
    patch as _patch,
    delete as _delete,
    head as _head,
    options as _options,
    stream as _stream,
)
from .responses import Response, StreamingResponse
from .utils import (
    _process_params, _process_headers, _process_timeout,
    _process_auth, _process_cookies, _prepare_files
)


def stream(method: str, url: str, **kwargs) -> StreamingResponse:
    """Send a streaming request - 真正的生产级流式处理."""
    rust_response = _stream(
        method,
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
    return StreamingResponse(rust_response)


def get(url: str, **kwargs) -> Response:
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


def post(url: str, **kwargs) -> Response:
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


def put(url: str, **kwargs) -> Response:
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


def patch(url: str, **kwargs) -> Response:
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


def delete(url: str, **kwargs) -> Response:
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


def head(url: str, **kwargs) -> Response:
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


def options(url: str, **kwargs) -> Response:
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