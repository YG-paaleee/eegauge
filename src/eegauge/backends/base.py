"""Backend protocol for dataset sources (MOABB, EEGDash)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ..metadata import DatasetMetadata


@runtime_checkable
class DatasetBackend(Protocol):
    """A source of dataset metadata, and where available a record listing.

    Backends are intentionally small: ``get_dataset_metadata`` returns a
    normalized :class:`~eegauge.metadata.DatasetMetadata`, and ``list_records``
    returns lightweight per-recording dicts (subject/session/task/run) used for
    cohort provenance and leakage-risk hints. Neither method downloads signals.
    """

    name: str

    def get_dataset_metadata(self, dataset_id: str, **options: Any) -> DatasetMetadata: ...

    def list_records(
        self, dataset_id: str, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]: ...
