# Install in Codex

1. From the checked-out forecasting harness repo root, create and activate a Python 3.12+ virtualenv.
2. Run `pip install -e 'packages/core[dev]'`.
3. Copy `adapters/codex/forecast-harness` into your local Codex plugins directory or link it from your workspace.
4. Verify the shared CLI query-style commands are available:
   - `forecast-harness start-run --help`
   - `forecast-harness save-intake-draft --help`
   - `forecast-harness draft-intake-guidance --help`
   - `forecast-harness draft-evidence-packet --help`
   - `forecast-harness save-evidence-draft --help`
   - `forecast-harness draft-approval-packet --help`
   - `forecast-harness approve-revision --help`
   - `forecast-harness simulate --help`
   - `forecast-harness summarize-run --help`
   - `forecast-harness summarize-revision --help`
   - `forecast-harness generate-report --help`
5. Drive the workflow through the guided sequence rather than loading raw run artifacts into the agent context:
   - `forecast-harness start-run`
   - `forecast-harness save-intake-draft`
   - `forecast-harness draft-intake-guidance`
   - `forecast-harness draft-evidence-packet`
   - `forecast-harness save-evidence-draft`
   - `forecast-harness draft-approval-packet`
   - `forecast-harness approve-revision`
   - `forecast-harness simulate`
   - `forecast-harness summarize-revision`
   - `forecast-harness summarize-run`
