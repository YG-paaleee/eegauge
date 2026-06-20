"""Small filesystem helpers for CLI outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def safe_name(value: str) -> str:
    """Return a filesystem-safe name while preserving readable dataset IDs."""

    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return cleaned.strip("-") or "dataset"


def ensure_dir(path: Path | str) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def write_json(path: Path | str, payload: dict[str, Any]) -> Path:
    target = Path(path)
    ensure_dir(target.parent)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def write_text(path: Path | str, content: str) -> Path:
    target = Path(path)
    ensure_dir(target.parent)
    target.write_text(content.rstrip() + "\n", encoding="utf-8")
    return target
