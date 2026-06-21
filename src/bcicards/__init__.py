"""Utilities for generating beginner-friendly BCI dataset cards."""

# Single source of truth for the version. pyproject.toml reads this via
# [tool.setuptools.dynamic], and the CLI imports it for `bcicards --version`.
__version__ = "0.3.0"
