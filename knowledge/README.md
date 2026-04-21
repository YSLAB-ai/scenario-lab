# Knowledge Manifests

This directory is the repo-owned blueprint for the local knowledge system.

Each file under `knowledge/domains/` describes:

- what a domain cares about
- which evidence categories matter
- which state fields tend to drive the forecast
- which source types should be ingested into the local corpus
- which sources should be prioritized first

These files are intentionally lightweight. They are not the corpus itself.

Use them to guide ingestion of:

- user-provided documents
- licensed materials
- public-domain materials
- structured datasets with clear reuse terms

Do not treat these manifests as permission to copy copyrighted books or papers into the repository.
