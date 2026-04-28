---
allowed-tools: Bash(test:*), Bash(scenario-lab:*), Bash(packages/core/.venv/bin/scenario-lab:*)
description: Start a Scenario Lab run from a natural-language scenario question
---

Start a Scenario Lab run for this user request: `$ARGUMENTS`

## Workflow

This is an interactive, stage-by-stage workflow. **Stop at the end of every stage and wait for the user to confirm, correct, or redirect before proceeding to the next stage.** Never chain stages together without explicit user approval of the current stage's output.

---

### Stage 1 — Bootstrap (always run first)

1. Use `packages/core/.venv/bin/scenario-lab` if it exists in the current repository. Otherwise use `scenario-lab` from `PATH`.
2. Run the CLI bootstrap:
   - `packages/core/.venv/bin/scenario-lab scenario --root .forecast "/scenario $ARGUMENTS"`
3. Read the JSON output and present to the user:
   - Run ID
   - Inferred domain pack — ask the user if this is correct
   - Inferred actors (focus entities) — ask the user if any are missing or wrong
   - Current workflow stage and next recommended action
   - Follow-up questions from the intake guidance
4. **STOP. Ask the user:**
   - Are the actors correct? Who should be added or removed?
   - Is the domain pack right?
   - Any known constraints or unknowns to add before collecting evidence?

---

### Stage 2 — Evidence Collection (only when user approves Stage 1)

Only proceed after the user explicitly confirms the actors and domain pack from Stage 1.

1. Build or update evidence documents based on what the user confirmed — use `.forecast/evidence-candidates/` as the staging directory.
2. Ingest into `.forecast/corpus.db` (or a run-specific corpus).
3. Run `scenario-lab draft-evidence-packet` and present each evidence passage to the user:
   - Source and passage text
   - Which evidence category it was assigned to
   - Whether it seems relevant or should be dropped
4. **STOP. Ask the user:**
   - Do these passages look right?
   - Is anything missing that should be in the evidence?
   - Any passages to remove or replace?

---

### Stage 3 — Approval (only when user approves Stage 2 evidence)

Only proceed after the user confirms the evidence packet from Stage 2.

1. Run `scenario-lab draft-approval-packet` and surface:
   - Assumption summary
   - Suggested actors
   - Any warnings
2. Ask the user to confirm or edit each assumption before locking.
3. Run `scenario-lab approve-revision` with the confirmed assumptions and actors.
4. **STOP. Ask the user:**
   - Are these assumptions correct?
   - Anything to add before running the simulation?

---

### Stage 4 — Simulation and Report (only when user approves Stage 3)

Only proceed after the user explicitly says to run the simulation.

1. Run `scenario-lab simulate` with appropriate iteration count.
2. Run `scenario-lab generate-report`.
3. Present results:
   - Top branches with scores and confidence
   - Scenario families and paths
   - Plain-English interpretation of each branch
   - Key drivers and what to watch for
4. **STOP.** Offer next steps:
   - Run a second revision with different assumptions
   - Drill into a specific branch
   - Adjust actors and re-simulate

---

## Key Rules

- **Never skip a stop point.** A user saying "yes" or "A" or "continue" at one stage is permission for that stage only — not for all remaining stages.
- **Always surface what the engine inferred** (actors, domain pack, evidence passages, assumptions) before accepting it — the user may know something the engine doesn't.
- **Flag gaps explicitly.** If the engine couldn't extract actors, or evidence passages seem weak, say so and ask the user to fill in rather than filling in silently yourself.
- **One stage at a time.** Even if the user seems eager to proceed, confirm stage output before moving forward.
