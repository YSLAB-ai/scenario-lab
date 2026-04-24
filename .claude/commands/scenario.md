---
allowed-tools: Bash(test:*), Bash(scenario-lab:*), Bash(packages/core/.venv/bin/scenario-lab:*)
description: Start a Scenario Lab run from a natural-language scenario question
---

Start a Scenario Lab run for this user request: `$ARGUMENTS`

Workflow:

1. Use `packages/core/.venv/bin/scenario-lab` if it exists in the current repository. Otherwise use `scenario-lab` from `PATH`.
2. Run the CLI bootstrap with the user's text:
   - `packages/core/.venv/bin/scenario-lab scenario --root .forecast "/scenario $ARGUMENTS"`
   - or `scenario-lab scenario --root .forecast "/scenario $ARGUMENTS"`
3. Read the JSON output and summarize:
   - run id
   - inferred domain pack
   - inferred actors
   - current workflow stage
   - next recommended action
4. If the user asks you to continue into evidence collection, use `.forecast/corpus.db` as the default corpus. Save gathered evidence files under `.forecast/evidence-candidates/`, run `scenario-lab run-adapter-action --root .forecast --candidate-path .forecast/evidence-candidates --run-id <run-id> --revision-id r1 --action batch-ingest-recommended`, then run `scenario-lab run-adapter-action --root .forecast --run-id <run-id> --revision-id r1 --action draft-evidence-packet`.
5. Stop after the bootstrap summary unless the user explicitly asks you to continue into evidence collection, approval, or simulation.
