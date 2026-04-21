# Manifest Retrieval V1 Implementation Plan

Date: 2026-04-20

1. Add failing tests for:
   - manifest loading
   - manifest-driven semantic alias search
   - manifest-driven evidence category coverage
2. Add a typed domain manifest loader under `forecasting_harness.knowledge`.
3. Extend local semantic search so manifest alias groups can be injected at query time.
4. Extend evidence packet drafting so manifest evidence categories influence selection and reasons.
5. Update domain manifest JSON files with machine-usable alias groups and category terms.
6. Run focused tests and the full `packages/core` suite.
7. Update README and status documentation.
