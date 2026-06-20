# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `CONTRIBUTING.md` with beginner-friendly setup and contribution guidance.
- GitHub issue templates for bug reports and feature requests.
- Real example output (card + plot) from a `BNCI2014_001` benchmark run.
- Ruff linting and formatting, enforced by a dedicated CI job (`[lint]` extra).

## [0.1.0] - 2026-06-20

### Added
- `bcicards scan` to generate a Markdown dataset card from MOABB metadata.
- `bcicards benchmark` to run a small CSP + LDA motor-imagery baseline and
  save results as JSON plus a metrics plot.
- Subject-aware (leave-one-subject-out) splitting when multiple subjects are
  provided; stratified holdout for a single subject.
- Explicit leakage warnings and "what this does not prove" sections in cards.
- Mocked unit tests and CI across Windows/Linux and Python 3.11/3.12.
