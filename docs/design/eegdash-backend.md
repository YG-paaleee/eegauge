# Design Spec: EEGDash backend + evaluation-provenance card (draft v0.1)

> Status: **draft for review - no code yet.** Decide scope before building.
> Author target: a v0.3.0 milestone for bci-dataset-cards.

## 1. Goal and positioning

EEGDash (launched ~June 2026) does **discovery + loading**: 791 OpenNeuro/NEMAR
datasets exposed as queryable, ML-ready (PyTorch/Braindecode) classes, with BIDS
validation. It does **not** record how a dataset was evaluated or whether a score
should be trusted. That downstream layer is our niche.

**Step 1 (this spec): metadata-only.** Add `bcicards scan --backend eegdash <id>`
that reads EEGDash metadata and emits (a) a human-readable card and (b) a
machine-readable **evaluation-provenance record**. No signal download, no benchmark.

Explicitly *not* in step 1: running baselines on EEGDash data, Hugging Face export,
upstream integration. Those are later, separately-decided phases.

## 2. Why metadata-only first (the guardrails)

- EEGDash is ~1 week old; its API may change. Keep our surface tiny and isolated.
- A generic CSP+LDA baseline is only meaningful for motor-imagery datasets with
  consistent labels; most of the 791 are other modalities/tasks. So a universal
  "baseline accuracy" is not achievable or honest. Defer baselines.
- Metadata calls are cheap, testable, and mockable in CI (no large downloads).

## 3. Architecture (fits the existing codebase)

Introduce a backend abstraction; refactor the current MOABB path into it unchanged.

```
src/bcicards/backends/
  base.py     # DatasetBackend Protocol
  moabb.py    # existing logic moved here (behavior identical)
  eegdash.py  # new adapter
```

```python
class DatasetBackend(Protocol):
    def get_dataset_metadata(self, dataset_id: str) -> DatasetMetadata: ...
    def list_records(self, dataset_id: str, filters: dict | None = None) -> list[dict]: ...
```

- CLI: add `--backend {moabb,eegdash}` (default `moabb`) to `scan`. `benchmark`
  stays MOABB-only for now.
- Reuse the existing `DatasetMetadata` dataclass and `render_dataset_card`
  (already has license / DOI / citation rows from v0.2.0).
- Lazy import + `DependencyMissingError`, exactly like the MOABB path. New optional
  extra: `eegdash` (`pip install -e ".[eegdash]"`).

## 4. EEGDash API touchpoints (verified against eegdash 0.8.2)

- `from eegdash import EEGDash`
- `EEGDash().get_dataset(dataset_id) -> Mapping` - dataset-level metadata. Real
  fields include: `dataset_id`, `source`, `recording_modality` (list),
  `senior_author`, `contact_info`, `bids_validator_status` (`pass`/`fail`/`unknown`),
  `n_validator_errors`, `top_issue_code` (schema allows extra fields).
- `EEGDash().find(query)` / `find_datasets(query)` - list records **without
  downloading signals**. Each record carries `entities`:
  `subject` / `session` / `task` / `run` / `acquisition`. This is the cohort grain.
- We only ever call read methods (`get_dataset`, `find`, `count`). Never `insert` /
  `update_*`.

## 5. What the card shows (scan, metadata-only)

Map EEGDash metadata onto existing card fields, plus a few new ones:

| Card field | Source |
| --- | --- |
| Dataset / source archive | `dataset_id`, `source` (OpenNeuro/NEMAR) |
| Modalities | `recording_modality` |
| Subjects / records | derived from `find()` entity counts |
| License / DOI / Citation | existing rows (license, DOI; citation from `senior_author`) |
| **BIDS validation** (new) | `bids_validator_status` + `n_validator_errors` |
| **Leakage risk factors** (new) | derived from record entities (see below) |

**Leakage risk factors** = an honest, non-verdict note, NOT a "RISK: HIGH" badge.
Example: if any subject has >1 session or >1 run, emit:
> "Multiple sessions/runs per subject are present. A random epoch-level shuffle
> would mix them and inflate accuracy. Use subject-wise (and ideally
> session-aware) splits."
If a single session/run per subject: say so. This stays within the responsible-claims ethos.

## 6. The novel piece: evaluation-provenance record

Emit a machine-readable `*.provenance.json` capturing the **exact cohort**, so
"we used ds002718" becomes fully reproducible:

```json
{
  "schema": "bci-evaluation-card/0.1",
  "backend": "eegdash",
  "dataset_id": "ds002718",
  "source": "openneuro",
  "retrieved_at": "<ISO timestamp>",
  "record_query": { "modality": "eeg", "task": "..." },
  "selected": {
    "n_subjects": 18, "n_sessions": 18, "n_records": 18,
    "subjects": ["sub-01", "..."]
  },
  "bids_validation": { "status": "pass", "n_errors": 0 },
  "leakage_risk_factors": ["multiple runs per subject"],
  "evaluation": null,            // filled only in a later benchmark phase
  "environment": { "eegdash": "0.8.2", "bcicards": "0.3.0" }
}
```

Markdown stays the human view; JSON is the reproducibility record. The `evaluation`
block stays `null` until (and if) we add baselines later.

## 7. New `DatasetMetadata` fields

Add (all optional, default None/empty): `modalities: list[str]`,
`source_archive: str | None`, `bids_status: str | None`,
`bids_n_errors: int | None`, `n_records: int | None`. The card renderer gets rows
for these; missing values degrade to "Not available" (existing behavior).

## 8. Testing (no network in CI)

- Mock the `EEGDash` client (canned `get_dataset` / `find` return values), mirroring
  the existing MOABB fake-stack pattern in `tests/`. Assert: card fields, leakage-risk
  note logic, provenance JSON shape.
- One *manual/opt-in* live smoke test hitting the real API for a single dataset id.
- Keep MOABB tests green (the refactor must be behavior-preserving).

## 9. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| 1-week-old API changes | Tiny surface (`get_dataset`/`find`), isolated adapter, optional extra, lazy import |
| Network flakiness | Metadata-only; everything mocked in CI |
| Scope creep into baselines | Hard line: no signal download in step 1 |
| Is it useful to EEGDash? (unknown) | Step 1 is standalone-useful; only pitch upstream after the artifact exists |

## 10. Effort (realistic at ~2 hrs/week)

1. Backend Protocol + move MOABB into `backends/moabb.py` (behavior identical) - 1 session
2. `eegdash.py` adapter (`get_dataset` + `find` mapping) - 1-2 sessions
3. Provenance JSON + leakage-risk note + new card fields - 1 session
4. Tests + one committed example (e.g. `ds002718`) + docs - 1-2 sessions

-> ~5-6 short sessions to a shippable **v0.3.0: "EEGDash scan + evaluation-provenance."**

## 11. After step 1

Open an EEGDash **discussion/issue** (not a PR) linking the example, proposing an
optional evaluation section in their dataset pages - citing their existing
`_format_quality_section` as the precedent and offering this tool as the data source,
scoped to "datasets with a defined task." Only then consider any integration PR.
