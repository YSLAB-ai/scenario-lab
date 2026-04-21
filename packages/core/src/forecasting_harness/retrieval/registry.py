from __future__ import annotations

import json
import sqlite3
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_published_at(published_at: str | None) -> str | None:
    if published_at is None:
        return None
    try:
        datetime.strptime(published_at, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"invalid published_at date: {published_at!r}") from exc
    return published_at


class CorpusRegistry:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    source_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    published_at TEXT,
                    tags TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    ingested_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks
                USING fts5(source_id, chunk_id, title, published_at, source_type, tags, location, content)
                """
            )

    def register_document(
        self,
        *,
        source_id: str,
        title: str,
        source_type: str,
        published_at: str | None,
        tags: dict[str, str],
        path: str | None = None,
        content: str | None = None,
        chunks: list[dict[str, str]] | None = None,
    ) -> None:
        normalized_published_at = parse_published_at(published_at)
        normalized_path = path or f"/virtual/{source_id}"
        if chunks is None:
            if content is None:
                raise ValueError("either content or chunks must be provided")
            normalized_chunks = [
                {
                    "chunk_id": "1",
                    "location": "document:1",
                    "content": content,
                }
            ]
        else:
            normalized_chunks = chunks

        with self._connect() as connection:
            connection.execute("DELETE FROM documents WHERE source_id = ?", (source_id,))
            connection.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
            connection.execute(
                """
                INSERT INTO documents (source_id, title, source_type, path, published_at, tags, chunk_count, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    title,
                    source_type,
                    normalized_path,
                    normalized_published_at,
                    json.dumps(tags, sort_keys=True),
                    len(normalized_chunks),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            connection.executemany(
                """
                INSERT INTO chunks (source_id, chunk_id, title, published_at, source_type, tags, location, content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        source_id,
                        chunk["chunk_id"],
                        title,
                        normalized_published_at,
                        source_type,
                        json.dumps(tags, sort_keys=True),
                        chunk["location"],
                        chunk["content"],
                    )
                    for chunk in normalized_chunks
                ],
            )

    def list_documents(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source_id, title, source_type, path, published_at, tags, chunk_count, ingested_at
                FROM documents
                ORDER BY source_id
                """
            ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            result = dict(row)
            tags = result.get("tags")
            if isinstance(tags, str) and tags:
                result["tags"] = json.loads(tags)
            else:
                result["tags"] = {}
            results.append(result)
        return results

    def search_chunks(self, text: str) -> list[dict[str, Any]]:
        if not text.strip():
            query = (
                "SELECT source_id, chunk_id, title, published_at, source_type, tags, location, content "
                "FROM chunks"
            )
            parameters: tuple[Any, ...] = ()
        elif not re.fullmatch(r"[A-Za-z0-9\s]+", text):
            return []
        else:
            tokens = re.findall(r"[A-Za-z0-9]+", text)
            if not tokens:
                return []
            safe_query = " AND ".join(tokens)
            query = (
                "SELECT source_id, chunk_id, title, published_at, source_type, tags, location, content "
                "FROM chunks WHERE chunks MATCH ?"
            )
            parameters = (safe_query,)

        try:
            with self._connect() as connection:
                rows = connection.execute(query, parameters).fetchall()
        except sqlite3.OperationalError as exc:
            message = str(exc).lower()
            if message.startswith("fts5: syntax error"):
                return []
            raise

        results: list[dict[str, Any]] = []
        for row in rows:
            result = dict(row)
            tags = result.get("tags")
            if isinstance(tags, str) and tags:
                result["tags"] = json.loads(tags)
            else:
                result["tags"] = {}
            results.append(result)
        return results
