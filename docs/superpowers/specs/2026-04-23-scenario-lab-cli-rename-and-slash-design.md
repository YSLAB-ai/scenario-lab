# Scenario Lab CLI Rename And Slash Bootstrap Design

## Goal

Make the repo consistent with the public `Scenario Lab` name in the shipped code and adapter bundles, and add a verified slash-style bootstrap entrypoint so a user can start a workflow with `/scenario <prompt>` instead of hand-assembling the first runtime actions.

## Verified Current State

- The public repo/docs are branded `Scenario Lab`, but the shipped code surface is still `forecast-harness`.
- The installed CLI command is still `forecast-harness` in [packages/core/pyproject.toml](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/pyproject.toml).
- The Python distribution name is still `forecasting-harness` and the internal module path is still `forecasting_harness`.
- The Codex and Claude adapter bundles are still named `forecast-harness`:
  - [adapters/codex/forecast-harness/adapter.json](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/adapters/codex/forecast-harness/adapter.json)
  - [adapters/claude/forecast-harness/adapter.json](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/adapters/claude/forecast-harness/adapter.json)
- The shipped Codex plugin manifest does not declare any slash-command registration field:
  - [adapters/codex/forecast-harness/.codex-plugin/plugin.json](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/adapters/codex/forecast-harness/.codex-plugin/plugin.json)
- The current adapter runtime is driven through `run-adapter-action`, and the real workflow phases are still:
  - `intake -> evidence -> approval -> simulation -> report`
- The existing workflow already exposes the primitives needed to bootstrap a run:
  - `start-run`
  - `draft-intake-guidance`
  - `save-intake-draft`
  - `draft-conversation-turn`
  - `run-adapter-action`

## Problem

The repo currently has a public-facing name and a different shipped command/bundle name. That inconsistency leaks into:

- install docs
- adapter bundle names
- skill docs
- test expectations
- CLI examples

At the same time, the desired `/scenario <prompt>` interaction does not currently exist. It also cannot be honestly claimed as a native Codex/Claude slash command, because the shipped bundle manifests do not expose a verified slash registration mechanism.

## Requirements

### User-facing consistency

The shipped product surface should use `scenario-lab` instead of `forecast-harness` for:

- CLI command examples
- package script entrypoint
- adapter bundle names
- adapter install targets
- adapter README/skill guidance
- current tests that validate these user-facing surfaces

### Internal stability

The internal Python module path should remain `forecasting_harness` for this pass.

Reason:

- it is deeply wired into the codebase and tests
- changing it would create a much larger refactor than the user-facing rename requires
- the user request is to make the code surface consistent, not to rewrite all import paths

### Slash-style bootstrap

The repo should support a slash-style start command using the real workflow engine:

- user input form: `/scenario <prompt>`
- implementation form: a repo-owned CLI/runtime path, not a fake manifest-native slash claim

The slash bootstrap must be built from the existing workflow service, not a parallel workflow implementation.

## Design Decisions

### 1. Rename the shipped command to `scenario-lab`

Change the package metadata so the installed console script becomes:

- `scenario-lab`

The internal module remains:

- `forecasting_harness`

This keeps the public surface consistent while avoiding a broad import-path migration.

### 2. Rename the shipped adapter bundles to `scenario-lab`

Rename the live adapter bundle directories and manifests from `forecast-harness` to `scenario-lab`:

- Codex bundle directory
- Claude bundle directory
- adapter `name` fields
- install targets
- skill directory names

The bundle content should then consistently tell users to run `scenario-lab ...`.

### 3. Add a repo-level slash bootstrap command

Add a new CLI command that accepts a slash-style prompt:

- `scenario-lab scenario --root ... --run-id ... "/scenario how would US-Iran conflict at the Strait of Hormuz develop for the next 30 days"`

Behavior:

1. validate that the input starts with `/scenario`
2. extract the natural-language prompt
3. create the run if needed
4. derive the initial intake guidance from the existing workflow/domain defaults
5. save a best-effort intake draft from the prompt using the existing guidance path
6. return the normal adapter-style turn payload so the workflow continues through the real runtime

