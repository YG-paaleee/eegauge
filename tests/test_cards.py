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
        license="CC-BY-ND-4.0",
        doi="10.3389/fnins.2012.00055",
        citation="Michael Tangermann et al. (2012)",
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
        "chance_level": 0.5,
        "significance": {"test": "binomial", "p_value": 0.003, "above_chance": True},
        "per_class_metrics": [
            {"class": "left_hand", "precision": 0.62, "recall": 0.58, "f1": 0.60, "support": 50},
            {"class": "right_hand", "precision": 0.60, "recall": 0.64, "f1": 0.62, "support": 50},
        ],
        "confusion_matrix": {"labels": ["left_hand", "right_hand"], "matrix": [[29, 21], [18, 32]]},
        "confusion_matrix_path": "results/BNCI2014_001_confusion.png",
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
    # v0.2.0 additions
    assert "Chance level" in card
    assert "yes (binomial p = 0.003)" in card
    assert "10.3389/fnins.2012.00055" in card
    assert "Michael Tangermann et al. (2012)" in card
    assert "## Per-Class Performance" in card
    assert "## Confusion Matrix" in card
    assert "results/BNCI2014_001_confusion.png" in card


def test_render_dataset_card_degrades_when_optional_fields_missing():
    metadata = DatasetMetadata(dataset="BNCI2014_001", paradigm="motor imagery")

    card = render_dataset_card(metadata)

    assert "| DOI | Not available |" in card
    assert "| Citation | Not available |" in card
    # No benchmark block, so no per-class or confusion sections
    assert "## Per-Class Performance" not in card
    assert "## Confusion Matrix" not in card
