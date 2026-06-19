"""MOABB dataset access.

Imports are intentionally lazy so documentation and unit tests do not require
downloading the scientific stack.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from .errors import DependencyMissingError, missing_dependency_message
from .metadata import DatasetMetadata, metadata_from_moabb

SUPPORTED_DATASETS: dict[str, str] = {
    "BNCI2014_001": "BNCI2014_001",
}


def _import_moabb_datasets() -> Any:
    try:
        import moabb.datasets as moabb_datasets
    except ImportError as exc:
        raise DependencyMissingError(missing_dependency_message("moabb")) from exc
    return moabb_datasets


def _import_motor_imagery() -> Any:
    try:
        from moabb.paradigms import MotorImagery
    except ImportError as exc:
        raise DependencyMissingError(missing_dependency_message("moabb")) from exc
    return MotorImagery


def get_dataset(dataset_name: str) -> Any:
    if dataset_name not in SUPPORTED_DATASETS:
        supported = ", ".join(sorted(SUPPORTED_DATASETS))
        raise ValueError(f"Unsupported dataset '{dataset_name}'. Supported datasets: {supported}")

    moabb_datasets = _import_moabb_datasets()
    dataset_class = getattr(moabb_datasets, SUPPORTED_DATASETS[dataset_name])
    return dataset_class()


def scan_dataset(dataset_name: str, *, sample_subject: int | None = None) -> DatasetMetadata:
    dataset = get_dataset(dataset_name)
    sample_info = None

    if sample_subject is not None:
        sample_info = load_sample_info(dataset, sample_subject)

    return metadata_from_moabb(
        dataset_name,
        dataset,
        subjects_used=[sample_subject] if sample_subject is not None else [],
        sample_info=sample_info,
    )


def load_sample_info(dataset: Any, subject: int) -> dict[str, Any]:
    raw = _first_raw(dataset.get_data(subjects=[subject]))
    channel_types = raw.get_channel_types()
    channel_type_counts = dict(Counter(str(channel_type) for channel_type in channel_types))
    eeg_channels = [
        str(channel)
        for channel, channel_type in zip(raw.ch_names, channel_types, strict=False)
        if channel_type == "eeg"
    ]

    return {
        "channels": eeg_channels or [str(channel) for channel in raw.ch_names],
        "channel_type_counts": channel_type_counts,
        "raw_channel_count": int(raw.info.get("nchan", len(raw.ch_names))),
        "sampling_rate_hz": float(raw.info["sfreq"]),
    }


def _first_raw(subject_data: dict[Any, Any]) -> Any:
    for sessions in subject_data.values():
        for runs in sessions.values():
            for raw in runs.values():
                return raw
    raise ValueError("MOABB returned no raw runs for the requested subject.")
