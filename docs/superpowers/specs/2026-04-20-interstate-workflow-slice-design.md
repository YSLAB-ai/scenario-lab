# Interstate Workflow Slice Design

Date: 2026-04-20

## Summary

This document defines the next milestone for the forecasting harness after the current core vertical slice. The goal of this milestone is to build the first real analyst workflow while preserving the existing architecture choice:

- `skill-driven conversation flow` for the user-facing experience
- `CLI/API core` for deterministic state transitions and durable artifacts

This milestone is intentionally workflow-first, but it is not domain-free. It uses one reference domain pack, `interstate crisis escalation`, to pressure-test the workflow with a real forecasting problem.

The workflow defined here is meant to be reusable across future domains. Domain packs should be able to replace:

- actor suggestions
- intake follow-up prompts
- evidence selection heuristics
- phase templates
- transition logic
- scoring logic

without changing the core run lifecycle, revision model, approval flow, or adapter/core boundary.

## Goal

Deliver the first usable forecasting workflow that can:

1. open a new run from a user’s crisis description
2. conduct structured but adaptive intake
3. draft a grouped assumption summary
4. retrieve and draft a grouped evidence packet from the local corpus
5. pause for grouped approval
6. compile an approved belief-state revision
7. run a simulation once
8. generate a scenario report
9. pause again if material new evidence emerges and create a revisioned rerun

## Non-Goals

This milestone does not attempt to deliver:

- multiple production-ready domain packs
- a high-fidelity war simulator
- automatic rule extraction from sources
- open-web retrieval
- simultaneous-move resolution
- full historical replay and calibration tooling
- a polished turnkey Codex or Claude marketplace integration

## Product Boundary

The adapter remains conversational. The core remains deterministic.

The workflow contracts in this milestone are intended to be domain-reusable. Interstate crisis is the first `reference validation pack`, not a special-case architecture.

The adapter is responsible for:

- natural-language questioning
- adaptive follow-up prompts
- drafting candidate third parties
- drafting an objective profile
- drafting grouped assumptions
- drafting grouped evidence packets
- presenting approvals and reports

The core is responsible for:

- opening runs
- creating and storing revisions
- persisting approved intake, evidence, and assumptions
- compiling belief-state snapshots
- running simulation
- producing reports and workbench outputs
- recording lifecycle events

The adapter may propose. The core records and executes.

That means a future domain pack such as `corporate strategic response` or `market shock` should reuse the same run lifecycle and revision machinery while swapping in different intake prompts, actors, evidence heuristics, and simulation logic.

## Reference Domain Pack

The first real workflow milestone is validated with `interstate crisis escalation`.

### Domain choice

This pack is the first reference pack because it matches the original project intent and forces the reusable workflow to handle:

- multiple strategic actors
- escalation and de-escalation
- signaling
- constraints
- negotiations
- material third parties

### Interaction model

`v1` uses:

- `event-driven` transitions
- `phase-based` progression
- same-epoch reactions represented through transition context

It does not implement full simultaneous-move resolution in this milestone.

### Actor granularity

`v1` models:

- primary states as actors
- major external states as optional actors when approved

It does not model domestic factions as separate actors in this milestone. Domestic politics, leader style, military posture, and institutional behavior remain state fields.

### Canonical phases

The first pack uses a fixed phase set:

- `trigger`
- `signaling`
- `limited-response`
- `escalation`
- `negotiation-deescalation`
- `settlement-stalemate`

These phases are canonical for `v1`, but they should remain owned by the domain pack so later versions can make them configurable.

## Workflow Architecture

The next milestone is a `balanced workflow slice`.

The workflow itself is generic. The interstate-crisis pack is the first pack used to validate that the workflow contracts are strong enough for a real forecasting problem.

### User-facing layer

Codex and Claude expose the system through a skill-driven conversation flow. The interaction should feel like an analyst workflow rather than a raw CLI prompt tree.

### Core layer

The core should expose explicit operations that the adapter calls. These operations may be implemented as CLI commands, Python API functions, or both, but they must remain deterministic and testable.

Recommended core operations:

