"""Utility functions for faster-http."""
from typing import Any, Dict, Optional, Tuple, Union

from .auth import Auth, BasicAuth
from .models import Headers, Cookies, QueryParams, Timeout
from .files import process_files_parameter


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