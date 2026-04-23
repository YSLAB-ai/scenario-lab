# Scenario Lab for Claude

Use this local bundle to install the Scenario Lab Claude adapter into a local Claude root and verify the packaged runtime path.

## Python 3.12+ environment

```bash
PYTHON=/path/to/python3.12
"$PYTHON" -m venv packages/core/.venv
source packages/core/.venv/bin/activate
pip install -e 'packages/core[dev]'
```

## Install the local bundle

For a disposable local Claude root:

```bash
packages/core/.venv/bin/python adapters/claude/forecast-harness/install.py --target-dir /tmp/claude-root
```

Add `--link` to symlink the bundle instead of copying it while iterating locally.

## Smoke the packaged bundle

```bash
packages/core/.venv/bin/python adapters/claude/forecast-harness/smoke.py --work-dir /tmp/scenario-lab-claude-smoke
```

## Next docs

- `docs/quickstart.md`
- `docs/natural-language-workflow.md`
- `docs/demo-us-iran.md`