This is a slash-style entrypoint implemented by the repo, not a claim that Codex/Claude natively register `/scenario`.

### 4. Use the existing workflow service, not a parallel engine

The new slash bootstrap should be a thin orchestration layer over existing behavior:

- reuse `start_run`
- reuse `draft_intake_guidance`
- reuse `save_intake_draft`
- reuse `draft_conversation_turn`

This keeps one source of truth for the workflow.

### 5. Prompt parsing stays intentionally narrow in v1

The slash bootstrap should not attempt a full LLM-like semantic intake parser.

For v1 it should:

- require `--domain-pack`
- treat the prompt text as `event_framing`
- use existing guidance/defaults for the rest
- derive a simple `current_development` string from the prompt text
- default the phase to the first canonical stage for the selected pack
- leave evidence/assumptions to the normal later workflow steps

This is enough to make `/scenario <prompt>` real without inventing a second intake system.

## Approach Options Considered

### Option A: Full internal rename

Rename:

- package name
- module path
- imports
- tests
- bundles
- docs

Rejected for this pass.

Reason:

- much larger blast radius
- not required to make the user-facing product consistent
- higher regression risk with little user benefit

### Option B: User-facing rename only

Rename the command/bundles/docs, keep the internal module path stable.

Accepted as the base of the design.

Reason:

- gives the user-visible consistency they asked for
- keeps the implementation tractable

### Option C: User-facing rename plus slash bootstrap

Build Option B, then add a repo-owned `/scenario <prompt>` bootstrap.

Accepted.

Reason:

- matches the desired interaction model
- can be implemented honestly with the current runtime
- does not require native slash-manifest support

## File Areas Expected To Change

### Package metadata / entrypoint

- [packages/core/pyproject.toml](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/pyproject.toml)

### CLI/runtime

- [packages/core/src/forecasting_harness/cli.py](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/src/forecasting_harness/cli.py)
- [packages/core/src/forecasting_harness/workflow/service.py](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/src/forecasting_harness/workflow/service.py)
- possibly [packages/core/src/forecasting_harness/workflow/models.py](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/src/forecasting_harness/workflow/models.py) if the slash bootstrap needs a typed payload

### Adapter bundles

- `adapters/codex/forecast-harness/...` -> renamed `adapters/codex/scenario-lab/...`
- `adapters/claude/forecast-harness/...` -> renamed `adapters/claude/scenario-lab/...`
- legacy `adapters/claude/skills/forecast-harness/SKILL.md` may also need to move or be retired if it is still part of the live install path

### Public/current docs

- [README.md](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/README.md)
- [docs/quickstart.md](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/docs/quickstart.md)
- [docs/natural-language-workflow.md](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/docs/natural-language-workflow.md)
- [docs/install-codex.md](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/docs/install-codex.md)
- [docs/install-claude-code.md](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/docs/install-claude-code.md)

### Live tests

- adapter package tests
- adapter docs tests
- adapter runtime CLI tests
- public release docs tests
- any CLI tests that assert the old command name

Historical status/spec docs do not need a mass rewrite, because they document prior states.

## Testing Requirements

At minimum, the implementation must re-verify:

- package CLI tests
- adapter package install tests
- adapter docs tests
- adapter runtime CLI tests
- public release docs tests
- Codex bundle smoke
- Claude bundle smoke

And a direct slash bootstrap smoke should verify:

1. `/scenario <prompt>` is accepted
2. the run is created
3. the returned turn is in the real workflow
4. the workflow can continue through evidence/approval/simulation/report without a parallel path

## Non-Goals

This pass does not:

- rename the internal Python module path away from `forecasting_harness`
- claim native Codex or Claude slash-command registration without verified manifest support
- build a full natural-language intake parser

## Recommended Implementation Order

1. rename package entrypoint and current docs to `scenario-lab`
2. rename adapter bundles/manifests/install targets
3. add the slash bootstrap command
4. update tests
5. run adapter smokes and CLI verification

