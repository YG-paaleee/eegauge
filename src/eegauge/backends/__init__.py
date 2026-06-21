"""Dataset source backends.

Each backend implements :class:`~eegauge.backends.base.DatasetBackend`. Imports
of the concrete backends are lazy so that selecting one backend never pulls in the
other's heavy optional dependencies.
"""

from __future__ import annotations

from .base import DatasetBackend

BACKENDS = ("moabb", "eegdash")


def get_backend(name: str) -> DatasetBackend:
    """Return a backend instance by name (lazy import)."""
    if name == "moabb":
        from .moabb import MoabbBackend

        return MoabbBackend()
    if name == "eegdash":
        from .eegdash import EegdashBackend

        return EegdashBackend()
    supported = ", ".join(BACKENDS)
    raise ValueError(f"Unsupported backend '{name}'. Supported backends: {supported}")


__all__ = ["BACKENDS", "DatasetBackend", "get_backend"]
