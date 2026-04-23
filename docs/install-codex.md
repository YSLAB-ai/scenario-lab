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

## Next docs

- `docs/quickstart.md`
- `docs/natural-language-workflow.md`
- `docs/demo-us-iran.md`
