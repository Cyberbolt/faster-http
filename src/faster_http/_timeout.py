"""
Timeout configuration wrapper to provide httpx-compatible interface.
"""

from . import _core

# Sentinel object to distinguish "not provided" from None
_UNSET = object()


class Timeout:
    """
    Timeout configuration for HTTP requests.

    Compatible with httpx.Timeout interface.
    """

    def __init__(
        self,
        timeout=_UNSET,  # Sentinel: _UNSET means "not provided"
        *,
        connect=_UNSET,  # Sentinel: _UNSET means "not provided"
        read=_UNSET,  # Sentinel: _UNSET means "not provided"
        write=_UNSET,  # Sentinel: _UNSET means "not provided"
        pool=_UNSET,  # Sentinel: _UNSET means "not provided"
    ):
        """
        Initialize timeout configuration.

        Args:
            timeout: Default timeout for all operations, or None for infinite timeout
            connect: Connection timeout in seconds
            read: Read timeout in seconds
            write: Write timeout in seconds
            pool: Pool timeout in seconds
        """

        # Convert parameters for Rust side
        timeout_val = (float("nan") if timeout is None else float(timeout)) if timeout is not _UNSET else -1.0

        connect_val = -1.0 if connect is _UNSET else (float("nan") if connect is None else float(connect))
        read_val = -1.0 if read is _UNSET else (float("nan") if read is None else float(read))
        write_val = -1.0 if write is _UNSET else (float("nan") if write is None else float(write))
        pool_val = -1.0 if pool is _UNSET else (float("nan") if pool is None else float(pool))

        self._inner = _core.Timeout(
            timeout=timeout_val, connect=connect_val, read=read_val, write=write_val, pool=pool_val
        )

    @property
    def connect(self) -> float | None:
        """Connect timeout in seconds."""
        return self._inner.connect

    @property
    def read(self) -> float | None:
        """Read timeout in seconds."""
        return self._inner.read

    @property
    def write(self) -> float | None:
        """Write timeout in seconds."""
        return self._inner.write

    @property
    def pool(self) -> float | None:
        """Pool timeout in seconds."""
        return self._inner.pool

    def __repr__(self) -> str:
        """String representation matching httpx format."""
        return self._inner.__repr__()

    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if isinstance(other, Timeout):
            return self._inner.__eq__(other._inner)
        return False
