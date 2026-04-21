# Native Adapter Loop V1 Implementation

Date: 2026-04-20

## Scope

Implement the native adapter loop on top of the existing deterministic workflow surfaces.

## Steps

1. Extend workflow models with an adapter action type and add ordered actions to `ConversationTurn`.
2. Update `WorkflowService.draft_conversation_turn(...)` to:
   - accept an optional candidate directory
   - embed evidence-stage planning payloads when a corpus registry is available
   - emit ordered actions and a default next command for every stage
3. Extend the CLI `draft-conversation-turn` command with:
   - optional `--corpus-db`
   - optional `--candidate-path`
4. Add focused tests for:
   - adapter action model serialization
   - service-level evidence-stage native loop payloads
   - CLI-level evidence-stage native loop payloads
5. Update README, install notes, skills, and the status note to describe the native loop.
6. Verify with:
   - focused tests
   - full test suite
   - direct CLI smoke run with a corpus database and candidate directory
