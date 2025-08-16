"""
Client registry for managing EventHooksProxy synchronization.
"""

from typing import Any
import weakref


class ClientRegistry:
    """Global registry for managing client references for EventHooksProxy sync."""

    def __init__(self):
        self._clients: dict[str, Any] = {}
        self._weak_clients = weakref.WeakValueDictionary()

    def register_client(self, client_id: str, client):
        """Register a client for EventHooksProxy synchronization."""
        self._clients[client_id] = client
        self._weak_clients[client_id] = client

    def get_client(self, client_id: str):
        """Get a client by ID."""
        return self._clients.get(client_id) or self._weak_clients.get(client_id)

    def unregister_client(self, client_id: str):
        """Unregister a client."""
        self._clients.pop(client_id, None)
        # WeakValueDictionary will clean itself automatically


# Global instance
_registry = ClientRegistry()


def register_client(client_id: str, client):
    """Register a client globally."""
    _registry.register_client(client_id, client)


def get_client(client_id: str):
    """Get a client by ID."""
    return _registry.get_client(client_id)


def unregister_client(client_id: str):
    """Unregister a client."""
    _registry.unregister_client(client_id)
