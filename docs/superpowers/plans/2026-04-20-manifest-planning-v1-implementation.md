# Manifest Planning V1 Implementation Plan

Date: 2026-04-20

1. Add failing tests for:
   - retrieval plan generation
   - ingestion plan generation
   - evidence drafting without explicit query text
   - CLI commands for the new planning surfaces
2. Add typed workflow models for `RetrievalPlan` and `IngestionPlan`.
3. Add shared deterministic planning helpers for:
   - query variant generation
   - evidence-category classification
4. Implement `WorkflowService.draft_retrieval_plan`.
5. Implement `WorkflowService.draft_ingestion_plan`.
6. Update `draft_evidence_packet` to search query variants and merge results.
7. Add CLI commands for the new planning surfaces.
8. Run focused tests, the full suite, and a direct smoke check.
9. Update README and status documentation.
