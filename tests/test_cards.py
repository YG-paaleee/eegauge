from bcicards.cards import render_dataset_card
from bcicards.metadata import DatasetMetadata


def test_render_dataset_card_includes_limits_and_no_medical_claims():
    metadata = DatasetMetadata(
        dataset="BNCI2014_001",
        paradigm="motor imagery",
        subjects_used=[1, 2],
        available_subjects=[1, 2, 3],
        classes=["left_hand", "right_hand"],
        channels=["C3", "C4"],
        channel_type_counts={"eeg": 2, "eog": 1, "stim": 1},
        sampling_rate_hz=250,
        source="MOABB dataset code: BNCI2014-001",
    )
    result = {
        "baseline": "CSP + LDA",
        "pipeline": "CSP + LDA",
        "split_method": "leave-one-subject-out",
        "subjects": [1, 2],
        "n_trials": 100,
        "seed": 42,
        "runtime_seconds": 1.25,
        "metrics": {"accuracy": 0.61, "balanced_accuracy": 0.604},
        "warnings": ["Metrics are dataset-specific."],
    }

    card = render_dataset_card(metadata, result)

    assert "# Dataset Card: BNCI2014_001" in card
    assert "leave-one-subject-out" in card
    assert "C3, C4" in card
    assert "eeg: 2" in card
    assert "250 Hz" in card
    assert "0.610" in card
    assert "This project is not medical software" in card
    assert "does not prove real-world BCI reliability" in card
    assert "diagnosis ability" in card
