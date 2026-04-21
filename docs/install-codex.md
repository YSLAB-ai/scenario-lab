# Install in Codex

1. From the checked-out forecasting harness repo root, create and activate a Python 3.12+ virtualenv.
2. Run `pip install -e 'packages/core[dev]'`.
3. Copy `adapters/codex/forecast-harness` into your local Codex plugins directory or link it from your workspace.
4. Verify the shared CLI query-style commands are available:
   - `forecast-harness start-run --help`
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
5. Drive the workflow through the native adapter loop rather than manually sequencing planning commands. For the normal adapter path, still prefer direct structured input over temporary JSON files:
   - start a run with `forecast-harness start-run`
   - save structured intake with `forecast-harness save-intake-draft --event-framing ... --focus-entity ... --current-development ...`
   - after each workflow mutation, call `forecast-harness draft-conversation-turn --corpus-db <db> [--candidate-path <dir>]`
   - treat the returned `recommended_command` as the default next action
   - treat the returned `actions` list as the ordered set of allowed next steps
   - use the returned `context` payload instead of separately calling `forecast-harness draft-intake-guidance`, `forecast-harness draft-retrieval-plan`, or `forecast-harness draft-ingestion-plan` during the normal loop
   - when evidence-stage context includes `ingestion_recommendations`, prefer `forecast-harness batch-ingest-recommended` before drafting evidence
   - once evidence is drafted, curate it in place with `forecast-harness curate-evidence-draft`, then ask `draft-conversation-turn` for the approval packet stage
   - after approval, use the same loop to reach simulation, report review, and `begin-revision-update`
6. Use `forecast-harness save-evidence-draft` only when the adapter needs to replace the drafted packet from a file rather than curating the existing draft in place.
