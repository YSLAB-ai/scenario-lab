# Native Adapter Loop V1 Design

Date: 2026-04-20

## Goal

Promote `forecast-harness draft-conversation-turn` into the single native adapter query surface after each workflow mutation so Codex and Claude adapters no longer need to manually sequence planning commands.

## Scope

- Extend `ConversationTurn` with ordered next-step actions.
- Let evidence-stage turns embed the deterministic planning payloads adapters already need:
  - `intake_guidance`
  - `retrieval_plan`
  - `ingestion_plan`
  - `ingestion_recommendations` when a local candidate directory is provided
- Preserve the existing stage-resolution behavior and top-level compatibility fields already consumed by tests.
- Keep the loop deterministic and local-only.

## Design

`draft-conversation-turn` remains the adapter entrypoint. The adapter calls it after each mutation and treats:

- `recommended_command` as the default next command
- `actions` as the ordered allowed next steps
- `context` as the only narrow payload the adapter needs to render the next user-facing turn

Evidence stage is the main change. When the service has a corpus registry, it derives retrieval and ingestion planning from the approved intake. When the caller also provides a candidate directory, the service evaluates those local files and adds ranked ingestion recommendations. If recommendations exist, the default next action becomes `forecast-harness batch-ingest-recommended`; otherwise it stays `forecast-harness draft-evidence-packet`.

Other stages gain ordered actions as well, but keep their previous narrow payloads:

- `intake` -> `save-intake-draft`
- `approval` -> `approve-revision`
- `simulation` -> `simulate`
- `report` -> `begin-revision-update`

## Non-Goals

- No automatic execution of the returned actions inside the core.
- No new plugin runtime or background orchestration layer.
- No change to the underlying deterministic workflow transitions.
