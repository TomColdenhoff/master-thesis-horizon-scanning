"""Repository for the bronze store."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from pipeline.db.connection import transaction


@dataclass
class BronzeRecord:
    id: str
    soort: str
    datum: Optional[date]
    onderwerp: Optional[str]
    vergaderjaar: Optional[str]
    content_type: Optional[str]
    stream_tag: str
    raw_text: Optional[str] = None
    raw_file_path: Optional[str] = None
    ingested_at: Optional[datetime] = None


class BronzeRepository:
    """All read/write access to the bronze store."""

    def exists(self, doc_id: str) -> bool:
        """Return True if a document with this id is already in the store."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM bronze WHERE id = %s", (doc_id,))
            return cur.fetchone() is not None

    def insert(self, record: BronzeRecord) -> None:
        """Insert a new bronze record. Raises if id already exists."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO bronze
                    (id, soort, datum, onderwerp, vergaderjaar,
                     content_type, stream_tag, raw_text, raw_file_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record.id, record.soort, record.datum, record.onderwerp,
                    record.vergaderjaar, record.content_type, record.stream_tag,
                    record.raw_text, record.raw_file_path,
                ),
            )

    def get_watermark(self) -> str:
        """Return the latest document Datum as an ISO string.

        Returns START_DATE from config if the bronze store is empty.
        Uses MAX(datum) — the date of the most recent document — not
        ingested_at, which would be today and filter out all real documents.
        """
        import config
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT MAX(datum) FROM bronze")
            result = cur.fetchone()[0]
            return str(result) if result else config.START_DATE

    def update_file(self, doc_id: str, raw_file_path: str, content_type: str) -> None:
        """Update the raw file path and content type after download."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE bronze SET raw_file_path = %s, content_type = %s WHERE id = %s",
                (raw_file_path, content_type, doc_id),
            )

    def update_raw_text(self, doc_id: str, raw_text: str) -> None:
        """Store extracted plain text after successful text extraction."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE bronze SET raw_text = %s WHERE id = %s",
                (raw_text, doc_id),
            )

    def get_missing_raw_text(self) -> list[BronzeRecord]:
        """Return records that have a file but no raw_text yet (for backfill)."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, soort, datum, onderwerp, vergaderjaar,
                       content_type, stream_tag, raw_text, raw_file_path, ingested_at
                FROM bronze
                WHERE raw_file_path IS NOT NULL
                  AND content_type IS NOT NULL
                  AND raw_text IS NULL
                ORDER BY datum
                """
            )
            return [
                BronzeRecord(
                    id=row[0], soort=row[1], datum=row[2], onderwerp=row[3],
                    vergaderjaar=row[4], content_type=row[5], stream_tag=row[6],
                    raw_text=row[7], raw_file_path=row[8], ingested_at=row[9],
                )
                for row in cur.fetchall()
            ]

    def count(self) -> int:
        """Return total number of documents in bronze."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM bronze")
            return cur.fetchone()[0]

    def get_all_ids(self) -> list[str]:
        """Return all doc_ids in bronze that have raw_text, ordered by datum."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM bronze WHERE raw_text IS NOT NULL ORDER BY datum"
            )
            return [row[0] for row in cur.fetchall()]

    def get_unprocessed(self, profile_version: str, doc_id: str | None = None) -> list[BronzeRecord]:
        """Return bronze records not yet classified under the given profile version.

        If doc_id is given, only that document is returned (single-doc mode).
        """
        with transaction() as conn:
            cur = conn.cursor()
            doc_filter = "AND b.id = %s" if doc_id else ""
            params = (profile_version, profile_version, doc_id) if doc_id else (profile_version, profile_version)
            cur.execute(
                f"""
                SELECT b.id, b.soort, b.datum, b.onderwerp, b.vergaderjaar,
                       b.content_type, b.stream_tag, b.raw_text, b.raw_file_path, b.ingested_at
                FROM bronze b
                WHERE b.raw_text IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM silver s
                      WHERE s.doc_id = b.id
                        AND s.profile_version = %s
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM silver_rejected r
                      WHERE r.doc_id = b.id
                        AND r.profile_version = %s
                  )
                  {doc_filter}
                ORDER BY b.datum
                """,
                params,
            )
            return [
                BronzeRecord(
                    id=row[0], soort=row[1], datum=row[2], onderwerp=row[3],
                    vergaderjaar=row[4], content_type=row[5], stream_tag=row[6],
                    raw_text=row[7], raw_file_path=row[8], ingested_at=row[9],
                )
                for row in cur.fetchall()
            ]
