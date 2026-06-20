"""Markdown card rendering."""

from __future__ import annotations

from typing import Any

from .metadata import DatasetMetadata


def render_dataset_card(
    metadata: DatasetMetadata | dict[str, Any],
    benchmark: dict[str, Any] | None = None,
) -> str:
    meta = metadata.to_dict() if isinstance(metadata, DatasetMetadata) else dict(metadata)
    benchmark = benchmark or {}
    metrics = benchmark.get("metrics", {})

    lines = [
        f"# Dataset Card: {meta.get('dataset', 'unknown')}",
        "",
        "## Summary",
        "",
        (
            "This card describes a public EEG/BCI dataset and, when available, "
            "a small reproducible baseline. It is intended for learning, inspection, "
            "and benchmark hygiene."
        ),
        "",
        "## Dataset Metadata",
        "",
        "| Field | Value |",
        "| --- | --- |",
        _row("Dataset", meta.get("dataset")),
        _row("Paradigm", meta.get("paradigm")),
        _row("Subjects used", _join(meta.get("subjects_used"))),
        _row(
            "Available subjects",
            meta.get("n_available_subjects") or _join(meta.get("available_subjects")),
        ),
        _row("Classes", _join(meta.get("classes"))),
        _row("Channels", meta.get("n_channels") or _join(meta.get("channels"))),
        _row("EEG channel names", _join(meta.get("channels"))),
        _row("Raw channel types", _format_counts(meta.get("channel_type_counts"))),
        _row("Sampling rate", _format_sampling_rate(meta.get("sampling_rate_hz"))),
        _row("Sessions per subject", meta.get("sessions_per_subject")),
        _row("Source", meta.get("source")),
        _row("License", meta.get("license")),
        _row("DOI", meta.get("doi")),
        _row("Citation", meta.get("citation")),
        "",
    ]

    if benchmark:
        lines.extend(
            [
                "## Benchmark",
                "",
                "| Metric | Value |",
                "| --- | --- |",
                _row("Baseline", benchmark.get("baseline")),
                _row("Split method", benchmark.get("split_method")),
                _row("Accuracy", _format_metric(metrics.get("accuracy"))),
                _row("Balanced accuracy", _format_metric(metrics.get("balanced_accuracy"))),
                _row("Chance level", _format_metric(benchmark.get("chance_level"))),
                _row("Above chance?", _format_significance(benchmark.get("significance"))),
                _row("Subjects", _join(benchmark.get("subjects"))),
                _row("Trials", benchmark.get("n_trials")),
                _row("Seed", benchmark.get("seed")),
                _row("Runtime", _format_seconds(benchmark.get("runtime_seconds"))),
                _row("Plot", benchmark.get("plot_path")),
                "",
            ]
        )

        per_class = benchmark.get("per_class_metrics") or []
        if per_class:
            lines.extend(
                [
                    "## Per-Class Performance",
                    "",
                    "| Class | Precision | Recall | F1 | Support |",
                    "| --- | --- | --- | --- | --- |",
                    *[_per_class_row(item) for item in per_class],
                    "",
                ]
            )

        confusion_path = benchmark.get("confusion_matrix_path")
        if confusion_path:
            lines.extend(
                [
                    "## Confusion Matrix",
                    "",
                    f"![Confusion matrix]({confusion_path})",
                    "",
                ]
            )

    lines.extend(
        [
            "## What This Result Means",
            "",
            (
                "This output is a reproducible baseline for a specific public dataset, "
                "subject list, split method, and preprocessing path."
            ),
            "",
            "## What This Result Does Not Prove",
            "",
            (
                "This does not prove real-world BCI reliability, medical usefulness, "
                "diagnosis ability, treatment ability, emotion detection ability, or "
                "performance on people outside the dataset."
            ),
            "",
            "## Leakage And Limitations",
            "",
            (
                "- Subject-aware testing is stronger than random trial-level "
                "splitting across subjects."
            ),
            "- EEG datasets can contain subject, session, hardware, and preprocessing artifacts.",
            "- A high score on one dataset does not imply a deployable BCI system.",
            "- This project is not medical software.",
        ]
    )

    notes = meta.get("notes") or []
    warnings = benchmark.get("warnings") or []
    if notes or warnings:
        lines.extend(["", "## Notes And Warnings", ""])
        lines.extend(f"- {item}" for item in [*notes, *warnings])

    return "\n".join(lines)


def _row(label: str, value: Any) -> str:
    return f"| {label} | {_display(value)} |"


def _display(value: Any) -> str:
    if value is None or value == "":
        return "Not available"
    return str(value).replace("\n", " ")


def _join(values: Any) -> str:
    if not values:
        return "Not available"
    if isinstance(values, str):
        return values
    return ", ".join(str(value) for value in values)


def _format_metric(value: Any) -> str:
    if value is None:
        return "Not available"
    return f"{float(value):.3f}"


def _format_significance(value: Any) -> str:
    if not value:
        return "Not available"
    verdict = "yes" if value.get("above_chance") else "no"
    p_value = value.get("p_value")
    if p_value is None:
        return verdict
    return f"{verdict} (binomial p = {float(p_value):.3g})"


def _per_class_row(item: dict[str, Any]) -> str:
    return (
        f"| {_display(item.get('class'))} "
        f"| {_format_metric(item.get('precision'))} "
        f"| {_format_metric(item.get('recall'))} "
        f"| {_format_metric(item.get('f1'))} "
        f"| {_display(item.get('support'))} |"
    )


def _format_seconds(value: Any) -> str:
    if value is None:
        return "Not available"
    return f"{float(value):.3f} seconds"


def _format_sampling_rate(value: Any) -> str:
    if value is None:
        return "Not available"
    return f"{float(value):g} Hz"


def _format_counts(value: Any) -> str:
    if not value:
        return "Not available"
    return ", ".join(f"{key}: {value[key]}" for key in sorted(value))
