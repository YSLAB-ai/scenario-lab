# Scenario Lab Natural-Language Workflow

## Actual runtime phases

These are the actual adapter-runtime phases exposed by the repo.

1. `intake`
   Next action: `save-intake-draft`
   Meaning: capture the event framing and core entities first.
2. `evidence`
   Next action: usually `draft-evidence-packet`
   Optional next action: `batch-ingest-recommended` if local candidate files are available and recommended
   Meaning: review guidance, retrieval planning, and evidence coverage, then build the evidence packet.
3. `approval`
   Next action: `approve-revision`
   Meaning: review warnings, assumptions, and evidence summary before freezing the revision.
4. `simulation`
   Next action: `simulate`
   Meaning: run deterministic Monte Carlo search on the approved revision.
5. `report`
   Next action: `begin-revision-update`
   Meaning: review top branches and decide whether to continue with a child revision.

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

Scenario Lab exposes a packaged adapter runtime through `forecast-harness run-adapter-action`.

The packaged adapter smokes in this repo reached the stage sequence `intake -> evidence -> approval -> simulation -> report`.
