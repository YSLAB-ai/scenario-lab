from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from forecasting_harness.retrieval.registry import parse_published_at


@dataclass(frozen=True)
class IngestedChunk:
    chunk_id: str
    location: str
    content: str


@dataclass(frozen=True)
class IngestedDocument:
    source_id: str
    title: str
    source_type: str
    path: str
    published_at: str | None
    tags: dict[str, str]
    chunks: list[IngestedChunk]


def _sanitize_source_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "source"


def detect_source_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return "markdown"
    if suffix == ".csv":
        return "csv"
    if suffix == ".json":
        return "json"
    if suffix == ".pdf":
        return "pdf"
    raise ValueError(f"unsupported source type: {suffix or path.name}")


def _markdown_chunks(text: str) -> list[IngestedChunk]:
    heading_stack: list[str] = []
    buffer: list[str] = []
    chunks: list[IngestedChunk] = []
    paragraph_index = 0

    def flush() -> None:
        nonlocal paragraph_index
        content = "\n".join(line.rstrip() for line in buffer).strip()
        buffer.clear()
        if not content:
            return
        if heading_stack:
            location = "heading:" + " > ".join(heading_stack)
        else:
            paragraph_index += 1
            location = f"paragraph:{paragraph_index}"
        chunks.append(
            IngestedChunk(
                chunk_id=str(len(chunks) + 1),
                location=location,
                content=content,
            )
        )

    for raw_line in text.splitlines():
        heading_match = re.match(r"^(#{1,6})\s+(.*\S)\s*$", raw_line)
        if heading_match:
            flush()
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            heading_stack[:] = heading_stack[: level - 1]
            heading_stack.append(heading_text)
            continue
        if raw_line.strip() or buffer:
            buffer.append(raw_line)

    flush()
    return chunks


def _csv_chunks(path: Path) -> list[IngestedChunk]:
    chunks: list[IngestedChunk] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row_index, row in enumerate(reader, start=1):
            parts = [f"{key}={value}" for key, value in row.items() if key is not None]
            chunks.append(
                IngestedChunk(
                    chunk_id=str(row_index),
                    location=f"row:{row_index}",
                    content=", ".join(parts),
                )
            )
    return chunks


def _json_chunks(path: Path) -> list[IngestedChunk]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    chunks: list[IngestedChunk] = []
    if isinstance(payload, list):
        for index, item in enumerate(payload):
            chunks.append(
                IngestedChunk(
                    chunk_id=str(index + 1),
                    location=f"items[{index}]",
                    content=json.dumps(item, sort_keys=True),
                )
            )
        return chunks
    if isinstance(payload, dict):
        for index, key in enumerate(sorted(payload), start=1):
            chunks.append(
                IngestedChunk(
                    chunk_id=str(index),
                    location=f"key:{key}",
                    content=json.dumps(payload[key], sort_keys=True),
                )
            )
        return chunks
    return [
        IngestedChunk(
            chunk_id="1",
            location="root",
            content=json.dumps(payload, sort_keys=True),
        )
    ]


def _pdf_chunks(path: Path) -> list[IngestedChunk]:
    chunks: list[IngestedChunk] = []
    reader = PdfReader(str(path))
    for page_index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        chunks.append(
            IngestedChunk(
                chunk_id=str(page_index),
                location=f"page:{page_index}",
                content=text,
            )
        )
    if not chunks:
        raise ValueError(f"pdf has no extractable text: {path}")
    return chunks


def _chunks_for_path(path: Path, source_type: str) -> list[IngestedChunk]:
    if source_type == "markdown":
        return _markdown_chunks(path.read_text(encoding="utf-8"))
    if source_type == "csv":
        return _csv_chunks(path)
    if source_type == "json":
        return _json_chunks(path)
    if source_type == "pdf":
        return _pdf_chunks(path)
    raise ValueError(f"unsupported source type: {source_type}")


def ingest_file(
    path: Path,
    *,
    source_id: str | None = None,
    title: str | None = None,
    published_at: str | None = None,
    tags: dict[str, str] | None = None,
) -> IngestedDocument:
    source_path = path.resolve()
    source_type = detect_source_type(source_path)
    normalized_published_at = parse_published_at(published_at) if published_at is not None else None
    normalized_tags = dict(tags or {})
    chunks = _chunks_for_path(source_path, source_type)
    return IngestedDocument(
        source_id=source_id or _sanitize_source_id(source_path.stem),
        title=title or source_path.stem,
        source_type=source_type,
        path=str(source_path),
        published_at=normalized_published_at,
        tags=normalized_tags,
        chunks=chunks,
    )
