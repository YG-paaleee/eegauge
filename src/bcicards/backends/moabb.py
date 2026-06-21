"""MOABB-backed dataset source.

A thin wrapper over the existing :mod:`bcicards.datasets` logic so behavior is
unchanged; it just exposes that logic through the :class:`DatasetBackend` protocol.
"""

from __future__ import annotations

from typing import Any

from ..datasets import scan_dataset
from ..metadata import DatasetMetadata


class MoabbBackend:
    name = "moabb"

    def get_dataset_metadata(
        self, dataset_id: str, *, sample_subject: int | None = None, **_: Any
    ) -> DatasetMetadata:
        return scan_dataset(dataset_id, sample_subject=sample_subject)

    def list_records(
        self, dataset_id: str, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        # MOABB does not expose a BIDS-style record listing at metadata time.
        return []
