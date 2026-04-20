# Install in Claude Code

1. From the checked-out forecasting harness repo root, create and activate a Python 3.12+ virtualenv.
2. Run `pip install -e 'packages/core[dev]'`.
3. Copy `adapters/claude/skills/forecast-harness` into `.claude/skills/` for the target workspace or personal Claude directory.
4. Verify the shared CLI works with:
   - `forecast-harness demo-run`
   - `forecast-harness start-run --help`
   - `forecast-harness simulate --help`
   - `forecast-harness generate-report --help`