- `start-run`
- `save-intake-draft`
- `save-evidence-draft`
- `approve-revision`
- `compile-belief-state`
- `simulate`
- `generate-report`

### Lifecycle

1. User describes a crisis.
2. Adapter opens a run.
3. Adapter drafts structured intake.
4. Adapter proposes material third parties and an objective profile.
5. Adapter drafts grouped assumptions.
6. Adapter retrieves candidate evidence from the local corpus and drafts one grouped evidence packet.
7. User approves the grouped intake summary, grouped assumptions, and grouped evidence packet.
8. Core compiles an approved belief-state revision.
9. Core simulates that revision and stores outputs.
10. Adapter presents the report.
11. If material new evidence appears, the workflow pauses, requests approval, creates a new revision, recompiles, and reruns.

## Structured Intake

The workflow is `structured but adaptive`.

That means required sections are fixed, while the follow-up questions inside those sections can vary by event and by domain-pack logic.

### Required intake sections

- `event framing`
- `primary actors`
- `trigger`
- `current phase`
- `time horizon`
- `known constraints`
- `known unknowns`

These are workflow-level sections. Future domain packs may reinterpret their contents, but should not need a different approval lifecycle.

### Adaptive follow-ups

Domain packs may insert adaptive follow-ups. For the interstate-crisis reference pack, examples include:

- suggested third parties
- leader style prompts
- institutional behavior prompts
- escalation sensitivity prompts
- capability gaps

### Third parties

Third parties are optional input fields, but the adapter should proactively suggest them when materially relevant. For example, in a US-Iran crisis, the system may suggest actors such as China, Israel, Gulf states, or Russia.

Suggested third parties are `draft actors` until the user approves them.

### Objective profile

The user does not choose an objective profile from scratch. Instead:

- the adapter drafts one
- `balanced` is the default fallback
- the grouped approval step shows the draft
- the user can approve or edit it

## Assumption Approval

Assumptions are approved as a grouped summary.

`v1` does not require one-by-one approval. The grouped summary should include:

- high-level assumptions inferred from the event framing
- assumptions about actor intent or behavior
- assumptions caused by missing evidence
- the drafted objective profile
- suggested third-party inclusions

The approved assumption set becomes part of the revision snapshot.

## Evidence Flow

Evidence is approved as `one grouped packet`, not split into multiple separate approval sections.

### Retrieval model

The adapter retrieves candidate documents and passages from the local corpus after intake drafting. It then creates a grouped evidence packet for user approval.

This retrieval-and-approval flow is reusable across domains. Only the retrieval heuristics and ranking criteria should vary by domain pack.

### Packet sizing

Packet size is adaptive. The adapter and domain pack may adjust packet size based on:

- event scope
- number of material actors
- current phase
- time horizon
- uncertainty level
- source diversity

`v1` should still enforce guardrails:

- minimum and maximum packet size
- source balancing
- maximum passages per source

### Approval model

The user sees a summarized grouped packet for approval, but the core stores and reasons over the raw approved passages.

Each grouped packet item should expose:

- source title
- short reason for inclusion
- passage count
- citation identifiers or links

The user can:

- approve the packet
- remove items
- request expansion

### Dynamic evidence expansion

The system may continue retrieving and proposing evidence during the same run. However, it must not silently mutate the approved evidence basis during an active analysis pass.

If material new evidence is discovered:

1. analysis pauses
2. the adapter presents an added grouped evidence packet
3. the user approves or rejects it
4. the core creates a new evidence revision
5. the belief state is recompiled
6. simulation reruns, using warm-start reuse when compatible

## Run Artifacts and Revision Model

This milestone extends the current artifact model into a revisioned run record.

The artifact model is intentionally domain-neutral.

Each run should contain:

- `run.json`
- `intake/`
- `evidence/`
- `assumptions/`
- `belief-state/`
- `simulation/`
- `reports/`
- `events.jsonl`

### Artifact responsibilities

- `run.json`
  Stable metadata such as run id, domain pack, created time, and current revision id.
- `intake/`
  Structured intake drafts and approved snapshots.
- `evidence/`
  Proposed packets, approved packets, and rejected items by revision.
