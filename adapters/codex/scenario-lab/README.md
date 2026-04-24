# Scenario Lab Codex Bundle

This packaged local bundle installs Scenario Lab into a local Codex plugin root and verifies the end-to-end runtime path with the packaged smoke flow.

```bash
packages/core/.venv/bin/python adapters/codex/scenario-lab/install.py --target-dir /tmp/codex-plugins
packages/core/.venv/bin/python adapters/codex/scenario-lab/smoke.py --work-dir /tmp/scenario-lab-codex-smoke
```

Evidence commands default to `.forecast/corpus.db`. If a run has no evidence corpus yet, save candidate evidence files under `.forecast/evidence-candidates/`, run `scenario-lab run-adapter-action --root .forecast --candidate-path .forecast/evidence-candidates --run-id <run-id> --revision-id r1 --action batch-ingest-recommended`, then run `scenario-lab run-adapter-action --root .forecast --run-id <run-id> --revision-id r1 --action draft-evidence-packet`.
