"""Evaluation-provenance records (BCI Evaluation Card v0.1).

Captures the exact cohort behind a scan/evaluation so that "we used dataset X"
becomes reproducible. At scan time the ``evaluation`` block is left ``None``; a
future benchmark phase can fill it in.
"""

from __future__ import annotations

from typing import Any

SCHEMA = "bci-evaluation-card/0.1"


def leakage_risk_factors(records: list[dict[str, Any]]) -> list[str]:
    """Return honest leakage *risk factors* from record entities (not a verdict)."""
    by_subject: dict[str, dict[str, set[Any]]] = {}
    for record in records:
        subject = record.get("subject")
        if not subject:
            continue
        slot = by_subject.setdefault(subject, {"session": set(), "run": set()})
        if record.get("session"):
            slot["session"].add(record["session"])
        if record.get("run"):
            slot["run"].add(record["run"])

    factors: list[str] = []
    if any(len(slot["session"]) > 1 for slot in by_subject.values()):
        factors.append(
            "Multiple sessions per subject are present. A random epoch-level shuffle "
            "would mix sessions and can inflate accuracy; prefer subject- and "
            "session-aware splits."
        )
    if any(len(slot["run"]) > 1 for slot in by_subject.values()):
        factors.append(
            "Multiple runs per subject are present. Splitting runs of one subject "
            "across train and test can leak subject-specific signal; prefer "
            "subject-wise splits."
        )
    if not factors and by_subject:
        factors.append(
            "One session/run per subject detected. Subject-wise splitting is still "
            "recommended before making cross-subject claims."
        )
    return factors


def build_provenance(
    *,
    backend: str,
    dataset_id: str,
    metadata: Any,
    records: list[dict[str, Any]],
    filters: dict[str, Any] | None,
    retrieved_at: str,
    versions: dict[str, str],
) -> dict[str, Any]:
    """Build a machine-readable evaluation-provenance record for a scan."""
    subjects = sorted({r["subject"] for r in records if r.get("subject")})
    sessions = {(r.get("subject"), r.get("session")) for r in records if r.get("session")}
    return {
        "schema": SCHEMA,
        "backend": backend,
        "dataset_id": dataset_id,
        "source": getattr(metadata, "source_archive", None),
        "retrieved_at": retrieved_at,
        "record_query": filters or {"dataset": dataset_id},
        "selected": {
            "n_subjects": len(subjects),
            "n_sessions": len(sessions),
            "n_records": len(records),
            "subjects": subjects,
        },
        "bids_validation": {
            "status": getattr(metadata, "bids_status", None),
            "n_errors": getattr(metadata, "bids_n_errors", None),
        },
        "leakage_risk_factors": leakage_risk_factors(records),
        "evaluation": None,
        "environment": versions,
    }
