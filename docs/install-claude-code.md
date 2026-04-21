# Install in Claude Code

1. From the checked-out forecasting harness repo root, create and activate a Python 3.12+ virtualenv.
2. Run `pip install -e 'packages/core[dev]'`.
3. Copy `adapters/claude/skills/forecast-harness` into `.claude/skills/` for the target workspace or personal Claude directory.
4. Verify the shared CLI query-style commands are available:
   - `forecast-harness start-run --help`
   - `forecast-harness save-intake-draft --help`
   - `forecast-harness draft-intake-guidance --help`
   - `forecast-harness draft-conversation-turn --help`
   - `forecast-harness draft-evidence-packet --help`
   - `forecast-harness curate-evidence-draft --help`
   - `forecast-harness save-evidence-draft --help`
   - `forecast-harness draft-approval-packet --help`
   - `forecast-harness approve-revision --help`
   - `forecast-harness begin-revision-update --help`
   - `forecast-harness simulate --help`
   - `forecast-harness summarize-run --help`
   - `forecast-harness summarize-revision --help`
   - `forecast-harness generate-report --help`
5. Drive the workflow through the guided sequence rather than loading raw run artifacts into active context. For the normal adapter path, prefer direct structured input over temporary JSON files, and after each workflow mutation call `forecast-harness draft-conversation-turn` to decide the next user-facing step:
   - `forecast-harness start-run`
   - `forecast-harness save-intake-draft --event-framing ... --focus-entity ... --current-development ...`
   - `forecast-harness draft-conversation-turn`
   - `forecast-harness draft-intake-guidance`
   - `forecast-harness draft-evidence-packet`
   - `forecast-harness curate-evidence-draft`
   - `forecast-harness draft-conversation-turn`
   - `forecast-harness draft-approval-packet`
   - `forecast-harness approve-revision --assumption ...`
   - `forecast-harness draft-conversation-turn`
   - `forecast-harness simulate`
   - `forecast-harness draft-conversation-turn`
   - `forecast-harness summarize-revision`
   - `forecast-harness summarize-run`
   - `forecast-harness begin-revision-update`
6. Use `forecast-harness save-evidence-draft` only when the adapter needs to replace the drafted packet from a file rather than curating the existing draft in place.
