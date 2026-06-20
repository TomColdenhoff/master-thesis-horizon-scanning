"""Repository for chunks discarded by the gold completeness filter."""

from __future__ import annotations
from pipeline.db.connection import transaction


class GoldDiscardedRepository:
    """Tracks silver chunks that failed the completeness threshold in gold."""

    def insert(self, doc_id: str, chunk_index: int, score: int) -> None:
        """Record a discarded chunk. Silently ignores duplicates."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO gold_discarded (doc_id, chunk_index, score)
                VALUES (%s, %s, %s)
                ON CONFLICT (doc_id, chunk_index) DO NOTHING
                """,
                (doc_id, chunk_index, score),
            )
