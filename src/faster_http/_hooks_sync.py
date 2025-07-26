"""
Synchronization mechanism for EventHooksProxy.
"""

import weakref
from typing import Dict, Any, Callable

class HooksSyncManager:
    """Manager for synchronizing EventHooksProxy changes with Rust clients."""
    
    def __init__(self):
        self._clients = weakref.WeakValueDictionary()
        self._update_funcs = {}
    
    def register_client(self, client_id: str, client, update_func: Callable):
        """Register a client with its update function."""
        self._clients[client_id] = client
        self._update_funcs[client_id] = update_func
    
    def update_hooks(self, client_id: str, hooks_dict: Dict[str, Any]):
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

def update_hooks(client_id: str, hooks_dict: Dict[str, Any]):
    """Update hooks for a client."""
    _sync_manager.update_hooks(client_id, hooks_dict)