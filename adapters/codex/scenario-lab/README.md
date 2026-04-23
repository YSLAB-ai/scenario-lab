# Scenario Lab Codex Bundle

This packaged local bundle installs Scenario Lab into a local Codex plugin root and verifies the end-to-end runtime path with the packaged smoke flow.

```bash
packages/core/.venv/bin/python adapters/codex/scenario-lab/install.py --target-dir /tmp/codex-plugins
packages/core/.venv/bin/python adapters/codex/scenario-lab/smoke.py --work-dir /tmp/scenario-lab-codex-smoke
```
