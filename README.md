# Forecasting Harness

Minimal core package for forecasting harness experiments.

## Quickstart

From the repository root, set `PYTHON` to any Python 3.12+ interpreter on your system:

```bash
PYTHON=/path/to/python3.12+-interpreter
"$PYTHON" -m venv .venv
source .venv/bin/activate
pip install -e 'packages/core[dev]'
forecast-harness demo-run
```

Requires Python 3.12+.

## Current Workflow Slice

The local CLI now supports the verified workflow commands:

- `forecast-harness version`
- `forecast-harness demo-run`
- `forecast-harness list-domain-packs`
- `forecast-harness ingest-file`
- `forecast-harness ingest-directory`
- `forecast-harness list-corpus-sources`
- `forecast-harness start-run`
- `forecast-harness save-intake-draft`
- `forecast-harness save-evidence-draft`
- `forecast-harness draft-evidence-packet`
- `forecast-harness approve-revision`
- `forecast-harness simulate`
- `forecast-harness generate-report`

Verified current progress:

- The reusable workflow core now supports registry-backed domain-pack discovery, local corpus ingestion, revisioned runs, draft/approved artifacts, retrieval-backed evidence drafting, belief-state compilation, revisioned simulation outputs, and report generation.
- The repository includes two domain packs: `generic-event` and the `interstate-crisis` reference pack.
- The current workflow slice test suite passes with `107 passed` under `packages/core/.venv/bin/python -m pytest packages/core -q`.
- The workflow slice persists artifacts locally under `.forecast/runs/<run-id>/`, including revision-specific files such as `belief-state/<revision>.approved.json`, `simulation/<revision>.approved.json`, `reports/<revision>.report.md`, and `revisions/<revision>.json`.
- The intake schema now accepts generic fields such as `focus_entities`, `current_development`, `current_stage`, and `pack_fields`, while still accepting the older interstate-oriented aliases.
- The local corpus can now ingest curated `Markdown`, `CSV`, `JSON`, and text-extractable `PDF` files into a searchable SQLite/FTS corpus with citation-friendly chunk locations.

## Remaining Gaps

- The broader analyst workflow is still a local filesystem slice, not the full product described in the design spec.
- Intake, evidence, and assumptions are still file-backed JSON inputs; there is not yet a conversational adapter loop that drafts and approves them end to end.
- The repository still relies on curated local inputs rather than open-web retrieval.
- The current simulation engine is still a one-step branch enumerator, not a full MCTS implementation.
- The `interstate-crisis` pack is still a reference pack with fixed actions, transitions, and scores.
- Only one concrete reference domain pack is implemented for the new workflow slice; broader multi-domain coverage remains future work.
- Corpus ingestion does not yet support OCR PDFs, spreadsheets, or web archives.
