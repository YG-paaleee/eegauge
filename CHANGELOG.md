# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.1] - 2026-06-21

### Fixed
- EEGDash metadata mapping against the live API: read the DOI from `dataset_doi`
  (with the `doi:` prefix stripped) and the citation from `author_year`, and read
  BIDS entities (subject/session/task/run) whether nested under `entities` or flat
  at the top level. Verified end to end against `ds002718` (Wakeman face-processing).

### Added
- A real EEGDash example under `examples/` (`ds002718` card + provenance JSON).

## [0.3.0] - 2026-06-21

### Added
- Pluggable dataset-source backends via a `DatasetBackend` protocol. The existing
  MOABB logic is exposed through a `moabb` backend; a new `eegdash` backend reads
  metadata from EEGDash (OpenNeuro/NEMAR) without downloading signals.
- `bcicards scan --backend eegdash <dataset-id>` produces a metadata card plus a
  machine-readable evaluation-provenance record (`<id>.provenance.json`,
  schema `bci-evaluation-card/0.1`) capturing the exact cohort (subjects/sessions/
  records), BIDS validation status, and honest leakage *risk factors*.
- New optional card fields: modalities, records, BIDS validation, surfaced for the
  eegdash backend (MOABB cards are unchanged; missing values show "Not available").
- `eegdash` optional dependency extra (`pip install -e ".[eegdash]"`).
- Design spec at `docs/design/eegdash-backend.md`.

### Notes
- The eegdash backend is metadata-only by design (no signal download, no baseline
  yet). EEGDash is new and its API may change; the backend is isolated and its
  surface is intentionally small.

## [0.2.1] - 2026-06-20

### Fixed
- `bcicards --version` reported the wrong version. The version is now single-sourced
  from `bcicards.__version__`, read by both the CLI and `pyproject.toml` (dynamic
  metadata), so it cannot drift again.
- Card plot paths now use forward slashes, and the committed example card references
  its co-located images so they render on GitHub.
- Replaced non-ASCII em dashes in the README and `.gitignore` with plain ASCII.

### Added
- A CLI `--version` smoke test that guards against version drift.

## [0.2.0] - 2026-06-20

### Added
- Chance level and an approximate one-sided binomial significance test (is the
  score above chance?) in benchmark results and cards (closes #1).
- Per-class precision/recall/F1 table and a confusion-matrix plot in cards.
- Dataset license, DOI, and a citation line in cards, read defensively from MOABB
  metadata (closes #2).
- Three more motor-imagery datasets: `BNCI2014_004`, `Zhou2016`, `Weibo2014`
  (closes #3).
- `.pre-commit-config.yaml` running Ruff (lint + format) for contributors.
- `CONTRIBUTING.md`, `CHANGELOG.md`, and GitHub issue templates.
- Real example output (card + plots) from a `BNCI2014_001` benchmark run.
- Ruff linting and formatting, enforced by a dedicated CI job (`[lint]` extra).

### Notes
- The "above chance" check is an approximate binomial test versus the naive chance
  level (1 / number of classes), not a permutation test. It is a sanity check only.

## [0.1.0] - 2026-06-20

### Added
- `bcicards scan` to generate a Markdown dataset card from MOABB metadata.
- `bcicards benchmark` to run a small CSP + LDA motor-imagery baseline and
  save results as JSON plus a metrics plot.
- Subject-aware (leave-one-subject-out) splitting when multiple subjects are
  provided; stratified holdout for a single subject.
- Explicit leakage warnings and "what this does not prove" sections in cards.
- Mocked unit tests and CI across Windows/Linux and Python 3.11/3.12.
