import json

import pytest

import eegauge
from eegauge import cli
from eegauge.cli import build_parser
from eegauge.metadata import metadata_from_eegdash


def test_version_matches_package(capsys):
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])

    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert out.strip() == f"eegauge {eegauge.__version__}"


def test_top_level_help_smoke():
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])

    assert exc.value.code == 0


def test_benchmark_requires_subjects():
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["benchmark", "--dataset", "BNCI2014_001"])

    assert exc.value.code == 2


def test_scan_eegdash_writes_card_and_provenance(monkeypatch, tmp_path):
    records = [
        {"subject": "sub-01", "session": "01", "task": "rest", "run": "1"},
        {"subject": "sub-01", "session": "02", "task": "rest", "run": "1"},
    ]
    raw = {
        "recording_modality": ["eeg"],
        "source": "openneuro",
        "bids_validator_status": "pass",
        "n_validator_errors": 0,
    }

    class FakeBackend:
        name = "eegdash"

        def get_dataset_metadata(self, dataset_id, **_):
            return metadata_from_eegdash(dataset_id, raw, records)

        def list_records(self, dataset_id, filters=None):
            return records

    monkeypatch.setattr(cli, "get_backend", lambda name: FakeBackend())

    args = build_parser().parse_args(
        [
            "scan",
            "--dataset",
            "ds002718",
            "--backend",
            "eegdash",
            "--cards-dir",
            str(tmp_path / "cards"),
            "--results-dir",
            str(tmp_path / "res"),
        ]
    )
    assert args.func(args) == 0

    card = (tmp_path / "cards" / "ds002718.md").read_text(encoding="utf-8")
    assert "ds002718" in card

    prov_path = tmp_path / "res" / "ds002718.provenance.json"
    assert prov_path.exists()
    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    assert prov["schema"] == "bci-evaluation-card/0.1"
    assert prov["selected"]["n_subjects"] == 1
    assert any("Multiple sessions" in factor for factor in prov["leakage_risk_factors"])
