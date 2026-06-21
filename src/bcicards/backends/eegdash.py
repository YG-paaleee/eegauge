"""EEGDash-backed dataset source (metadata only, no signal download).

Uses the EEGDash query client to read dataset-level metadata and to list a
dataset's recordings (subject/session/task/run) without fetching signals. The
import is lazy so the optional ``eegdash`` dependency is only required when this
backend is actually used.
"""

from __future__ import annotations

from typing import Any

from ..errors import DependencyMissingError, missing_dependency_message
from ..metadata import DatasetMetadata, metadata_from_eegdash


def _import_eegdash() -> Any:
    try:
        from eegdash import EEGDash
    except ImportError as exc:
        raise DependencyMissingError(
            missing_dependency_message("eegdash", extra="eegdash")
        ) from exc
    return EEGDash


def _normalize_record(record: Any) -> dict[str, Any]:
    """Reduce a raw EEGDash record to the fields we need (defensive)."""
    if hasattr(record, "model_dump"):
        record = record.model_dump()
    elif not isinstance(record, dict):
        record = dict(record)

    entities = record.get("entities") or {}
    if hasattr(entities, "model_dump"):
        entities = entities.model_dump()
    elif not isinstance(entities, dict):
        entities = dict(entities) if entities else {}

    def pick(field: str) -> Any:
        # EEGDash records may carry BIDS entities nested under "entities" or
        # flattened at the top level; accept either.
        return entities.get(field) or record.get(field)

    return {
        "subject": pick("subject"),
        "session": pick("session"),
        "task": pick("task"),
        "run": pick("run"),
        "modality": record.get("recording_modality") or record.get("datatype"),
    }


class EegdashBackend:
    name = "eegdash"

    def __init__(self, client: Any | None = None) -> None:
        # ``client`` may be injected (used by tests) to avoid importing eegdash.
        self._client = client
        self._records_cache: dict[tuple[Any, ...], list[dict[str, Any]]] = {}

    def _get_client(self) -> Any:
        if self._client is None:
            eeg_dash = _import_eegdash()
            self._client = eeg_dash()
        return self._client

    def list_records(
        self, dataset_id: str, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        key = (dataset_id, tuple(sorted((filters or {}).items())))
        if key in self._records_cache:
            return self._records_cache[key]
        client = self._get_client()
        query = {"dataset": dataset_id, **(filters or {})}
        raw_records = client.find(query) or []
        records = [_normalize_record(record) for record in raw_records]
        self._records_cache[key] = records
        return records

    def get_dataset_metadata(self, dataset_id: str, **_: Any) -> DatasetMetadata:
        client = self._get_client()
        raw = client.get_dataset(dataset_id) or {}
        records = self.list_records(dataset_id)
        return metadata_from_eegdash(dataset_id, raw, records)
