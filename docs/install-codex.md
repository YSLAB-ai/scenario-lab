# Install in Codex

1. From the checked-out forecasting harness repo root, create and activate `packages/core/.venv` with a Python 3.12+ interpreter.
   - `PYTHON=/path/to/python3.12`
   - `"$PYTHON" -m venv packages/core/.venv`
   - `source packages/core/.venv/bin/activate`
2. Run `pip install -e 'packages/core[dev]'`.
3. Install the packaged local Codex bundle into your Codex plugin root. For a disposable local test root, use `/tmp/codex-plugins`.
   - `packages/core/.venv/bin/python adapters/codex/forecast-harness/install.py --target-dir /tmp/codex-plugins`
   - optional: add `--link` to symlink the bundle instead of copying it while iterating locally
4. Run the packaged adapter smoke from the same virtualenv:
   - `packages/core/.venv/bin/python adapters/codex/forecast-harness/smoke.py`
5. Verify the shared CLI query-style commands are available:
   - `forecast-harness start-run --help`
   - `forecast-harness run-adapter-action --help`
   - `forecast-harness save-intake-draft --help`
   - `forecast-harness draft-conversation-turn --help`
   - `forecast-harness batch-ingest-recommended --help`
   - `forecast-harness draft-evidence-packet --help`
   - `forecast-harness curate-evidence-draft --help`
   - `forecast-harness draft-approval-packet --help`
   - `forecast-harness approve-revision --help`
   - `forecast-harness begin-revision-update --help`
   - `forecast-harness simulate --help`
   - `forecast-harness summarize-run --help`
   - `forecast-harness summarize-revision --help`
   - `forecast-harness generate-report --help`
6. Drive the workflow through the packaged adapter runtime instead of manually chaining raw workflow commands. For the normal adapter path, still prefer direct structured input over temporary JSON files.
   - bootstrap the run with:
     - `forecast-harness run-adapter-action --root <root> --run-id <run> --revision-id r1 --action start-run --domain-pack <slug>`
   - the underlying raw commands still exist, including `forecast-harness start-run` and `forecast-harness draft-conversation-turn`, but the packaged runtime is the normal path
   - after each workflow mutation, advance the loop with the same command:
     - `forecast-harness run-adapter-action --root <root> --corpus-db <db> [--candidate-path <dir>] --run-id <run> --revision-id <rev> --action <action-name> ...`
   - treat `turn.recommended_runtime_action` as the default next runtime action
   - treat `turn.actions` as the ordered set of allowed next steps
   - use `turn.context` instead of separately calling `forecast-harness draft-intake-guidance`, `forecast-harness draft-retrieval-plan`, or `forecast-harness draft-ingestion-plan` during the normal path
   - when the runtime returns evidence-stage `ingestion_recommendations`, prefer `--action batch-ingest-recommended` before `--action draft-evidence-packet`
   - after approval, keep using `run-adapter-action` to reach simulation, report review, and `begin-revision-update`
7. Use `forecast-harness draft-conversation-turn` only for inspection, recovery, or debugging when you need to query the current stage without executing a mutation.
8. If the adapter needs to replace the drafted packet instead of curating the existing draft in place, use either:
   - `forecast-harness run-adapter-action --root <root> --run-id <run> --revision-id <rev> --action save-evidence-draft --item-json '<item-json>'`
   - or `forecast-harness save-evidence-draft --root <root> --run-id <run> --revision-id <rev> --item-json '<item-json>'`
