from eegauge.metadata import metadata_from_eegdash
from eegauge.provenance import SCHEMA, build_provenance, leakage_risk_factors


def test_leakage_flags_multiple_sessions():
    records = [
        {"subject": "sub-01", "session": "01", "run": "1"},
        {"subject": "sub-01", "session": "02", "run": "1"},
    ]
    factors = leakage_risk_factors(records)
    assert any("Multiple sessions" in f for f in factors)


def test_leakage_flags_multiple_runs():
    records = [
        {"subject": "sub-01", "session": "01", "run": "1"},
        {"subject": "sub-01", "session": "01", "run": "2"},
    ]
    factors = leakage_risk_factors(records)
    assert any("Multiple runs" in f for f in factors)


def test_leakage_single_session_still_warns_about_subject_split():
    records = [
        {"subject": "sub-01", "session": "01", "run": "1"},
        {"subject": "sub-02", "session": "01", "run": "1"},
    ]
    factors = leakage_risk_factors(records)
    assert factors and "Subject-wise" in factors[0]


def test_leakage_empty_records_no_factors():
    assert leakage_risk_factors([]) == []


def test_build_provenance_shape():
    records = [
        {"subject": "sub-01", "session": "01", "run": "1"},
        {"subject": "sub-02", "session": "01", "run": "1"},
    ]
    metadata = metadata_from_eegdash(
        "ds002718",
        {"source": "openneuro", "bids_validator_status": "pass", "n_validator_errors": 0},
        records,
    )
    prov = build_provenance(
        backend="eegdash",
        dataset_id="ds002718",
        metadata=metadata,
        records=records,
        filters=None,
        retrieved_at="2026-06-21T00:00:00+00:00",
        versions={"eegauge": "0.3.0", "eegdash": "0.8.2"},
    )

    assert prov["schema"] == SCHEMA
    assert prov["backend"] == "eegdash"
    assert prov["dataset_id"] == "ds002718"
    assert prov["source"] == "openneuro"
    assert prov["selected"]["n_subjects"] == 2
    assert prov["selected"]["n_records"] == 2
    assert prov["selected"]["subjects"] == ["sub-01", "sub-02"]
    assert prov["bids_validation"] == {"status": "pass", "n_errors": 0}
    assert prov["evaluation"] is None
    assert prov["environment"]["eegauge"] == "0.3.0"
