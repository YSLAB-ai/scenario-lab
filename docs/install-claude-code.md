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
packages/core/.venv/bin/python adapters/claude/scenario-lab/install.py --target-dir /tmp/claude-root
```

Add `--link` to symlink the bundle instead of copying it while iterating locally.

When you install into a real Claude root such as `~/.claude`, the bundle now includes a native Claude project/user command at `commands/scenario-lab/scenario.md`. That gives you a chat-level `/scenario` command in Claude Code.

Example use in Claude Code:

```text
/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days
```

That command uses the repo’s `scenario-lab scenario` bootstrap, summarizes the inferred actors and next stage, and then stops for approval instead of silently running the whole workflow.

## Smoke the packaged bundle

```bash
packages/core/.venv/bin/python adapters/claude/scenario-lab/smoke.py --work-dir /tmp/scenario-lab-claude-smoke
```

## Next docs

- `docs/quickstart.md`
- `docs/natural-language-workflow.md`
- `docs/demo-us-iran.md`
