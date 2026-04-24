# Scenario Lab for Codex

Use this local bundle to install the Scenario Lab Codex adapter into a local plugin root and verify the packaged runtime path.

## Python 3.12+ environment

```bash
PYTHON=/path/to/python3.12
"$PYTHON" -m venv packages/core/.venv
source packages/core/.venv/bin/activate
pip install -e 'packages/core[dev]'
```

## Install the local bundle

For a disposable local Codex plugin root:

```bash
packages/core/.venv/bin/python adapters/codex/scenario-lab/install.py --target-dir /tmp/codex-plugins
```

Add `--link` to symlink the bundle instead of copying it while iterating locally.

## Smoke the packaged bundle

```bash
packages/core/.venv/bin/python adapters/codex/scenario-lab/smoke.py --work-dir /tmp/scenario-lab-codex-smoke
```

## Evidence corpus

Codex should use `.forecast/corpus.db` as the default local evidence corpus. When a run reaches evidence collection and no corpus exists yet, save relevant evidence files under `.forecast/evidence-candidates/`, then use:

```bash
scenario-lab run-adapter-action --root .forecast --candidate-path .forecast/evidence-candidates --run-id <run-id> --revision-id r1 --action batch-ingest-recommended
scenario-lab run-adapter-action --root .forecast --run-id <run-id> --revision-id r1 --action draft-evidence-packet
```

Only pass `--corpus-db <path>` when intentionally using a separate evidence database.

## Next docs

- `docs/quickstart.md`
- `docs/natural-language-workflow.md`
- `docs/demo-us-iran.md`
