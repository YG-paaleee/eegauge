import pytest

from eegauge.backends import BACKENDS, get_backend
from eegauge.backends.eegdash import EegdashBackend, _normalize_record
from eegauge.backends.moabb import MoabbBackend


class FakeEegdashClient:
    """Stand-in for the EEGDash query client (no network, no eegdash install)."""

    def __init__(self, dataset, records):
        self._dataset = dataset
        self._records = records
        self.queries = []

    def get_dataset(self, dataset_id):
        return self._dataset

    def find(self, query):
        self.queries.append(query)
        return self._records


def _sample_client():
    dataset = {
        "recording_modality": ["eeg"],
        "source": "openneuro",
        "senior_author": "A. Researcher",
        "publication_year": 2024,
        "license": "CC0",
        "bids_validator_status": "pass",
        "n_validator_errors": 0,
    }
    records = [
        {"entities": {"subject": "sub-01", "session": "01", "task": "rest", "run": "1"}},
        {"entities": {"subject": "sub-02", "session": "01", "task": "rest", "run": "1"}},
    ]
    return FakeEegdashClient(dataset, records)


def test_get_backend_dispatch():
    assert isinstance(get_backend("moabb"), MoabbBackend)
    assert isinstance(get_backend("eegdash"), EegdashBackend)
    assert set(BACKENDS) == {"moabb", "eegdash"}


def test_get_backend_rejects_unknown():
    with pytest.raises(ValueError, match="Unsupported backend"):
        get_backend("nope")


def test_moabb_backend_has_no_record_listing():
    assert MoabbBackend().list_records("BNCI2014_001") == []


def test_normalize_record_extracts_entities():
    record = {
        "entities": {"subject": "sub-03", "session": "02", "task": "oddball", "run": "2"},
        "recording_modality": ["eeg"],
    }
    norm = _normalize_record(record)
    assert norm == {
        "subject": "sub-03",
        "session": "02",
        "task": "oddball",
        "run": "2",
        "modality": ["eeg"],
    }


def test_normalize_record_accepts_flat_entities():
    # Some records may carry BIDS entities at the top level rather than nested.
    record = {"subject": "012", "session": "01", "task": "rest", "run": "1"}
    norm = _normalize_record(record)
    assert norm["subject"] == "012"
    assert norm["session"] == "01"
    assert norm["task"] == "rest"


def test_eegdash_backend_builds_metadata_from_injected_client():
    backend = EegdashBackend(client=_sample_client())
    metadata = backend.get_dataset_metadata("ds002718")

    assert metadata.dataset == "ds002718"
    assert metadata.modalities == ["eeg"]
    assert metadata.n_subjects == 2
    assert metadata.n_records == 2
    assert metadata.source_archive == "openneuro"
    assert metadata.license == "CC0"
    assert metadata.bids_status == "pass"
    assert metadata.citation == "A. Researcher et al. (2024)"


def test_eegdash_backend_reads_real_field_names():
    # EEGDash get_dataset uses dataset_doi (with a "doi:" prefix) and author_year,
    # and records carry entities flat at the top level.
    dataset = {
        "recording_modality": ["eeg"],
        "source": "openneuro",
        "license": "CC0",
        "dataset_doi": "doi:10.18112/openneuro.ds002718.v1.1.0",
        "author_year": "Wakeman2020",
    }
    records = [{"subject": "002", "task": "FaceRecognition"}]
    backend = EegdashBackend(client=FakeEegdashClient(dataset, records))
    metadata = backend.get_dataset_metadata("ds002718")

    assert metadata.doi == "10.18112/openneuro.ds002718.v1.1.0"
    assert metadata.citation == "Wakeman2020"
    assert metadata.license == "CC0"
    assert metadata.n_subjects == 1
    assert metadata.paradigm == "FaceRecognition"


def test_eegdash_backend_caches_records():
    client = _sample_client()
    backend = EegdashBackend(client=client)
    backend.get_dataset_metadata("ds002718")  # triggers one find()
    backend.list_records("ds002718")  # should hit cache, not call find() again
    assert len(client.queries) == 1
