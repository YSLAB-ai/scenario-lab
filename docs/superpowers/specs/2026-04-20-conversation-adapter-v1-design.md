# Conversation Adapter V1 Design

## Summary

The harness now has:

- revisioned workflow state
- guided intake and approval payloads
- direct structured adapter inputs
- evidence curation and revision updates

But the adapters still do not have a single deterministic answer to the question:

`what should I ask or show the user next?`

That is the missing piece between the current CLI/core and a real conversation/approval workflow.

## Goal

Add a deterministic conversation-turn surface that tells a Codex or Claude adapter what stage a run/revision is in, what the adapter should present next, and which core command should follow.

## Non-Goals

- no natural-language generation inside the core beyond short deterministic summaries
- no autonomous decisions without user approval
- no new simulation behavior
- no new retrieval behavior
- no new domain-pack logic

## Product Boundary

The adapter still owns the actual conversation wording and turn-taking.

The core should provide:

- current workflow stage
- narrow structured payload for that stage
- concise user-facing summary text
- the next deterministic command/action the adapter should drive

That means the adapter no longer needs to infer stage from raw files or invent its own workflow state machine.

## Design

### 1. Conversation Turn Model

Add a new workflow payload model, `ConversationTurn`.

It should include:

- `run_id`
- `revision_id`
- `stage`
- `headline`
- `user_message`
- `recommended_command`
- `available_sections`
- `context`

`stage` should be one of a small deterministic set:

- `intake`
- `evidence`
- `approval`
- `simulation`
- `report`

`context` is stage-specific JSON-friendly data that the adapter can use to render a better response without loading raw artifacts.

### 2. Stage Resolution Rules

The workflow service should determine the current stage from revision artifacts in this order:

1. If a simulation exists for the revision:
   - stage = `report`
   - payload should include `RevisionSummary`
   - `recommended_command` = `forecast-harness begin-revision-update` for follow-on changes, or none if the adapter is only showing the report

2. Else if approved assumptions exist:
   - stage = `simulation`
   - payload should summarize approved evidence count and assumptions count
   - `recommended_command` = `forecast-harness simulate`

3. Else if draft evidence exists:
   - stage = `approval`
   - payload should include the existing `ApprovalPacket`
   - `recommended_command` = `forecast-harness approve-revision`

4. Else if draft intake exists:
   - stage = `evidence`
   - payload should include the existing `IntakeGuidance`
   - `recommended_command` = `forecast-harness draft-evidence-packet`

5. Else:
   - stage = `intake`
   - payload should tell the adapter the revision exists but intake is missing
   - `recommended_command` = `forecast-harness save-intake-draft`

This should be deterministic and only depend on stored run/revision artifacts.

### 3. User Message Content

The core should not try to be conversational in style, but it should give the adapter a concise stage message.

Examples:

- `evidence`:
  `Intake draft saved. Review suggested entities and follow-up questions, then draft evidence.`

- `approval`:
  `Evidence draft is ready. Review warnings, assumptions, and evidence summary before approval.`

- `simulation`:
  `Revision is approved and ready to simulate.`

- `report`:
  `Simulation is complete. Review the top branches and decide whether to update the revision.`

These are deterministic summaries, not freeform chat.

### 4. CLI Surface

Add:

- `forecast-harness draft-conversation-turn`

Inputs:

- `--root`
- `--run-id`
- `--revision-id`

Output:

- JSON serialization of `ConversationTurn`

This becomes the primary adapter query after each workflow mutation.

### 5. Adapter Docs

The Codex and Claude adapter docs should shift from “remember this whole workflow” to:

1. mutate state with the appropriate command
2. call `forecast-harness draft-conversation-turn`
3. show the returned summary and stage-specific context
4. ask for approval or the next user input

This is the first point where the adapter can behave like a real workflow guide instead of a bundle of remembered CLI steps.

## Files and Responsibilities

- `packages/core/src/forecasting_harness/workflow/models.py`
  Add `ConversationTurn`.
- `packages/core/src/forecasting_harness/workflow/service.py`
  Add deterministic stage resolution and turn drafting.
- `packages/core/src/forecasting_harness/cli.py`
  Expose `draft-conversation-turn`.
- `packages/core/tests/test_workflow_models.py`
- `packages/core/tests/test_workflow_service.py`
- `packages/core/tests/test_cli_workflow.py`
  Cover the new model, service logic, and CLI command.
- `packages/core/tests/test_adapter_docs.py`
- `docs/install-codex.md`
- `docs/install-claude-code.md`
- `adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md`
- `adapters/claude/skills/forecast-harness/SKILL.md`
- `README.md`
- `docs/status/2026-04-20-project-status.md`
  Refresh adapter guidance and verified status.

## Error Handling

- if the run or revision does not exist, propagate the existing repository error
- if only partial stage data exists, resolve to the earliest valid stage instead of guessing
- never inspect raw report Markdown to infer stage; use structured artifacts only

## Testing

The main tests should prove:

- model serialization for `ConversationTurn`
- service stage resolution for:
  - intake missing
  - evidence stage
  - approval stage
  - simulation stage
  - report stage
- CLI command returns the correct stage payload for a real run
- adapter docs mention `draft-conversation-turn` as the stage-resolution step

## Outcome

After this slice, the harness still will not be a fully polished installed conversational product, but it will finally have a deterministic conversation state machine for adapters.

That is the minimum missing layer for “conversation/approval-based analysis” to work as an actual workflow rather than a manual sequence of remembered commands.
