# Scenario Lab Claude Bundle

This packaged local bundle installs Scenario Lab into a local Claude root and verifies the end-to-end runtime path with the packaged smoke flow.

```bash
packages/core/.venv/bin/python adapters/claude/scenario-lab/install.py --target-dir /tmp/claude-root
packages/core/.venv/bin/python adapters/claude/scenario-lab/smoke.py --work-dir /tmp/scenario-lab-claude-smoke
```

If you install into a real Claude root such as `~/.claude`, the bundle also installs a native Claude slash command:

```text
/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days
```
