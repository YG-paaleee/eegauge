"""Simple baseline benchmarks for public BCI datasets."""

from __future__ import annotations

import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from .datasets import get_dataset, load_sample_info
from .errors import DependencyMissingError, missing_dependency_message
from .io import ensure_dir, safe_name
from .metadata import DatasetMetadata, metadata_from_moabb


def _import_scientific_stack() -> dict[str, Any]:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from mne.decoding import CSP
        from moabb.paradigms import MotorImagery
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.metrics import accuracy_score, balanced_accuracy_score
        from sklearn.model_selection import LeaveOneGroupOut, StratifiedShuffleSplit
        from sklearn.pipeline import make_pipeline
    except ImportError as exc:
        package = getattr(exc, "name", "scientific stack")
        raise DependencyMissingError(missing_dependency_message(package)) from exc

    return {
        "plt": plt,
        "np": np,
        "CSP": CSP,
        "MotorImagery": MotorImagery,
        "LinearDiscriminantAnalysis": LinearDiscriminantAnalysis,
        "accuracy_score": accuracy_score,
        "balanced_accuracy_score": balanced_accuracy_score,
        "LeaveOneGroupOut": LeaveOneGroupOut,
        "StratifiedShuffleSplit": StratifiedShuffleSplit,
        "make_pipeline": make_pipeline,
    }


def run_benchmark(
    dataset_name: str,
    subjects: list[int],
    *,
    seed: int = 42,
    plot_dir: Path | str = "results",
) -> tuple[dict[str, Any], DatasetMetadata]:
    """Run a small CSP + LDA benchmark and return serializable results."""

    if not subjects:
        raise ValueError("At least one subject is required.")

    stack = _import_scientific_stack()
    np = stack["np"]

    started = time.perf_counter()
    dataset = get_dataset(dataset_name)
    paradigm = stack["MotorImagery"]()
    x_data, labels, frame = paradigm.get_data(dataset=dataset, subjects=subjects)
    label_array = np.asarray(labels)

    groups = _subject_groups(frame, fallback_subjects=subjects, n_trials=len(label_array))
    class_count = len(set(label_array))
    n_components = max(2, min(4, int(x_data.shape[1]), class_count * 2))

    pipeline = stack["make_pipeline"](
        stack["CSP"](n_components=n_components, reg=None, log=True, norm_trace=False),
        stack["LinearDiscriminantAnalysis"](),
    )

    predictions: list[Any] = []
    truth: list[Any] = []
    split_method = "stratified-holdout"

    unique_groups = sorted(set(groups))
    if len(unique_groups) >= 2:
        split_method = "leave-one-subject-out"
        splitter = stack["LeaveOneGroupOut"]()
        split_iterator = splitter.split(x_data, label_array, groups)
    else:
        splitter = stack["StratifiedShuffleSplit"](n_splits=1, test_size=0.3, random_state=seed)
        split_iterator = splitter.split(x_data, label_array)

    for train_index, test_index in split_iterator:
        pipeline.fit(x_data[train_index], label_array[train_index])
        fold_predictions = pipeline.predict(x_data[test_index])
        predictions.extend(fold_predictions.tolist())
        truth.extend(label_array[test_index].tolist())

    accuracy = float(stack["accuracy_score"](truth, predictions))
    balanced_accuracy = float(stack["balanced_accuracy_score"](truth, predictions))
    runtime_seconds = round(time.perf_counter() - started, 3)

    plot_path = _write_metric_plot(
        dataset_name,
        {"accuracy": accuracy, "balanced_accuracy": balanced_accuracy},
        plot_dir=plot_dir,
        plt=stack["plt"],
    )

    sample_info = load_sample_info(dataset, subjects[0])
    metadata = metadata_from_moabb(
        dataset_name,
        dataset,
        subjects_used=subjects,
        sample_info=sample_info,
    )

    result = {
        "dataset": dataset_name,
        "paradigm": "motor imagery",
        "subjects": subjects,
        "n_subjects": len(subjects),
        "n_trials": int(len(label_array)),
        "classes": sorted(str(label) for label in set(label_array)),
        "pipeline": "CSP + LDA",
        "baseline": "CSP + LDA",
        "split_method": split_method,
        "seed": seed,
        "metrics": {
            "accuracy": round(accuracy, 6),
            "balanced_accuracy": round(balanced_accuracy, 6),
        },
        "runtime_seconds": runtime_seconds,
        "library_versions": _library_versions(["mne", "moabb", "scikit-learn"]),
        "plot_path": str(plot_path),
        "warnings": [
            "Metrics are dataset-specific and do not prove real-world BCI reliability.",
            "Avoid trial-level random splits across subjects; subject-aware splits reduce leakage risk.",
            "This is not medical software and should not be used for diagnosis or treatment.",
        ],
    }
    return result, metadata


def _library_versions(packages: list[str]) -> dict[str, str]:
    versions = {}
    for package in packages:
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = "unknown"
    return versions


def _subject_groups(frame: Any, *, fallback_subjects: list[int], n_trials: int) -> list[int]:
    if hasattr(frame, "__getitem__") and "subject" in getattr(frame, "columns", []):
        return [int(value) for value in frame["subject"].tolist()]
    if len(fallback_subjects) == 1:
        return [int(fallback_subjects[0])] * n_trials
    return [int(fallback_subjects[index % len(fallback_subjects)]) for index in range(n_trials)]


def _write_metric_plot(
    dataset_name: str,
    metrics: dict[str, float],
    *,
    plot_dir: Path | str,
    plt: Any,
) -> Path:
    target_dir = ensure_dir(plot_dir)
    target = target_dir / f"{safe_name(dataset_name)}.png"

    labels = list(metrics)
    values = [metrics[label] for label in labels]

    figure, axis = plt.subplots(figsize=(6, 4))
    axis.bar(labels, values, color=["#2563eb", "#16a34a"])
    axis.set_ylim(0, 1)
    axis.set_ylabel("Score")
    axis.set_title(f"{dataset_name} baseline metrics")
    for index, value in enumerate(values):
        axis.text(index, min(value + 0.03, 0.98), f"{value:.3f}", ha="center")
    figure.tight_layout()
    figure.savefig(target, dpi=150)
    plt.close(figure)
    return target
