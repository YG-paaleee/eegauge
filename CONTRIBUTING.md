# Contributing to BCI Dataset Cards

Thanks for your interest! This project is intentionally small and beginner-friendly.
Its goal is to make public EEG/BCI datasets easier to inspect and to make simple
baselines reproducible and honest about their limits.

You do **not** need EEG hardware or deep neuroscience knowledge to contribute.

## Ways to help

- Improve documentation or wording in the README and dataset cards.
- Add support for another public MOABB motor-imagery dataset.
- Improve leakage/limitation warnings.
- Add tests (we prefer mocked metadata over large EEG downloads in CI).
- Report a bug or a confusing result via an issue.

Look for issues labelled `good first issue` to get started.

## Development setup

Python 3.11 or 3.12 is recommended (the scientific stack can lag on the newest
Python release).

```bash
python -m venv .venv
# Windows:  .\.venv\Scripts\Activate.ps1
# macOS/Linux:  source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"   # mocked tests only, no heavy downloads
python -m pytest
```

To run a real benchmark you also need the science stack:

```bash
python -m pip install -e ".[bci]"
bcicards benchmark --dataset BNCI2014_001 --subjects 1 2 3
```

EEG downloads can be large. Keep them out of the repo (see the README section
on dataset downloads). The `.gitignore` already blocks common data folders and
`.mat` files.

## Pull requests

1. Keep changes focused and small.
2. Run `python -m pytest` before opening a PR.
3. Run a CLI smoke check: `bcicards --help`.
4. Do not add medical, diagnostic, "mind reading", or assistive-reliability claims.
   This project is research tooling for public datasets only.

## Scope and claims

This is not medical software. Reported metrics are only meaningful with the stated
split method, subject count, preprocessing, and dataset limitations. Please keep all
contributions modest and verifiable.
