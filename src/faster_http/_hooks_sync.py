"""
Synchronization mechanism for EventHooksProxy.
"""

from collections.abc import Callable
from typing import Any
import weakref


class HooksSyncManager:
    """Manager for synchronizing EventHooksProxy changes with Rust clients."""

    def __init__(self):
        self._clients = weakref.WeakValueDictionary()
        self._update_funcs = {}

    def register_client(self, client_id: str, client, update_func: Callable):
        """Register a client with its update function."""
        self._clients[client_id] = client
        self._update_funcs[client_id] = update_func

    def update_hooks(self, client_id: str, hooks_dict: dict[str, Any]):
        """Update hooks for a client."""
        update_func = self._update_funcs.get(client_id)
        if update_func:
            try:
                update_func(hooks_dict)
            except Exception:
                # Ignore update errors to avoid breaking hook modifications
                pass


# Global instance
_sync_manager = HooksSyncManager()


def register_client(client_id: str, client, update_func: Callable):
    """Register a client globally."""
    _sync_manager.register_client(client_id, client, update_func)


def update_hooks(client_id: str, hooks_dict: dict[str, Any]):
    """Update hooks for a client."""
    _sync_manager.update_hooks(client_id, hooks_dict)


def execute_request_hooks(event_hooks, request):
    """Execute request hooks on Python side to avoid Rust GIL conflicts."""
    if not event_hooks:
        return

    # Get request hooks
    try:
        request_hooks = event_hooks['request']
        if request_hooks:
            for hook in request_hooks:
                if callable(hook):
                    try:
                        hook(request)
                    except Exception as e:
                        # Log the error but don't break the request
                        print(f"Warning: Request hook failed: {e}")
    except (KeyError, TypeError):
        # No request hooks or invalid hooks
        pass


def execute_response_hooks(event_hooks, response):
    """Execute response hooks on Python side to avoid Rust GIL conflicts."""
    if not event_hooks:
        return

    # Get response hooks
    try:
        response_hooks = event_hooks['response']
        if response_hooks:
            for hook in response_hooks:
                if callable(hook):
                    try:
                        hook(response)
                    except Exception as e:
                        # Log the error but don't break the request
                        print(f"Warning: Response hook failed: {e}")
    except (KeyError, TypeError):
        # No response hooks or invalid hooks
        pass
