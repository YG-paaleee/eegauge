"""Metadata extraction for public BCI datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class DatasetMetadata:
    dataset: str
    paradigm: str
    subjects_used: list[int] = field(default_factory=list)
    available_subjects: list[int] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    channels: list[str] = field(default_factory=list)
    channel_type_counts: dict[str, int] = field(default_factory=dict)
    sampling_rate_hz: float | None = None
    sessions_per_subject: int | None = None
    interval_seconds: list[float] = field(default_factory=list)
    source: str | None = None
    license: str | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def n_channels(self) -> int | None:
        return len(self.channels) if self.channels else None

    @property
    def n_available_subjects(self) -> int:
        return len(self.available_subjects)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["n_channels"] = self.n_channels
        payload["n_available_subjects"] = self.n_available_subjects
        return payload


def metadata_from_moabb(
    dataset_name: str,
    dataset: Any,
    *,
    subjects_used: list[int] | None = None,
    sample_info: dict[str, Any] | None = None,
) -> DatasetMetadata:
    """Build conservative metadata from a MOABB dataset object."""

    event_id = getattr(dataset, "event_id", {}) or {}
    classes = sorted(str(label) for label in event_id)
    subject_list = [int(subject) for subject in getattr(dataset, "subject_list", []) or []]
    interval = getattr(dataset, "interval", None) or []
    sessions = getattr(dataset, "sessions_per_subject", None)
    code = getattr(dataset, "code", dataset_name)

    channels = []
    sampling_rate = None
    notes = []
    if sample_info:
        channels = [str(channel) for channel in sample_info.get("channels", [])]
        sampling_rate = sample_info.get("sampling_rate_hz")
        channel_type_counts = {
            str(channel_type): int(count)
            for channel_type, count in (sample_info.get("channel_type_counts") or {}).items()
        }
        raw_channel_count = sample_info.get("raw_channel_count")
        if raw_channel_count and channels and int(raw_channel_count) != len(channels):
            notes.append(
                f"Raw files expose {raw_channel_count} channels; this card lists "
                f"{len(channels)} EEG channels used for motor-imagery analysis."
            )
    else:
        channel_type_counts = {}
        notes.append("Channel names and sampling rate require loading a sample through MOABB/MNE.")

    return DatasetMetadata(
        dataset=dataset_name,
        paradigm="motor imagery",
        subjects_used=subjects_used or [],
        available_subjects=subject_list,
        classes=classes,
        channels=channels,
        channel_type_counts=channel_type_counts,
        sampling_rate_hz=sampling_rate,
        sessions_per_subject=int(sessions) if sessions is not None else None,
        interval_seconds=[float(value) for value in interval],
        source=f"MOABB dataset code: {code}",
        license=getattr(dataset, "license", None),
        notes=notes,
    )
