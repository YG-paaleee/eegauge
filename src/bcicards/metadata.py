"""Metadata extraction for public BCI datasets."""

from __future__ import annotations

from collections.abc import Mapping
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
    doi: str | None = None
    citation: str | None = None
    # Optional fields used by non-MOABB backends (e.g. EEGDash). Default to
    # empty/None so MOABB cards are unchanged.
    modalities: list[str] = field(default_factory=list)
    source_archive: str | None = None
    bids_status: str | None = None
    bids_n_errors: int | None = None
    n_records: int | None = None
    n_subjects: int | None = None
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

    documentation = _moabb_documentation(dataset)

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
        license=_extract_license(dataset, documentation),
        doi=_extract_doi(dataset, documentation),
        citation=_build_citation(documentation),
        notes=notes,
    )


def _moabb_documentation(dataset: Any) -> Any:
    """Return MOABB's own ``METADATA.documentation`` block if present, else None.

    MOABB recently started attaching a structured ``METADATA`` class attribute to
    datasets. Not every dataset populates it, so all access stays defensive.
    """

    metadata = getattr(dataset, "METADATA", None)
    return getattr(metadata, "documentation", None)


def _extract_doi(dataset: Any, documentation: Any) -> str | None:
    doi = getattr(dataset, "doi", None) or getattr(documentation, "doi", None)
    return str(doi) if doi else None


def _extract_license(dataset: Any, documentation: Any) -> str | None:
    license_value = getattr(dataset, "license", None) or getattr(documentation, "license", None)
    return str(license_value) if license_value else None


def _build_citation(documentation: Any) -> str | None:
    if documentation is None:
        return None
    author = getattr(documentation, "senior_author", None)
    if not author:
        investigators = getattr(documentation, "investigators", None) or []
        author = investigators[0] if investigators else None
    year = getattr(documentation, "publication_year", None)
    if author and year:
        return f"{author} et al. ({year})"
    return str(author) if author else None


def _sessions_per_subject(records: list[dict[str, Any]]) -> int | None:
    per_subject: dict[str, set[Any]] = {}
    for record in records:
        subject = record.get("subject")
        if not subject:
            continue
        per_subject.setdefault(subject, set())
        if record.get("session"):
            per_subject[subject].add(record["session"])
    counts = {len(sessions) for sessions in per_subject.values() if sessions}
    return counts.pop() if len(counts) == 1 else None


def metadata_from_eegdash(
    dataset_id: str,
    raw: Mapping[str, Any],
    records: list[dict[str, Any]],
) -> DatasetMetadata:
    """Build metadata from EEGDash dataset metadata + a record listing (no signals).

    EEGDash is multi-modality, so signal-dependent fields (channels, sampling
    rate, class labels) are intentionally left empty here.
    """

    modalities = raw.get("recording_modality") or []
    if isinstance(modalities, str):
        modalities = [modalities]
    modalities = [str(modality) for modality in modalities]

    subjects = {record["subject"] for record in records if record.get("subject")}
    tasks = sorted({record["task"] for record in records if record.get("task")})

    senior = raw.get("senior_author")
    year = raw.get("publication_year")
    if senior and year:
        citation = f"{senior} et al. ({year})"
    elif senior:
        citation = str(senior)
    else:
        citation = None

    return DatasetMetadata(
        dataset=dataset_id,
        paradigm=", ".join(tasks) if tasks else "not specified",
        source=f"EEGDash dataset: {dataset_id}",
        license=str(raw["license"]) if raw.get("license") else None,
        doi=str(raw["doi"]) if raw.get("doi") else None,
        citation=citation,
        sessions_per_subject=_sessions_per_subject(records),
        modalities=modalities,
        source_archive=str(raw["source"]) if raw.get("source") else None,
        bids_status=(
            str(raw["bids_validator_status"]) if raw.get("bids_validator_status") else None
        ),
        bids_n_errors=(
            int(raw["n_validator_errors"]) if raw.get("n_validator_errors") is not None else None
        ),
        n_records=len(records),
        n_subjects=len(subjects),
        notes=[
            "Channel names, sampling rate, and class labels require loading signals "
            "(not done during scan)."
        ],
    )
