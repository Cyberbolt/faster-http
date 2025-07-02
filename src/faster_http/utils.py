"""Utility functions for faster-http - 零开销优化版本."""
from typing import Any, Dict, Optional, Tuple, Union

from .auth import Auth, BasicAuth
from .models import Headers, Cookies, QueryParams, Timeout
from .files import process_files_parameter


def _process_auth(auth: Union[Auth, Tuple[str, str], None]) -> Optional[Tuple[str, str]]:
    """Process authentication parameter - 零拷贝处理."""
    if auth is None:
        return None
    elif isinstance(auth, tuple) and len(auth) == 2:
        # 直接返回，避免重新构建tuple
        return auth
    elif isinstance(auth, BasicAuth):
        return (auth.username, auth.password)
    elif hasattr(auth, 'username') and hasattr(auth, 'password'):
        return (auth.username, auth.password)
    return None


def _process_headers(headers: Union[Headers, Dict[str, str], None]) -> Optional[Dict[str, str]]:
    """Process headers parameter - 避免不必要的复制."""
    if headers is None:
        return None
    elif isinstance(headers, dict) and not isinstance(headers, Headers):
        # 如果已经是标准字典，直接返回，避免复制
        return headers
    else:
        # 只有Headers类型才需要转换
        return dict(headers)


def _process_cookies(cookies: Union[Cookies, Dict[str, str], None]) -> Optional[Dict[str, str]]:
    """Process cookies parameter - 避免不必要的复制."""
    if cookies is None:
        return None
    elif isinstance(cookies, dict) and not isinstance(cookies, Cookies):
        # 如果已经是标准字典，直接返回，避免复制
        return cookies
    else:
        # 只有Cookies类型才需要转换
        return dict(cookies)


def _process_params(params: Union[QueryParams, Dict[str, str], None]) -> Optional[Dict[str, str]]:
    """Process params parameter - 避免不必要的复制."""
    if params is None:
        return None
    elif isinstance(params, dict) and not isinstance(params, QueryParams):
        # 如果已经是标准字典，直接返回，避免复制
        return params
    else:
        # 只有QueryParams类型才需要转换
        return dict(params)


def _process_timeout(timeout: Union[Timeout, float, None]) -> Optional[float]:
    """Process timeout parameter - 直接传递数值."""
    if isinstance(timeout, Timeout):
        # 使用read timeout，这与httpx行为一致
        return timeout.read or 30.0
    # 对于float或None，直接返回，零开销
    return timeout


def _prepare_files(files: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Prepare files for upload - 最小化处理开销."""
    if files is None:
        return None
    
    # 如果文件已经预处理过，直接返回
    if hasattr(files, '_processed'):
        return files
    
    processed_files = process_files_parameter(files)
    if processed_files:
        return {field_name: file_upload for field_name, file_upload in processed_files.items()}
    return None 