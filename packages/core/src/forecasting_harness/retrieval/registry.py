from __future__ import annotations

import json
import sqlite3
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forecasting_harness.retrieval.semantic import (
    DEFAULT_EMBEDDING_BACKEND,
    DEFAULT_NEURAL_MODEL,
    current_embedding_version,
    embedding_backend_summary,
    cosine_similarity,
    deserialize_vector,
    encode_text,
    serialize_vector,
)


def parse_published_at(published_at: str | None) -> str | None:
    if published_at is None:
        return None
    try:
        datetime.strptime(published_at, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"invalid published_at date: {published_at!r}") from exc
    return published_at


class CorpusRegistry:
    def __init__(
        self,
        db_path: Path | str,
        *,
        embedding_backend: str | None = None,
        embedding_model: str | None = None,
    ):
        self.db_path = Path(db_path)
        self.embedding_backend = embedding_backend
        self.embedding_model = embedding_model
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chunk_vectors (
                    source_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    embedding_version TEXT NOT NULL,
                    vector_json TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    PRIMARY KEY (source_id, chunk_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

    def _metadata_value(self, key: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
        return None if row is None else str(row["value"])

    def _set_metadata_value(self, key: str, value: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO metadata (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def _resolved_embedding_backend(self, override_backend: str | None = None) -> str | None:
        if override_backend is not None:
            return override_backend
        if self.embedding_backend is not None:
            return self.embedding_backend
        return self._metadata_value("embedding_backend") or DEFAULT_EMBEDDING_BACKEND

    def _resolved_embedding_model(self, override_model: str | None = None) -> str | None:
        if override_model is not None:
            return override_model
        if self.embedding_model is not None:
            return self.embedding_model
        return self._metadata_value("embedding_model") or DEFAULT_NEURAL_MODEL

    def _encode_text(
        self,
        text: str,
        *,
        alias_groups: list[tuple[str, ...]] | None = None,
        embedding_backend: str | None = None,
        embedding_model: str | None = None,
    ) -> tuple[list[float], int]:
        return encode_text(
            text,
            alias_groups=alias_groups,
            requested_backend=self._resolved_embedding_backend(embedding_backend),
            model_name=self._resolved_embedding_model(embedding_model),
        )

    def current_embedding_version(
        self,
        *,
        embedding_backend: str | None = None,
        embedding_model: str | None = None,
    ) -> str:
        return current_embedding_version(
            requested_backend=self._resolved_embedding_backend(embedding_backend),
            model_name=self._resolved_embedding_model(embedding_model),
        )

    def semantic_backend_summary(
        self,
        *,
        embedding_backend: str | None = None,
        embedding_model: str | None = None,
    ) -> dict[str, str | bool | None]:
        return embedding_backend_summary(
            requested_backend=self._resolved_embedding_backend(embedding_backend),
            model_name=self._resolved_embedding_model(embedding_model),
        )

    def _disambiguated_source_id(self, source_id: str, path: str) -> str:
        suffix = hashlib.sha1(path.encode("utf-8")).hexdigest()[:8]
        return f"{source_id}-{suffix}"

    def resolve_source_id(self, source_id: str, path: str) -> str:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT path FROM documents WHERE source_id = ?",
                (source_id,),
            ).fetchone()
            if row is None or row["path"] == path:
                return source_id

            disambiguated = self._disambiguated_source_id(source_id, path)
            while True:
                collision = connection.execute(
                    "SELECT path FROM documents WHERE source_id = ?",
                    (disambiguated,),
                ).fetchone()
                if collision is None or collision["path"] == path:
                    return disambiguated
                disambiguated = self._disambiguated_source_id(disambiguated, path)

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
    ) -> str:
        normalized_published_at = parse_published_at(published_at)
        normalized_path = path or f"/virtual/{source_id}"
        resolved_source_id = self.resolve_source_id(source_id, normalized_path)
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
        embedding_version = self.current_embedding_version()

        with self._connect() as connection:
            connection.execute("DELETE FROM documents WHERE source_id = ?", (resolved_source_id,))
            connection.execute("DELETE FROM chunks WHERE source_id = ?", (resolved_source_id,))
            connection.execute("DELETE FROM chunk_vectors WHERE source_id = ?", (resolved_source_id,))
            connection.execute(
                """
                INSERT INTO documents (source_id, title, source_type, path, published_at, tags, chunk_count, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    resolved_source_id,
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
                        resolved_source_id,
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
            connection.executemany(
                """
                INSERT INTO chunk_vectors (source_id, chunk_id, embedding_version, vector_json, token_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        resolved_source_id,
                        chunk["chunk_id"],
                        embedding_version,
                        serialize_vector((encoded := self._encode_text(chunk["content"]))[0]),
                        encoded[1],
                    )
                    for chunk in normalized_chunks
                ],
            )
        return resolved_source_id

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

    def search_semantic_chunks(
        self,
        text: str,
        *,
        limit: int = 20,
        alias_groups: list[tuple[str, ...]] | None = None,
    ) -> list[dict[str, Any]]:
        current_version = self.current_embedding_version()
        query_vector, token_count = self._encode_text(text, alias_groups=alias_groups)
        if token_count == 0:
            return []

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    chunks.source_id,
                    chunks.chunk_id,
                    chunks.title,
                    chunks.published_at,
                    chunks.source_type,
                    chunks.tags,
                    chunks.location,
                    chunks.content,
                    chunk_vectors.vector_json,
                    chunk_vectors.embedding_version
                FROM chunks
                JOIN chunk_vectors
                  ON chunks.source_id = chunk_vectors.source_id
                 AND chunks.chunk_id = chunk_vectors.chunk_id
                """,
            ).fetchall()

        scored: list[dict[str, Any]] = []
        for row in rows:
            result = dict(row)
            if alias_groups or result.get("embedding_version") != current_version:
                row_vector = self._encode_text(str(result.get("content", "")), alias_groups=alias_groups)[0]
            else:
                row_vector = deserialize_vector(str(result.get("vector_json", "[]")))
            result.pop("vector_json", None)
            result.pop("embedding_version", None)
            similarity = cosine_similarity(query_vector, row_vector)
            if similarity <= 0.0:
                continue
            tags = result.get("tags")
            if isinstance(tags, str) and tags:
                result["tags"] = json.loads(tags)
            else:
                result["tags"] = {}
            result["semantic_score"] = similarity
            scored.append(result)

        scored.sort(key=lambda item: (-item["semantic_score"], item["source_id"], item["chunk_id"]))
        return scored[:limit]

    def rebuild_embeddings(
        self,
        *,
        embedding_backend: str | None = None,
        embedding_model: str | None = None,
    ) -> dict[str, Any]:
        requested_backend = self._resolved_embedding_backend(embedding_backend)
        requested_model = self._resolved_embedding_model(embedding_model)
        backend_summary = self.semantic_backend_summary(
            embedding_backend=requested_backend,
            embedding_model=requested_model,
        )
        embedding_version = self.current_embedding_version(
            embedding_backend=requested_backend,
            embedding_model=requested_model,
        )

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source_id, chunk_id, content
                FROM chunks
                ORDER BY source_id, chunk_id
                """
            ).fetchall()

            connection.execute(
                """
                INSERT INTO metadata (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                ("embedding_backend", requested_backend),
            )
            connection.execute(
                """
                INSERT INTO metadata (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                ("embedding_model", requested_model),
            )

            updates = []
            for row in rows:
                encoded = self._encode_text(
                    str(row["content"]),
                    embedding_backend=requested_backend,
                    embedding_model=requested_model,
                )
                updates.append(
                    (
                        str(row["source_id"]),
                        str(row["chunk_id"]),
                        embedding_version,
                        serialize_vector(encoded[0]),
                        encoded[1],
                    )
                )

            connection.executemany(
                """
                INSERT INTO chunk_vectors (source_id, chunk_id, embedding_version, vector_json, token_count)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source_id, chunk_id) DO UPDATE SET
                    embedding_version = excluded.embedding_version,
                    vector_json = excluded.vector_json,
                    token_count = excluded.token_count
                """,
                updates,
            )

            document_count = int(
                connection.execute("SELECT COUNT(*) AS count FROM documents").fetchone()["count"]
            )

        return {
            **backend_summary,
            "document_count": document_count,
            "chunk_count": len(rows),
            "updated_chunks": len(rows),
        }
