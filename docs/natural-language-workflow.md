# Scenario Lab Natural-Language Workflow

## Actual runtime phases

These are the actual adapter-runtime phases exposed by the repo.

1. `intake`
   Next action: `save-intake-draft`
   Meaning: understand the problem, define the main actors, and set the time horizon.
2. `evidence`
   Next action: usually `draft-evidence-packet`
   Optional next action: `batch-ingest-recommended` if local candidate files are available and recommended
   Meaning: review what evidence is missing, what sources to pull in, and then build the evidence packet.
3. `approval`
   Next action: `approve-revision`
   Meaning: review warnings and assumptions, then lock the setup before search.
4. `simulation`
   Next action: `simulate`
   Meaning: explore many possible paths with deterministic Monte Carlo search.
5. `report`
   Next action: `begin-revision-update`
   Meaning: review the main outcomes and decide whether to continue with an updated revision.

## Verified U.S.-Iran walkthrough

This phase sequence was rechecked on a verified `U.S.-Iran` run in [docs/demo-us-iran.md](docs/demo-us-iran.md).

- broad question:
  - `How would a U.S.-Iran conflict at the Strait of Hormuz develop for the next 30 days?`
- short user correction:
  - `Consider China. Go ahead.`
- verified phase flow:
  - `intake -> evidence -> approval -> simulation -> report`
- verified evidence plan categories:
  - `force posture`
  - `diplomatic signaling`
  - `alliance commitments`
  - `leader behavior`
  - `economic constraints`
- verified simulation facts:
  - `iterations = 10000`
  - `node_count = 129`
  - top branch `Open negotiation`

## Runtime actions

Scenario Lab exposes a packaged adapter runtime through `scenario-lab run-adapter-action`.

The packaged adapter smokes in this repo reached the stage sequence `intake -> evidence -> approval -> simulation -> report`.

## Scenario Bootstrap

Use the repo-owned bootstrap when you want a literal scenario prompt to produce the normal next workflow turn without immediately running the full simulation:

```bash
scenario-lab scenario --root .forecast --run-id us-iran-1 --domain-pack interstate-crisis "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days"
```

When the input validates, it saves the intake draft and returns the next workflow turn. When validation fails, it returns an intake-stage turn with guidance and validation errors instead of saving an invalid draft.
