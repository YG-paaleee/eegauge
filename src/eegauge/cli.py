"""Command-line interface for EEGauge."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path

from . import __version__
from .backends import BACKENDS, get_backend
from .benchmark import run_benchmark
from .cards import render_dataset_card
from .datasets import SUPPORTED_DATASETS
from .errors import DependencyMissingError
from .io import safe_name, write_json, write_text
from .provenance import build_provenance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eegauge",
        description="Generate dataset cards and simple baselines for public EEG/BCI datasets.",
    )
    parser.add_argument("--version", action="version", version=f"eegauge {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Generate a dataset card from dataset metadata.")
    scan.add_argument(
        "--dataset",
        required=True,
        help="Dataset id: a MOABB code (e.g. BNCI2014_001) or an EEGDash id (e.g. ds002718).",
    )
    scan.add_argument(
        "--backend",
        choices=sorted(BACKENDS),
        default="moabb",
        help="Metadata source backend (default: moabb).",
    )
    scan.add_argument("--cards-dir", default="cards", help="Directory for Markdown cards.")
    scan.add_argument(
        "--results-dir",
        default="results",
        help="Directory for the provenance JSON (eegdash backend).",
    )
    scan.add_argument(
        "--sample-subject",
        type=int,
        default=None,
        help="MOABB only: load one subject to infer channels and sampling rate.",
    )
    scan.set_defaults(func=handle_scan)

    benchmark = subparsers.add_parser("benchmark", help="Run a small CSP + LDA baseline.")
    benchmark.add_argument("--dataset", required=True, choices=sorted(SUPPORTED_DATASETS))
    benchmark.add_argument("--subjects", nargs="+", type=int, required=True)
    benchmark.add_argument("--cards-dir", default="cards", help="Directory for Markdown cards.")
    benchmark.add_argument(
        "--results-dir", default="results", help="Directory for JSON and plot outputs."
    )
    benchmark.add_argument("--seed", type=int, default=42)
    benchmark.set_defaults(func=handle_benchmark)

    return parser


def handle_scan(args: argparse.Namespace) -> int:
    backend = get_backend(args.backend)
    metadata = backend.get_dataset_metadata(args.dataset, sample_subject=args.sample_subject)

    card_path = Path(args.cards_dir) / f"{safe_name(args.dataset)}.md"
    write_text(card_path, render_dataset_card(metadata))
    print(f"Wrote {card_path}")

    if args.backend == "eegdash":
        records = backend.list_records(args.dataset)
        provenance = build_provenance(
            backend=args.backend,
            dataset_id=args.dataset,
            metadata=metadata,
            records=records,
            filters=None,
            retrieved_at=datetime.now(UTC).isoformat(timespec="seconds"),
            versions={"eegauge": __version__, **_versions(["eegdash"])},
        )
        prov_path = Path(args.results_dir) / f"{safe_name(args.dataset)}.provenance.json"
        write_json(prov_path, provenance)
        print(f"Wrote {prov_path}")
    return 0


def handle_benchmark(args: argparse.Namespace) -> int:
    result, metadata = run_benchmark(
        args.dataset,
        args.subjects,
        seed=args.seed,
        plot_dir=args.results_dir,
    )
    result_path = Path(args.results_dir) / f"{safe_name(args.dataset)}.json"
    card_path = Path(args.cards_dir) / f"{safe_name(args.dataset)}.md"
    write_json(result_path, result)
    write_text(card_path, render_dataset_card(metadata, result))
    print(f"Wrote {result_path}")
    print(f"Wrote {card_path}")
    return 0


def _versions(packages: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for package in packages:
        try:
            out[package] = _pkg_version(package)
        except PackageNotFoundError:
            out[package] = "unknown"
    return out


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except DependencyMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