- `assumptions/`
  Draft grouped summaries and approved grouped summaries.
- `belief-state/`
  Compiled snapshots by revision.
- `simulation/`
  Tree configuration, compatibility records, summaries, and cache metadata.
- `reports/`
  Scenario reports and workbench outputs by revision.
- `events.jsonl`
  Append-only lifecycle log for auditability.

### Revision rule

Approved snapshots are immutable. New information creates a new revision rather than overwriting prior approved state.

Example progression:

- `r1`: intake approved
- `r2`: evidence packet approved
- `r3`: first simulation and report
- `r4`: new evidence approved after pause
- `r5`: rerun after revision

## Simulation Behavior

Simulation may run only from an approved revision.

The report should not block low-evidence cases, but it must explain their credibility limits directly.

### Inputs to simulation

The approved simulation input includes:

- approved intake summary
- approved grouped assumptions
- approved objective profile
- approved evidence packet
- compiled belief-state snapshot

### Scalarization

The simulation engine still scores leaves as vectors, but branch selection and backpropagation require scalarization. The approved objective profile determines how that scalarization is applied.

### Mid-analysis evidence updates

If material new evidence emerges while analysis is underway:

- pause
- request approval
- create a new revision
- recompile the belief state
- rerun with warm-start reuse when compatible

## Reporting

Every report should include:

- ranked scenario branches or families
- main drivers
- approved assumptions
- evidence coverage and gaps
- credibility and uncertainty notes
- variables or evidence that would most change the result

The report should communicate:

- what was approved
- what was inferred
- what remains weakly supported
- what changed across revisions

The report remains the user-facing output. The workbench remains the analyst-facing trace.

## Core Operations for This Milestone

The current core has a minimal CLI. This milestone should add deterministic operations sufficient for the new workflow slice.

Suggested operation set:

- `start-run`
  Create a run and initialize metadata.
- `save-intake-draft`
  Store normalized intake and adaptive draft fields.
- `save-evidence-draft`
  Store grouped evidence packet proposals.
- `approve-revision`
  Freeze approved intake, assumptions, objective profile, and evidence for a revision.
- `compile-belief-state`
  Compile the approved inputs into a structured belief-state snapshot.
- `simulate`
  Run the selected domain pack over the approved snapshot.
- `generate-report`
  Write report and workbench outputs for that revision.

These operations may be exposed via CLI subcommands, Python APIs, or both. The important requirement is that they remain deterministic and testable outside the agent layer.

## Error Handling

This milestone should explicitly handle:

- unsupported or ambiguous phase selection
- missing required intake fields
- suggested third parties rejected by the user
- empty approved evidence sets
- material new evidence discovered mid-analysis
- incompatible rerun state for warm-start reuse

The system must allow low-evidence runs, but the report must surface:

- evidence coverage
- unsupported assumptions
- missing critical variables

## Testing Strategy

The next implementation plan should include tests for:

- structured intake normalization
- grouped assumption approval
- grouped evidence packet approval
- revision creation and immutability
- reference-pack canonical phase handling
- suggested third-party drafting and approval
- approved objective profile persistence
- pause-and-rerun behavior for material new evidence
- report generation with coverage and credibility notes
- adapter-to-core boundaries that keep state transitions deterministic

It should also include at least one check that the workflow contracts remain domain-neutral at the core layer, with interstate-specific behavior confined to the reference pack and adapter prompts.

## Success Criteria

This milestone succeeds when a user can:

1. describe an interstate crisis in natural language through the adapter
2. go through structured but adaptive intake
3. approve grouped assumptions and one grouped evidence packet
4. receive a scenario report from an approved revision
5. approve newly surfaced material evidence
6. receive a revisioned rerun without losing audit history

## Why This Is the Next Solid Step

This milestone is the strongest next step because it validates the real product shape:

- conversational workflow
- deterministic core
- revisioned evidence and assumptions
- one serious reference domain

It avoids two failure modes:

- deepening domain knowledge before the workflow is real
- building a generic workflow with no domain pressure

This milestone establishes the reusable harness. Later domain packs and richer knowledge work can then plug into something operational instead of something hypothetical.
