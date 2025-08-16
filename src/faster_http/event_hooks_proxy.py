"""
Event hooks proxy that allows modification of client event hooks.
"""

from collections.abc import Callable


class EventHooksProxy(dict):
    """
    A dict-like proxy that synchronizes with the client's internal event hooks.
    This matches httpx's behavior where client.event_hooks can be modified after creation.
    """

    def __init__(self, client_id: str, current_hooks: dict[str, list[Callable]] | None = None):
        super().__init__()
        self._client_id = client_id
        # Initialize with current hooks or empty
        if current_hooks:
            self.update(current_hooks)
        else:
            self["request"] = []
            self["response"] = []

    def __setitem__(self, key: str, value: list[Callable]) -> None:
        # Update the local dict
        super().__setitem__(key, list(value) if value else [])
        # Sync changes to the Rust side
        self._sync_to_rust()

    def __delitem__(self, key: str) -> None:
        # Set to empty list rather than deleting
        super().__setitem__(key, [])
        # Sync changes to the Rust side
        self._sync_to_rust()

    def _sync_to_rust(self) -> None:
        """Synchronize current hooks to the Rust client"""
        try:
            from ._hooks_sync import update_hooks

            update_hooks(self._client_id, dict(self))
        except Exception:
            # Ignore sync errors to avoid breaking hook modifications
            pass
