# Scenario Lab Quickstart

## 1. Create the local environment

```bash
PYTHON=/path/to/python3.12
"$PYTHON" -m venv packages/core/.venv
source packages/core/.venv/bin/activate
pip install -e 'packages/core[dev]'
```

## 2. Run the built-in demo

```bash
scenario-lab demo-run --root .forecast
```

## 3. Inspect the generated artifacts

```bash
ls .forecast/runs/demo-run
cat .forecast/runs/demo-run/report.md
cat .forecast/runs/demo-run/workbench.md
```

You should see `demo-run complete` before inspecting the generated files.

## 4. Build an evidence corpus

Evidence drafting reads from a local SQLite corpus. The default path is `.forecast/corpus.db`, and the CLI creates that database automatically when you ingest evidence or draft an evidence packet.

Create a candidate folder, add evidence files, then ingest them:

```bash
mkdir -p .forecast/evidence-candidates
# Put relevant Markdown, CSV, JSON, spreadsheet, saved web page, or text-extractable PDF files here.
scenario-lab ingest-directory --root .forecast --path .forecast/evidence-candidates --tag domain=interstate-crisis
```

After a run has an intake draft, draft the evidence packet:

```bash
scenario-lab draft-evidence-packet --root .forecast --run-id <run-id> --revision-id r1
```

Agents should normally use the packaged runtime instead of raw commands:

```bash
scenario-lab run-adapter-action --root .forecast --candidate-path .forecast/evidence-candidates --run-id <run-id> --revision-id r1 --action batch-ingest-recommended
scenario-lab run-adapter-action --root .forecast --run-id <run-id> --revision-id r1 --action draft-evidence-packet
```

Use `--corpus-db <path>` only when you intentionally want a corpus outside `.forecast/corpus.db`.
