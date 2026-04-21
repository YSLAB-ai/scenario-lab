# Adapter Workflow V1 Design

## Summary

The next gap in the forecasting harness is no longer retrieval or revision storage. It is adapter ergonomics.

The current core is deterministic and reusable, but Codex and Claude adapters still need to manufacture temporary JSON files to:

- save intake drafts
- trim drafted evidence
- approve revisions
- start updated revisions from prior approved state

That friction is the main thing preventing the current workflow from feeling like a real conversational adapter layer.

This slice adds direct CLI surfaces for adapter-driven workflow operations while keeping the core deterministic and file-backed underneath.

## Goal

Enable Codex and Claude adapters to drive the guided forecasting workflow without hand-authoring temporary JSON files for common operations.

## Non-Goals

- no natural-language parsing inside the core
- no new simulation behavior
- no new retrieval algorithms
- no new domain-pack logic
- no attempt to make the CLI fully interactive on its own

## Product Boundary

The adapter still owns the conversation.

The CLI/core owns deterministic state transitions.

This slice improves the boundary between them by giving the adapter direct commands for the most common revision actions:

- create intake drafts from structured flags
- curate drafted evidence by selecting evidence ids
- approve revisions from structured flags
- fork a new revision from an approved prior revision

The JSON file path remains supported for compatibility and bulk editing, but it stops being the only practical adapter path.

## Design

### 1. Direct Intake Draft Inputs

`forecast-harness save-intake-draft` should support two modes:

- existing `--input <file>` mode
- new structured flag mode

Structured flag mode will accept:

- `--event-framing`
- repeated `--focus-entity`
- `--current-development`
- `--current-stage`
- `--time-horizon`
- repeated `--known-constraint`
- repeated `--known-unknown`
- repeated `--suggested-entity`
- repeated `--pack-field key=value`
- optional `--parent-revision-id`

If `--input` is supplied, the command behaves as it does today.

If `--input` is omitted, the command builds an `IntakeDraft` from flags and saves it through the existing workflow service.

`pack-field` values should be parsed deterministically:

- try JSON scalar parsing first
- otherwise treat the value as a string

This keeps pack-field typing compatible with the existing schema validation in the workflow service.

### 2. Evidence Curation Without File Rewrites

`forecast-harness curate-evidence-draft` should be added.

Purpose:
- load the current draft evidence packet for a revision
- keep only the explicitly selected `evidence_id` values
- preserve the original order of the retained items
- write the updated evidence draft back through the repository

Inputs:

- `--root`
- `--run-id`
- `--revision-id`
- repeated `--keep-evidence-id`

Behavior:

- fail if there is no draft evidence packet
- fail if any requested id is not present in the current draft
- overwrite the draft evidence packet with the curated selection
- append an `evidence-curated` event
- print the resulting packet as JSON

This command replaces the need for adapters to serialize a modified packet just to remove rejected items.

### 3. Direct Approval Inputs

`forecast-harness approve-revision` should also support two modes:

- existing `--input <file>` mode
- new structured flag mode

Structured flag mode will accept:

- repeated `--assumption`
- repeated `--suggested-actor`
- `--objective-profile-name`

If `--input` is present, existing behavior is unchanged.

If `--input` is absent, the command builds `AssumptionSummary` directly from flags and approves the revision through the workflow service.

### 4. Update Revisions From Prior Approved State

`forecast-harness begin-revision-update` should be added.

Purpose:
- create a new draft revision from a prior approved revision
- preserve lineage
- let the adapter continue the same run after new evidence or new developments

Inputs:

- `--root`
- `--run-id`
- `--parent-revision-id`
- `--revision-id`

Behavior:

- load approved intake and approved evidence from the parent revision
- save them as draft intake and draft evidence for the new revision
- create/update the new revision record with `parent_revision_id`
- append a `revision-update-started` event
- leave assumptions, belief-state, simulation, and report outputs unset for the new revision
- print a narrow JSON payload describing the new revision and copied sections

This matches the product direction already implied by revision lineage and reruns, but makes it usable from an adapter.

### 5. Backward Compatibility

Existing commands continue to work:

- `save-intake-draft --input ...`
- `save-evidence-draft --input ...`
- `approve-revision --input ...`

This slice is additive and should not break current smoke tests or existing users.

## Files and Responsibilities

- `packages/core/src/forecasting_harness/workflow/service.py`
  Add deterministic service methods for evidence curation and revision forking.
- `packages/core/src/forecasting_harness/cli.py`
  Add direct adapter-grade CLI inputs and the new update/curation commands.
- `packages/core/tests/test_workflow_service.py`
  Cover new service behavior.
- `packages/core/tests/test_cli_workflow.py`
  Cover direct-flag workflow paths and the new commands.
- `packages/core/tests/test_adapter_docs.py`
  Enforce the new adapter-facing command sequence.
- `docs/install-codex.md`
- `docs/install-claude-code.md`
- `adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md`
- `adapters/claude/skills/forecast-harness/SKILL.md`
- `README.md`
- `docs/status/2026-04-20-project-status.md`
  Refresh documentation to reflect the adapter-grade workflow.

## Error Handling

- reject mixed invalid flag/input combinations only when required fields are missing in flag mode
- reject unknown curated evidence ids with a clear error
- reject update forking when the parent revision lacks approved intake or approved evidence
- preserve path-safety and existing run/revision validation

## Testing

The main tests should prove:

- direct intake flags save a valid draft without an input file
- direct approval flags approve a revision without an input file
- evidence curation keeps only requested ids and records the event
- update forking copies approved intake/evidence into a new draft revision with parent lineage
- adapter/install docs mention the new commands and no longer imply that temp JSON files are required for routine adapter flow

## Outcome

After this slice, the harness will still be deterministic and file-backed internally, but the adapter path will be much closer to the intended product:

- conversational on the outside
- structured and deterministic underneath
- no temp JSON files for the normal guided workflow
