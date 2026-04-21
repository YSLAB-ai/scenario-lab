# Ingestion Orchestration V1 Implementation Plan

Date: 2026-04-20

1. Add failing tests for:
   - ingest tasks on `IngestionPlan`
   - local file recommendation mapping
   - batch-ingest registration and tagging
   - CLI commands for recommendation and batch ingestion
2. Add typed workflow models for:
   - `IngestionTask`
   - `IngestionRecommendation`
   - `BatchIngestionResult`
3. Extend shared planning helpers with:
   - category score calculation
   - starter-source/source-role selection
   - ingest task generation
4. Implement `WorkflowService.recommend_ingestion_files`.
5. Implement `WorkflowService.batch_ingest_recommended_files`.
6. Add CLI commands for:
   - `recommend-ingestion-files`
   - `batch-ingest-recommended`
7. Run focused tests and the full suite.
8. Update README and status documentation.
