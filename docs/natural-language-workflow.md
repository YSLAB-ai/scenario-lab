# Scenario Lab Natural-Language Workflow

## 5-minute conversational path

These prompts map to the verified `U.S.-Iran` public demo in [docs/demo-us-iran.md](docs/demo-us-iran.md).

1. `Start a U.S.-Iran scenario run for the next 30 days.`
   What to expect: the run enters `intake`.
2. `Save the intake draft with U.S. and Iran as the focus actors.`
   What to expect: the run moves to `evidence`.
3. `Draft the evidence packet.`
   What to expect: Scenario Lab drafts evidence if it finds it. In the verified public demo, this returned an empty packet and moved the run to `approval` with warnings instead of inventing evidence.
4. `Approve the revision and simulate it.`
   What to expect: the run becomes ready for `simulation`, then produces ranked branches.
5. `Generate the report.`
   What to expect: the verified public demo wrote `/tmp/scenario-lab-us-iran/run/runs/us-iran-public/reports/r1.report.md`.

## Example prompts

- `Start a U.S.-Iran scenario run for the next 30 days.`
- `Save the intake draft with U.S. and Iran as the focus actors.`
- `Draft the evidence packet.`
- `Approve the revision and simulate it.`
- `Generate the report.`

## Runtime actions

Scenario Lab exposes a packaged adapter runtime through `forecast-harness run-adapter-action`.

The packaged adapter smokes in this repo reached the stage sequence `intake -> evidence -> approval -> simulation -> report`.
