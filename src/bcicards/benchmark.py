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
        from scipy.stats import binomtest
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.metrics import (
            accuracy_score,
            balanced_accuracy_score,
            confusion_matrix,
            precision_recall_fscore_support,
        )
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
        "confusion_matrix": confusion_matrix,
        "precision_recall_fscore_support": precision_recall_fscore_support,
        "binomtest": binomtest,
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

    class_labels = sorted(str(label) for label in set(label_array))
    n_test_trials = len(truth)
    n_correct = sum(
        1 for actual, predicted in zip(truth, predictions, strict=True) if actual == predicted
    )
    chance_level = 1.0 / class_count if class_count else None
    significance = _significance(
        n_correct,
        n_test_trials,
        chance_level,
        binomtest=stack["binomtest"],
    )
    per_class_metrics = _per_class_metrics(
        truth,
        predictions,
        class_labels,
        precision_recall_fscore_support=stack["precision_recall_fscore_support"],
    )
    confusion = {
        "labels": class_labels,
        "matrix": [
            [int(value) for value in row]
            for row in stack["confusion_matrix"](truth, predictions, labels=class_labels)
        ],
    }

    runtime_seconds = round(time.perf_counter() - started, 3)

    plot_path = _write_metric_plot(
        dataset_name,
        {"accuracy": accuracy, "balanced_accuracy": balanced_accuracy},
        plot_dir=plot_dir,
        plt=stack["plt"],
    )
    confusion_matrix_path = _write_confusion_matrix_plot(
        dataset_name,
        confusion,
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
        "chance_level": round(chance_level, 6) if chance_level is not None else None,
        "n_test_trials": n_test_trials,
        "significance": significance,
        "per_class_metrics": per_class_metrics,
        "confusion_matrix": confusion,
        "runtime_seconds": runtime_seconds,
        "library_versions": _library_versions(["mne", "moabb", "scikit-learn"]),
        "plot_path": str(plot_path),
        "confusion_matrix_path": str(confusion_matrix_path),
        "warnings": [
            "Metrics are dataset-specific and do not prove real-world BCI reliability.",
            (
                "Avoid trial-level random splits across subjects; "
                "subject-aware splits reduce leakage risk."
            ),
            (
                "The 'above chance' check is an approximate one-sided binomial test "
                "against the naive chance level (1 / number of classes), not a "
                "permutation test; treat it as a sanity check, not proof."
            ),
            "This is not medical software and should not be used for diagnosis or treatment.",
        ],
    }
    return result, metadata


def _significance(
    n_correct: int,
    n_total: int,
    chance_level: float | None,
    *,
    binomtest: Any,
) -> dict[str, Any] | None:
    if chance_level is None or n_total <= 0:
        return None
    p_value = float(binomtest(n_correct, n_total, p=chance_level, alternative="greater").pvalue)
    return {
        "test": "binomial (one-sided, vs chance)",
        "p_value": round(p_value, 6),
        "above_chance": bool(p_value < 0.05),
    }


def _per_class_metrics(
    truth: list[Any],
    predictions: list[Any],
    class_labels: list[str],
    *,
    precision_recall_fscore_support: Any,
) -> list[dict[str, Any]]:
    precision, recall, f1, support = precision_recall_fscore_support(
        truth, predictions, labels=class_labels, zero_division=0
    )
    return [
        {
            "class": label,
            "precision": round(float(precision[index]), 6),
            "recall": round(float(recall[index]), 6),
            "f1": round(float(f1[index]), 6),
            "support": int(support[index]),
        }
        for index, label in enumerate(class_labels)
    ]


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


def _write_confusion_matrix_plot(
    dataset_name: str,
    confusion: dict[str, Any],
    *,
    plot_dir: Path | str,
    plt: Any,
) -> Path:
    target_dir = ensure_dir(plot_dir)
    target = target_dir / f"{safe_name(dataset_name)}_confusion.png"

    labels = confusion["labels"]
    matrix = confusion["matrix"]

    figure, axis = plt.subplots(figsize=(5, 4))
    image = axis.imshow(matrix, cmap="Blues")
    axis.set_xticks(range(len(labels)))
    axis.set_yticks(range(len(labels)))
    axis.set_xticklabels(labels, rotation=45, ha="right")
    axis.set_yticklabels(labels)
    axis.set_xlabel("Predicted")
    axis.set_ylabel("True")
    axis.set_title(f"{dataset_name} confusion matrix")
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            axis.text(j, i, str(value), ha="center", va="center")
    figure.colorbar(image, ax=axis)
    figure.tight_layout()
    figure.savefig(target, dpi=150)
    plt.close(figure)
    return target
