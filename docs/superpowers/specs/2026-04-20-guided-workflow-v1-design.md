# Guided Workflow V1 Design

Date: 2026-04-20

## Summary

This milestone adds the first adapter-facing workflow guidance layer on top of the deterministic forecasting core.

Verified current baseline on `codex/corpus-ingestion-v1`:

- the core already supports run creation, revision storage, intake drafts, evidence drafts, approval, simulation, and report generation
- the core already supports local corpus ingestion and retrieval-backed evidence drafting
- the adapters are still mostly installation notes plus raw CLI primitives
- users still need to hand-author JSON artifacts if they want to drive the workflow directly through the CLI

The goal of this milestone is not to make the core conversational. The goal is to expose deterministic guidance and summary commands that a Codex or Claude adapter can call to drive the workflow without loading whole artifacts or inventing its own workflow logic.

## Goal

Deliver an adapter-guidance milestone that:

1. drafts pack-driven intake guidance from a saved intake draft
2. drafts a grouped approval packet from saved intake and evidence drafts
3. exposes narrow run/revision summaries for progressive disclosure
4. updates adapter docs and skills to use these new deterministic commands

## Non-Goals

This milestone does not attempt to deliver:

- a fully conversational in-repo agent
- any direct LLM integration in the core package
- auto-approval or autonomous forecasting decisions
- MCTS or simulation realism improvements
- new domain packs

## Why This Milestone Exists

The architecture has been consistent from the start:

- conversational adapters on top
- deterministic core underneath

The deterministic core is now strong enough that the main remaining UX gap is orchestration.

Right now, adapters still have to:

- infer pack questions themselves
- infer suggested third parties themselves
- infer grouped approval structure themselves
- read raw run artifacts directly when answering follow-up questions

That duplicates core knowledge and pushes too much logic into prompts. This milestone moves that guidance into explicit core commands instead.

## Chosen Approach

This milestone uses `deterministic guidance artifacts on demand`.

That means:

- no new persisted source of truth beyond the existing run/revision artifacts
- guidance and summaries are computed from existing saved drafts and approved snapshots
- adapters can call query-style commands to get narrow JSON outputs

This is preferred over:

- making the adapters parse raw JSON files directly
- persisting a second set of transient “draft helper” artifacts unless needed
- trying to add an LLM-driven conversation framework inside the package

## Product Boundary

After this milestone, the adapter should be able to do the following without re-implementing workflow logic:

1. save a first intake draft
2. ask the core for intake guidance
3. revise intake if needed
4. ask the core to draft evidence from the corpus
5. ask the core for a grouped approval packet
6. present that packet to the user
7. approve and simulate
8. ask the core for narrow run summaries in later follow-up questions

The adapter still owns the conversation. The core owns the workflow structure.

## Intake Guidance

The first new surface should be a deterministic `intake guidance` payload.

### Inputs

- `run_id`
- `revision_id`

### Derived from

- the saved intake draft
- the selected domain pack

### Output fields

The intake guidance payload should include:

- `domain_pack`
- `current_stage`
- `canonical_stages`
- `suggested_entities`
- `follow_up_questions`
- `pack_field_schema`
- `default_objective_profile`

### Purpose

This payload lets the adapter ask the right follow-up questions and suggest material entities without re-encoding pack-specific logic.

For example, the interstate pack can drive:

- suggested outside actors
- known stage vocabulary
- pack-specific follow-up questions
- pack field prompts such as `military_posture` and `leader_style`

## Grouped Approval Packet

The second new surface should be a deterministic grouped approval packet.

### Inputs

- `run_id`
- `revision_id`

### Derived from

- the saved intake draft
- the saved evidence draft
- the selected domain pack’s default objective profile

### Output fields

The grouped approval packet should include:

- `revision_id`
- `intake_summary`
- `assumption_summary`
- `objective_profile`
- `evidence_summary`
- `warnings`

