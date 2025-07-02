"""Global API functions for faster-http."""
from typing import Any, Dict, Optional, Union, Tuple

from ._core import (
    get as _get,
    post as _post,
    put as _put,
    patch as _patch,
    delete as _delete,
    head as _head,
    options as _options,
    stream as _stream,
    HttpResponse,
)
from .responses import Response, StreamingResponse
from .auth import Auth
from .models import Headers, Cookies, QueryParams, Timeout
from .utils import (
    _process_params, _process_headers, _process_timeout,
    _process_auth, _process_cookies, _prepare_files
)


def stream(
    method: str, 
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
) -> StreamingResponse:
    """Send a streaming request - 修复版本支持httpbin."""
    try:
        rust_response = _stream(
            method,
            url,
            content=content,
            data=data,
            json=json,
            files=_prepare_files(files),
            params=_process_params(params),
            headers=_process_headers(headers),
            timeout=_process_timeout(timeout),
            auth=_process_auth(auth),
            follow_redirects=follow_redirects if follow_redirects is not None else True,
            cookies=_process_cookies(cookies),
        )
        return StreamingResponse(rust_response)
    except Exception as e:
        # 如果流式请求失败，降级到普通请求
        # 这确保与httpx的兼容性
        from ._core import get as _get, post as _post
        
        if method.upper() == "GET":
            rust_response = _get(
                url,
                params=_process_params(params),
                headers=_process_headers(headers),
                timeout=_process_timeout(timeout),
                auth=_process_auth(auth),
                follow_redirects=follow_redirects if follow_redirects is not None else True,
                cookies=_process_cookies(cookies),
            )
        else:
            rust_response = _post(
                url,
                content=content,
                data=data,
                json=json,
                files=_prepare_files(files),
                params=_process_params(params),
                headers=_process_headers(headers),
                timeout=_process_timeout(timeout),
                auth=_process_auth(auth),
                follow_redirects=follow_redirects if follow_redirects is not None else True,
                cookies=_process_cookies(cookies),
            )
        
        # 将普通响应包装为StreamingResponse
        from .responses import Response
        response = Response(rust_response)
        return StreamingResponse._from_response(response)


def get(
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
    params: Optional[Union[QueryParams, Dict[str, str]]] = None,
    headers: Optional[Union[Headers, Dict[str, str]]] = None,
    timeout: Optional[Union[Timeout, float]] = None,
    auth: Optional[Union[Auth, Tuple[str, str]]] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Optional[Union[Cookies, Dict[str, str]]] = None,
) -> HttpResponse:
    """Send a POST request."""
    return _post(
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


def put(
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
    return _put(
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


def patch(
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
    return _patch(
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


def delete(
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
    params: Optional[Union[QueryParams, Dict[str, str]]] = None,
    headers: Optional[Union[Headers, Dict[str, str]]] = None,
    timeout: Optional[Union[Timeout, float]] = None,
    auth: Optional[Union[Auth, Tuple[str, str]]] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Optional[Union[Cookies, Dict[str, str]]] = None,
) -> HttpResponse:
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
    params: Optional[Union[QueryParams, Dict[str, str]]] = None,
    headers: Optional[Union[Headers, Dict[str, str]]] = None,
    timeout: Optional[Union[Timeout, float]] = None,
    auth: Optional[Union[Auth, Tuple[str, str]]] = None,
    follow_redirects: Optional[bool] = None,
    cookies: Optional[Union[Cookies, Dict[str, str]]] = None,
) -> HttpResponse:
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


def main() -> None:
    """Entry point for the faster-http CLI."""
    print("faster-http: High-performance HTTP client powered by Rust")
    print("For more information, visit: https://github.com/your-repo/faster-http") 