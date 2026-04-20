# Install in Claude Code

1. Create and activate a virtualenv at the repo root.
2. Run `pip install -e packages/core[dev]`.
3. Copy `adapters/claude/skills/forecast-harness` into `.claude/skills/` for the target workspace or personal Claude directory.
4. Verify the shared CLI works with `forecast-harness demo-run`.
