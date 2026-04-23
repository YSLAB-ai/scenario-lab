# Scenario Lab Claude Bundle

This packaged local bundle installs Scenario Lab into a local Claude root and verifies the end-to-end runtime path with the packaged smoke flow.

```bash
packages/core/.venv/bin/python adapters/claude/scenario-lab/install.py --target-dir /tmp/claude-root
packages/core/.venv/bin/python adapters/claude/scenario-lab/smoke.py --work-dir /tmp/scenario-lab-claude-smoke
```