### Intake summary

The intake summary should restate only the important workflow fields:

- event framing
- focus entities
- current development
- current stage
- time horizon
- known constraints
- known unknowns

### Assumption summary

The assumption summary does not need to claim deep reasoning. It should be deterministic and transparent, for example:

- unsupported areas inferred from `known_unknowns`
- explicit mention when evidence count is zero
- mention of suggested entities that are outside the current focus set

This is enough to give the adapter a grouped approval baseline that the user can edit.

### Objective profile

The approval packet should expose the pack’s default objective profile as the draft default, including:

- profile name
- metric weights
- veto thresholds
- risk tolerance

That gives the adapter something explicit to show the user rather than silently assuming `balanced`.

### Evidence summary

The evidence summary should avoid loading whole raw passages into active context. It should summarize each evidence item with:

- `evidence_id`
- `source_id`
- `source_title`
- `reason`
- `passage_count`

The raw passage text remains in the saved evidence artifact and is still available when needed.

### Warnings

Warnings should be deterministic. Examples:

- no evidence drafted yet
- no suggested entities approved yet
- known unknowns remain unresolved

These warnings should not block the run. They are visibility, not policy gates.

## Run and Revision Summaries

The third new surface should be narrow summary commands for progressive disclosure.

### Required summaries

- `summarize-run`
- `summarize-revision`

### `summarize-run`

This should include:

- `run_id`
- `domain_pack`
- `current_revision_id`
- ordered revision list with statuses

### `summarize-revision`

This should include:

- `revision_id`
- revision status
- parent revision id
- evidence item count
- assumption count
- top branches if simulation exists
- available artifact sections

This is the core-friendly version of “what changed?” and “where is this run now?” without forcing adapters to load large raw artifacts.

## Persistence Model

These guidance and summary payloads should be computed on demand, not persisted as new source-of-truth artifacts in `v1`.

Reasoning:

- they are derived from existing saved artifacts
- they can be regenerated deterministically
- they should not create a second workflow history that can drift from the real run state

The existing persisted artifacts remain:

- run records
- revision records
- intake drafts and approvals
- evidence drafts and approvals
- approved assumptions
- compiled belief states
- simulation outputs
- reports

## CLI Surface

This milestone should add:

- `forecast-harness draft-intake-guidance`
- `forecast-harness draft-approval-packet`
- `forecast-harness summarize-run`
- `forecast-harness summarize-revision`

All four should return JSON payloads intended for adapter use.

## Query API

The existing `query_api.py` already exposes narrow branch and evidence helpers. This milestone should extend that style, not replace it.

The new summary/guidance code may live in the workflow service or query helpers, but the public behavior should stay consistent:

- narrow deterministic outputs
- no raw artifact flooding
- no hidden inference beyond documented deterministic rules

## Adapter Docs

The Codex and Claude adapter docs and skill stubs should be updated to recommend the new command sequence:

1. `start-run`
2. `save-intake-draft`
3. `draft-intake-guidance`
4. `draft-evidence-packet`
5. `draft-approval-packet`
6. `approve-revision`
7. `simulate`
8. `summarize-run` or `summarize-revision` for follow-ups

This is the first point where the adapter docs can describe a guided workflow rather than only a raw artifact workflow.

## Testing

This milestone should add tests for:

- intake guidance output from saved intake drafts
- approval packet generation with and without evidence
- run summary for revision lineage
- revision summary for simulated and unsimulated revisions
- CLI coverage for the new commands
- adapter docs mentioning the new guided sequence

The full existing suite should remain green.

## Out of Scope but Preserved

This milestone should leave room for:

- richer assumption-drafting logic later
- LLM-authored approval packet edits in adapters
- interactive thread-native adapters in Codex and Claude
- diff-style revision summaries
- material-change detection for update interruptions

The purpose of `v1` is to make the adapters thin and consistent, not to make the core “smart” in a new way.
