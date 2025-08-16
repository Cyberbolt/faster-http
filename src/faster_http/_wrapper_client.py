"""
Python wrapper client that handles Event Hooks in Python layer.

This wrapper completely avoids Rust-to-Python calls for Event Hooks,
preventing GIL deadlocks while maintaining httpx compatibility.
"""

from typing import Any, Dict, List, Optional, Union, Callable
import uuid
from ._core import HttpClient as RustHttpClient
from ._hooks_sync import execute_request_hooks, execute_response_hooks
from .event_hooks_proxy import EventHooksProxy


class Client:
    """
    Python wrapper for Rust HttpClient that handles Event Hooks in Python layer.
    
    This wrapper ensures Event Hooks are executed entirely in Python,
    avoiding Rust-to-Python GIL conflicts that cause deadlocks.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[Union[float, Dict[str, float]]] = None,
        headers: Optional[Dict[str, str]] = None,
        verify: Optional[bool] = None,
        follow_redirects: Optional[bool] = None,
        auth: Optional[Any] = None,
        proxy: Optional[Any] = None,
        proxies: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        http1: Optional[bool] = None,
        http2: Optional[bool] = None,
        event_hooks: Optional[Dict[str, List[Callable]]] = None,
        cert: Optional[Any] = None,
        trust_env: Optional[bool] = None,
        transport: Optional[Any] = None,
        mounts: Optional[Dict[str, Any]] = None,
        limits: Optional[Any] = None,
        max_redirects: Optional[int] = None,
        default_encoding: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
    ):
        # Store event hooks in Python layer
        self._event_hooks = {}
        if event_hooks:
            self._event_hooks.update(event_hooks)
        
        # Ensure hooks are lists
        self._event_hooks.setdefault("request", [])
        self._event_hooks.setdefault("response", [])
        
        # Create unique client ID for event hooks proxy
        self._client_id = str(uuid.uuid4())
        
        # Create the underlying Rust client WITHOUT event hooks
        # (passing None for event_hooks to avoid Rust-side hook handling)
        self._rust_client = RustHttpClient(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            verify=verify,
            follow_redirects=follow_redirects,
            auth=auth,
            proxy=proxy,
            proxies=proxies,
            cookies=cookies,
            http1=http1,
            http2=http2,
            event_hooks=None,  # IMPORTANT: No event hooks in Rust layer
            cert=cert,
            trust_env=trust_env,
            transport=transport,
            mounts=mounts,
            limits=limits,
            max_redirects=max_redirects,
            default_encoding=default_encoding,
            params=params,
        )
    
    @property
    def event_hooks(self) -> Dict[str, List[Callable]]:
        """
        Access to event hooks that can be modified at runtime.
        Returns the actual hooks dict for direct modification.
        """
        return self._event_hooks
    
    def _execute_hooks(self, hook_type: str, context_obj: Any) -> None:
        """Execute hooks of the specified type with the given context object."""
        hooks = self._event_hooks.get(hook_type, [])
        if hooks:
            if hook_type == "request":
                execute_request_hooks(self._event_hooks, context_obj)
            elif hook_type == "response":
                execute_response_hooks(self._event_hooks, context_obj)
    
    def request(
        self,
        method: str,
        url: str,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        auth: Optional[tuple] = None,
        follow_redirects: Optional[bool] = None,
        cookies: Optional[Dict[str, str]] = None,
    ):
        """
        Send HTTP request with Event Hooks handled in Python layer.
        
        This method:
        1. Executes request hooks in Python
        2. Calls Rust for pure HTTP request (no Python callbacks)
        3. Executes response hooks in Python
        4. Returns the response
        """
        # Build request object for hooks
        request_obj = self._rust_client.build_request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            content=content,
            data=data,
            files=files,
            json=json,
            stream=False,
        )
        
        # Execute request hooks in Python layer
        self._execute_hooks("request", request_obj)
        
        # Execute the actual HTTP request in Rust (no Python callbacks)
        response = self._rust_client.request(
            method=method,
            url=url,
            content=content,
            data=data,
            json=json,
            files=files,
            params=params,
            headers=headers,
            timeout=timeout,
            auth=auth,
            follow_redirects=follow_redirects,
            cookies=cookies,
        )
        
        # Execute response hooks in Python layer
        self._execute_hooks("response", response)
        
        return response
    
    def get(self, url: str, **kwargs):
        """Send GET request."""
        return self.request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs):
        """Send POST request."""
        return self.request("POST", url, **kwargs)
    
    def put(self, url: str, **kwargs):
        """Send PUT request."""
        return self.request("PUT", url, **kwargs)
    
    def patch(self, url: str, **kwargs):
        """Send PATCH request."""
        return self.request("PATCH", url, **kwargs)
    
    def delete(self, url: str, **kwargs):
        """Send DELETE request."""
        return self.request("DELETE", url, **kwargs)
    
    def head(self, url: str, **kwargs):
        """Send HEAD request."""
        return self.request("HEAD", url, **kwargs)
    
    def options(self, url: str, **kwargs):
        """Send OPTIONS request."""
        return self.request("OPTIONS", url, **kwargs)
    
    def stream(self, method: str, url: str, **kwargs):
        """Send streaming request."""
        return self._rust_client.stream(method, url, **kwargs)
    
    def close(self):
        """Close the client."""
        return self._rust_client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
    
    # Expose Rust client attributes for httpx compatibility
    @property
    def base_url(self):
        """Get base URL."""
        return self._rust_client.base_url
    
    @property
    def headers(self):
        """Get default headers."""
        return self._rust_client.headers
    
    @property
    def cookies(self):
        """Get default cookies."""
        return self._rust_client.cookies
    
    @property
    def params(self):
        """Get default params."""
        return self._rust_client.params
    
    @property
    def auth(self):
        """Get authentication."""
        return self._rust_client.auth