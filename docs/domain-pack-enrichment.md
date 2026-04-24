# How To Improve A Domain Pack

This guide is for AI agents and human contributors who want to improve Scenario Lab's domain knowledge without bypassing the protected replay and evolution workflow.

Use this when a run exposes a thin domain pack: weak actor coverage, missing evidence categories, poor branch differentiation, replay misses, or action labels that do not cover the case well.

## Core Rule

Improve one domain at a time, and prove that the change does not regress replay behavior.

Do not edit shared simulation code to force a desired outcome. Domain enrichment should normally happen through:

- approved evidence compiled from a real run
- replay-miss analysis
- `knowledge/domains/<domain>.json` manifest overlays
- `knowledge/replays/<domain>.json` replay cases
- domain-pack code only when the pack lacks a needed state field, action, transition, or scoring rule

## Safe Workflow

1. Identify the domain slug.

   ```bash
   scenario-lab list-domain-packs
   ```

2. Run or inspect the scenario that exposed the thin domain.

   The normal workflow is still:

   ```text
   intake -> evidence -> approval -> simulation -> report
   ```

   Do not enrich from unsupported assumptions alone. Prefer approved evidence, replay cases, or clearly documented user suggestions.

3. Compile reusable knowledge from an approved revision.

   Use this after a run has an approved revision with evidence:

   ```bash
   scenario-lab compile-revision-knowledge \
     --workspace-root . \
     --root .forecast \
     --run-id <run-id> \
     --revision-id <revision-id>
   ```

   This records candidate evidence terms, semantic aliases, and action-bias suggestions through the domain-evolution store. It does not rewrite the pack directly.

4. Compile knowledge from replay misses.

   Use this when replay calibration or a specific replay case shows a miss:

   ```bash
   scenario-lab compile-replay-knowledge \
     --workspace-root . \
     --domain-pack <domain-slug>
   ```

5. Inspect the weakness report and stored suggestions.

   ```bash
   scenario-lab analyze-domain-weakness \
     --workspace-root . \
     --domain-pack <domain-slug>

   scenario-lab summarize-domain-evolution \
     --workspace-root . \
     --domain-pack <domain-slug>
   ```

6. Try protected retuning before manual edits.

   ```bash
   scenario-lab run-replay-retuning \
     --workspace-root . \
     --domain-pack <domain-slug> \
     --no-branch
   ```

   If the summary rejects promotion or reports no candidate changes, do not force a manifest edit. Add better evidence, add or repair replay coverage, or inspect whether the domain pack needs a real code-level capability.

7. Promote only non-regressing domain changes.

   To let the protected evolution workflow create a domain-only branch:

   ```bash
   scenario-lab run-domain-evolution \
     --workspace-root . \
     --domain-pack <domain-slug>
   ```

   To test without branch creation:

   ```bash
   scenario-lab run-domain-evolution \
     --workspace-root . \
     --domain-pack <domain-slug> \
     --no-branch
   ```

8. Verify the repo after changes.

   ```bash
   PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest packages/core -q
   scenario-lab summarize-replay-calibration
   scenario-lab run-builtin-replay-retuning --workspace-root /tmp/scenario-lab-retuning --no-branch
   ```

## When Manual Edits Are Justified

Use manual edits only when the protected compiler/evolution path cannot express the needed domain knowledge.

Good reasons to edit a domain pack:

- a missing state field is needed for many cases in that domain
- an action should exist but the pack cannot propose it
- a transition should route to a different phase or outcome family
- a scoring rule misses a real negative consequence
- actor-impact scoring lacks a domain-specific pressure that affects branch ranking

Files to inspect first:

- `knowledge/domains/<domain-slug>.json`
- `knowledge/replays/<domain-slug>.json`
- `packages/core/src/forecasting_harness/domain/<domain_module>.py`
- `packages/core/tests/test_*domain*`
- `packages/core/tests/test_replay*.py`

If you edit pack code, add or update replay coverage and targeted tests in the same change. The goal is not to make one demo look better; the goal is to make the domain pack more generally useful.

## What To Avoid

- Do not tune scores only to make one public demo rank first.
- Do not add unsupported geopolitical, market, legal, or operational claims without evidence or replay context.
- Do not weaken calibration or replay assertions to hide a miss.
- Do not edit shared simulation code for a domain-specific issue.
- Do not merge domain changes until replay, calibration, and targeted tests have been run.

## Agent Prompt

If you hand this repo to another AI agent, use a prompt like:

```text
Improve the <domain-slug> domain pack using the protected enrichment workflow.
Follow docs/domain-pack-enrichment.md.
Start by inspecting the domain manifest, replay cases, and calibration summary.
Use compile-revision-knowledge or compile-replay-knowledge if there is approved evidence or a replay miss.
Prefer manifest/replay improvements before domain-pack code.
Do not edit shared simulation code.
Run targeted tests, the full packages/core suite, summarize-replay-calibration, and run-builtin-replay-retuning before reporting completion.
```
