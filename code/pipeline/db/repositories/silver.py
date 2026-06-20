"""Repository for the silver store."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Iterator

from pipeline.db.connection import transaction


@dataclass
class SilverRecord:
    doc_id: str
    chunk_index: int
    chunk_text: str
    profile_version: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None


class SilverRepository:
    """All read/write access to the silver store."""

    def insert(self, record: SilverRecord) -> int:
        """Insert a chunk and return the generated id."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO silver (doc_id, chunk_index, chunk_text, profile_version)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (record.doc_id, record.chunk_index, record.chunk_text, record.profile_version),
            )
            return cur.fetchone()[0]

    def get_unprocessed(self, doc_id: str | None = None) -> Iterator[tuple[SilverRecord, str]]:
        """Yield (SilverRecord, stream_tag) for chunks not yet in gold.

        If doc_id is given, only chunks for that document are returned (single-doc mode).
        """
        with transaction() as conn:
            cur = conn.cursor()
            doc_filter = "AND s.doc_id = %s" if doc_id else ""
            params = (doc_id,) if doc_id else ()
            cur.execute(
                f"""
                SELECT s.id, s.doc_id, s.chunk_index, s.chunk_text,
                       s.profile_version, s.created_at, b.stream_tag
                FROM silver s
                JOIN bronze b ON b.id = s.doc_id
                WHERE NOT EXISTS (
                    SELECT 1 FROM gold g
                    WHERE g.doc_id = s.doc_id AND g.chunk_index = s.chunk_index
                )
                AND NOT EXISTS (
                    SELECT 1 FROM gold_discarded gd
                    WHERE gd.doc_id = s.doc_id AND gd.chunk_index = s.chunk_index
                )
                {doc_filter}
                ORDER BY s.doc_id, s.chunk_index
                """,
                params,
            )
            for row in cur.fetchall():
                record = SilverRecord(
                    id=row[0], doc_id=row[1], chunk_index=row[2],
                    chunk_text=row[3], profile_version=row[4], created_at=row[5],
                )
                stream_tag = row[6]
                yield record, stream_tag

    def get_chunks_for_doc(self, doc_id: str) -> list[SilverRecord]:
        """Return all chunks for a document, ordered by chunk_index."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, doc_id, chunk_index, chunk_text, profile_version, created_at
                FROM silver WHERE doc_id = %s ORDER BY chunk_index
                """,
                (doc_id,),
            )
            return [
                SilverRecord(
                    id=row[0], doc_id=row[1], chunk_index=row[2],
                    chunk_text=row[3], profile_version=row[4], created_at=row[5],
                )
                for row in cur.fetchall()
            ]
