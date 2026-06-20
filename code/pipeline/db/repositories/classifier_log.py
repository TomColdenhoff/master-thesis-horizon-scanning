"""Repository for the classifier log — one row per classified document."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pipeline.db.connection import transaction


@dataclass
class ClassifierLogRecord:
    doc_id: str
    relevant: bool
    reason: str
    input_tokens: int
    output_tokens: int
    profile_version: str
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    duration_ms: Optional[int] = None


class ClassifierLogRepository:
    """All read/write access to the classifier_log table."""

    def insert(self, record: ClassifierLogRecord) -> None:
        """Insert a classifier log entry. Skips if doc_id already exists."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO classifier_log
                    (doc_id, relevant, reason, input_tokens, output_tokens, profile_version, duration_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (doc_id) DO NOTHING
                """,
                (
                    record.doc_id, record.relevant, record.reason,
                    record.input_tokens, record.output_tokens, record.profile_version,
                    record.duration_ms,
                ),
            )
