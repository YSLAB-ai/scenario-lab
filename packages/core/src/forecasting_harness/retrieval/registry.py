from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


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
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks
                USING fts5(source_id, title, published_at, source_type, tags, content)
                """
            )

    def register_document(
        self,
        *,
        source_id: str,
        title: str,
        source_type: str,
        published_at: str,
        tags: dict[str, str],
        content: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO chunks (source_id, title, published_at, source_type, tags, content)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    title,
                    published_at,
                    source_type,
                    json.dumps(tags, sort_keys=True),
                    content,
                ),
            )

    def search_chunks(self, text: str) -> list[dict[str, Any]]:
        if not text.strip():
            query = "SELECT source_id, title, published_at, source_type, tags, content FROM chunks"
            parameters: tuple[Any, ...] = ()
        else:
            query = (
                "SELECT source_id, title, published_at, source_type, tags, content "
                "FROM chunks WHERE chunks MATCH ?"
            )
            parameters = (text,)

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

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
