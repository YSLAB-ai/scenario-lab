# Corpus Ingestion V1 Design

Date: 2026-04-20

## Summary

This milestone adds the missing local corpus ingestion pipeline to the forecasting harness.

Verified current baseline on `codex/generalized-harness-v2`:

- the core can already retrieve from a local SQLite/FTS corpus
- the workflow can already draft evidence packets from that corpus
- there is still no end-user way to ingest curated `PDF`, `Markdown`, `CSV`, and `JSON` sources into the corpus

The goal of this milestone is to make the corpus usable from the CLI without expanding into open-web retrieval, rule extraction, or domain-specific modeling work.

## Goal

Deliver a generic local ingestion milestone that:

1. ingests curated files into the local corpus database
2. preserves source metadata and citation-friendly chunk locations
3. supports `Markdown`, `CSV`, `JSON`, and `PDF`
4. exposes simple CLI commands for ingesting files and listing stored sources
5. keeps retrieval and evidence drafting compatible with the new corpus structure

## Non-Goals

This milestone does not attempt to deliver:

- OCR for scanned PDFs
- semantic chunking or embedding search
- ingestion of spreadsheets, EPUB, web pages, or images
- automatic metadata extraction from external services
- automatic rule extraction or corpus-to-rule compilation
- adapter-side deep research UX

## Chosen Approach

This milestone uses a `file-first deterministic ingestion pipeline`.

That means:

- each file is parsed locally according to its file type
- ingestion produces explicit document metadata plus deterministic text chunks
- each chunk stores a stable location reference
- retrieval remains SQLite/FTS based

This is preferred over:

- adding a broad document-processing framework first
- trying to infer complex semantics during ingestion
- waiting for the future knowledge compiler

The harness needs a dependable curated corpus before it needs more sophistication.

## Product Boundary

After this milestone, the corpus layer should support this end-to-end flow:

1. user adds curated files locally
2. CLI ingests those files into a corpus database
3. retrieval searches the stored chunks
4. workflow evidence drafting selects from those chunks

The ingestion layer is still deterministic core behavior. The conversational adapter remains future work.

## Storage Model

The current `CorpusRegistry` only stores one FTS row per source. That is not sufficient for reusable evidence retrieval because it loses:

- document-level metadata as a first-class entity
- chunk-level identities
- stable citation locations

### Required structure

The corpus database should store:

- `documents` table
- `chunks` FTS table

### `documents` table

Each document record should include:

- `source_id`
- `title`
- `source_type`
- `path`
- `published_at`
- `tags`
- `chunk_count`
- `ingested_at`

`published_at` should become optional metadata. If it is absent, retrieval should not invent a fake publication date.

### `chunks` FTS table

Each chunk row should include:

- `source_id`
- `chunk_id`
- `title`
- `published_at`
- `source_type`
- `tags`
- `location`
- `content`

`location` is the citation-friendly locator, such as:

- Markdown heading path
- CSV row number
- JSON item path
- PDF page number

## Source Types

`v1` should support four source types.

### Markdown

Supported inputs:

- `.md`
- `.txt`

Chunking should be deterministic and citation-preserving:

- split by Markdown headings when present
- otherwise split by non-empty paragraph groups
- record a heading-based or paragraph-based location

### CSV

Chunking should be row-based:

- one chunk per data row
- content serialized as header-value pairs
- location recorded as `row:<n>`

This is the simplest citation model that keeps table rows auditable.

### JSON

Chunking should be structural:

- top-level list entries become one chunk each
- top-level object keys become one chunk each
- nested values can be JSON-serialized inside the chunk text
- location recorded as a JSON path such as `items[3]` or `key:constraints`

This avoids pretending JSON is plain prose while still producing searchable text.

### PDF

Chunking should be page-based:

- extract text page by page
- one chunk per non-empty page
- location recorded as `page:<n>`

`v1` only supports text-extractable PDFs. If a PDF yields no text, ingestion should fail clearly instead of silently storing empty content.

## Parser Surface

The ingestion layer should remain small and explicit.

### Required parser responsibilities

Each parser should return:

- normalized document metadata
- deterministic chunk list

Each chunk should contain:

- `chunk_id`
- `location`
- `content`

### Type detection

Type detection should be file-extension based in `v1`.

Supported mapping:

- `.md`, `.txt` -> `markdown`
- `.csv` -> `csv`
- `.json` -> `json`
- `.pdf` -> `pdf`

Unsupported suffixes should raise a deterministic error.

## Metadata Rules

The ingestion command should allow:

- optional explicit `source_id`
- optional explicit `title`
- optional explicit `published_at`
- repeated `tag` inputs as `key=value`

Default behavior:

- `source_id` defaults to a sanitized file stem
- `title` defaults to the file stem
- `published_at` defaults to `null`
- tags default to `{}` if omitted

If the caller reuses an existing `source_id`, ingestion should replace that source’s stored document and chunk rows, matching the current registry replacement behavior.

## Retrieval Compatibility

The existing `SearchEngine` and workflow evidence drafting should continue to work after ingestion changes.

### Required compatibility changes

Search results should now return:

- `source_id`
- `chunk_id`
- `title`
- `published_at`
- `source_type`
- `tags`
- `location`
- `content`

### Freshness behavior

Because `published_at` is now optional:

- rows with a valid date should keep current freshness behavior
- rows without `published_at` should receive a neutral freshness multiplier of `1.0`

This avoids inventing false temporal precision.

## CLI Surface

`v1` should add these commands:

- `forecast-harness ingest-file`
- `forecast-harness ingest-directory`
- `forecast-harness list-corpus-sources`

### `ingest-file`

This command should:

- detect type from extension
- parse the file
- register the document and its chunks
- print a JSON summary

### `ingest-directory`

This command should:

- walk a directory
- ingest supported files
- skip unsupported files with explicit counts in the final summary
- print a JSON summary of ingested and skipped files

`v1` does not need recursive filtering beyond supported suffix detection.

### `list-corpus-sources`

This command should list stored document records in deterministic order so users and adapters can inspect what is available in the corpus.

## Error Handling

The ingestion flow should fail loudly and specifically for:

- unsupported file types
- malformed CSV or JSON that cannot be parsed
- PDFs with no extractable text
- invalid `published_at` values
- malformed `tag` inputs that are not `key=value`

Directory ingestion should be more forgiving:

- one bad file should not abort the whole directory run
- the summary should report ingested vs skipped vs failed counts

## Testing

This milestone should add tests for:

- document and chunk persistence in the new registry schema
- markdown chunking with heading-based locations
- CSV row-based chunking and row citations
- JSON path-based chunking
- PDF page-based chunking
- optional `published_at` handling in search freshness
- CLI ingestion of a file into a searchable corpus
- directory ingestion summary behavior

The existing retrieval and workflow evidence-drafting tests should remain green after the schema change.

## Out of Scope but Preserved

This milestone should leave room for:

- richer chunking policies
- semantic/embedding search
- spreadsheet ingestion
- OCR-backed PDF ingestion
- remote or adapter-driven corpus management
- ingestion metadata approval or provenance review

The purpose of `v1` is to make the curated corpus real and usable, not to make it clever.
