"""Command-line interface for BCI Dataset Cards."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .benchmark import run_benchmark
from .cards import render_dataset_card
from .datasets import SUPPORTED_DATASETS, scan_dataset
from .errors import DependencyMissingError
from .io import safe_name, write_json, write_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bcicards",
        description="Generate dataset cards and simple baselines for public EEG/BCI datasets.",
    )
    parser.add_argument("--version", action="version", version="bcicards 0.1.0")

    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Generate a dataset card from MOABB metadata.")
    scan.add_argument("--dataset", required=True, choices=sorted(SUPPORTED_DATASETS))
    scan.add_argument("--cards-dir", default="cards", help="Directory for Markdown cards.")
    scan.add_argument(
        "--sample-subject",
        type=int,
        default=None,
        help="Optionally load one subject to infer channels and sampling rate.",
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
    metadata = scan_dataset(args.dataset, sample_subject=args.sample_subject)
    card = render_dataset_card(metadata)
    card_path = Path(args.cards_dir) / f"{safe_name(args.dataset)}.md"
    write_text(card_path, card)
    print(f"Wrote {card_path}")
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
