# Install in Codex

1. From the checked-out forecasting harness repo root, create and activate a Python 3.12+ virtualenv.
2. Run `pip install -e 'packages/core[dev]'`.
3. Copy `adapters/codex/forecast-harness` into your local Codex plugins directory or link it from your workspace.
4. Verify the shared CLI works with:
   - `forecast-harness demo-run`
   - `forecast-harness start-run --help`
   - `forecast-harness save-intake-draft --help`
   - `forecast-harness save-evidence-draft --help`
   - `forecast-harness approve-revision --help`
   - `forecast-harness simulate --help`
   - `forecast-harness generate-report --help`
