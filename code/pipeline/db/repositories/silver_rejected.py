"""Repository for the silver_rejected store."""

from __future__ import annotations
from pipeline.db.connection import transaction


class SilverRejectedRepository:
    """Tracks documents rejected by the classifier for a given profile version."""

    def insert(self, doc_id: str, profile_version: str, reason: str) -> None:
        """Record a rejection. Silently ignores duplicates (same doc + version)."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO silver_rejected (doc_id, profile_version, reason)
                VALUES (%s, %s, %s)
                ON CONFLICT (doc_id, profile_version) DO NOTHING
                """,
                (doc_id, profile_version, reason),
            )
